//! Dashboard UI Engine for 480×320 TFT Display.
//! Implements Nothing × Teenage Engineering design language:
//! - Pure zero-allocation static memory budget.
//! - Circular NDot 5×7 dot-matrix typography.
//! - Smooth differential bar updates and zero ghosting.
//! - Multi-face support (CPU Grid, GPU Grid, Dual Load, Memory, Thermal, Minimal).

use crate::display::Color;
use crate::font::draw_ascii;
use crate::ndot::{draw_dot_circle_7px, draw_ndot_char, draw_ndot_str};
use crate::traits::{DelayMs, Display};
use gadget_common::{ConfigurationPacket, TelemetryPacket};

// ── Screen Geometry (480 × 320) ───────────────────────────────────────────────
const WIDTH: u16 = 480;
const HEIGHT: u16 = 320;
const DIV_X: u16 = 240;

// Dual panel inner bounds
const CPU_IX: u16 = 16;
const CPU_IW: u16 = 208;
const GPU_IX: u16 = 256;
const GPU_IW: u16 = 208;

// Common Grid Geometry
const PAD_X: u16 = 24;
const HEAD_Y: u16 = 20;
const RULE1_Y: u16 = 46;
const VAL_Y: u16 = 56;     // cell = 11 -> 77px tall numerals (56..133)
const BAR_Y: u16 = 158;    // 7px dots (158..165)
const RULE2_Y: u16 = 194;  // hairline rule
const BOT_LBL_Y: u16 = 208;// sub-header / labels
const BOT_VAL_Y: u16 = 232;// cell = 7 -> 49px tall numerals (232..281)

const BAR_DOTS: usize = 24;  // 24 dots for split dual panel
const S_BAR_DOTS: usize = 28;// 28 dots for full-width single face
const MEM_DOTS: usize = 20;  // 20 dots for memory rows

// ── Dashboard State ───────────────────────────────────────────────────────────
pub struct Dashboard {
    pub config: ConfigurationPacket,
    last: Option<TelemetryPacket>,
    initialized: bool,
    prev_val1: u8,
    prev_val2: u8,
    prev_temp1: u8,
    prev_temp2: u8,
    curr_dots1: u8,
    curr_dots2: u8,
}

impl Dashboard {
    pub fn new() -> Self {
        Self {
            config: ConfigurationPacket::default(),
            last: None,
            initialized: false,
            prev_val1: 255,
            prev_val2: 255,
            prev_temp1: 255,
            prev_temp2: 255,
            curr_dots1: 0,
            curr_dots2: 0,
        }
    }

    /// Color palette resolution based on accent selection and invert flag.
    pub fn get_palette(&self) -> (Color, Color, Color, Color, Color) {
        let accent = match self.config.accent_color_id {
            1 => Color::new(215, 25, 33),   // Red #D71921
            2 => Color::new(255, 90, 0),    // Orange #FF5A00
            3 => Color::new(46, 230, 197),  // Cyan #2EE6C5
            4 => Color::new(139, 140, 249), // Purple #8B8CF9
            5 => Color::new(255, 194, 71),  // Gold #FFC247
            _ => Color::new(255, 255, 255), // White
        };

        if self.config.invert() {
            let fg = if self.config.accent_color_id == 0 { Color::BLACK } else { accent };
            (
                Color::WHITE,                  // bg
                fg,                            // fg / accent
                Color::new(140, 140, 140),     // dim
                Color::new(225, 225, 225),     // line
                Color::new(220, 220, 220),     // dot off
            )
        } else {
            (
                Color::BLACK,                  // bg
                accent,                        // fg / accent
                Color::new(107, 107, 107),     // dim
                Color::new(38, 38, 38),        // line
                Color::new(28, 28, 28),        // dot off
            )
        }
    }

    /// Dynamically switches configuration and invalidates previous render caches.
    pub fn apply_config<D: Display>(&mut self, display: &mut D, config: ConfigurationPacket) {
        if self.config != config || !self.initialized {
            self.config = config;
            self.prev_val1 = 255;
            self.prev_val2 = 255;
            self.prev_temp1 = 255;
            self.prev_temp2 = 255;
            self.curr_dots1 = 0;
            self.curr_dots2 = 0;
            self.draw_layout(display);
        }
    }

    /// Draws the static shell for the currently active face.
    pub fn draw_layout<D: Display>(&mut self, display: &mut D) {
        let (bg, fg, dim, line, dot_off) = self.get_palette();

        // 1. Clear full canvas
        display.fill_rect(0, 0, WIDTH, HEIGHT, bg);

        match self.config.face_id {
            0 => self.draw_single_shell(display, b"CPU", b"4.2 GHZ", b"ACTIVE", bg, fg, dim, line, dot_off),
            1 => self.draw_single_shell(display, b"GPU", b"185 W", b"PCIE", bg, fg, dim, line, dot_off),
            2 => self.draw_dual_shell(display, bg, fg, dim, line, dot_off),
            3 => self.draw_memory_shell(display, bg, fg, dim, line, dot_off),
            4 => self.draw_thermal_shell(display, bg, fg, dim, line, dot_off),
            5 => self.draw_minimal_shell(display, bg, dim, line, dot_off),
            _ => self.draw_dual_shell(display, bg, fg, dim, line, dot_off),
        }

        self.initialized = true;
    }

    /// Differential update: redraws dynamic metrics and animates progress bars.
    pub fn update<D: Display, DELAY: DelayMs>(
        &mut self,
        display: &mut D,
        delay: &mut DELAY,
        packet: TelemetryPacket,
    ) {
        if !self.initialized {
            self.draw_layout(display);
        }

        match self.config.face_id {
            0 => self.update_single(display, delay, packet.cpu_percent, packet.cpu_temp_c),
            1 => self.update_single(display, delay, packet.gpu_percent, packet.gpu_temp_c),
            2 => self.update_dual(display, delay, packet),
            3 => self.update_memory(display, packet.ram_percent, packet.cpu_temp_c),
            4 => self.update_thermal(display, delay, packet.cpu_temp_c, packet.gpu_temp_c),
            5 => self.update_minimal(display, delay, packet.cpu_percent),
            _ => self.update_dual(display, delay, packet),
        }

        self.last = Some(packet);
    }

    // ── SHELL DRAWERS ─────────────────────────────────────────────────────────

    fn draw_single_shell<D: Display>(
        &self,
        display: &mut D,
        lbl: &[u8],
        meta: &[u8],
        status: &[u8],
        bg: Color,
        fg: Color,
        dim: Color,
        line: Color,
        dot_off: Color,
    ) {
        if self.config.show_label() {
            draw_ndot_str(display, PAD_X, HEAD_Y, lbl, 3, fg, bg);
            draw_ascii(display, WIDTH - PAD_X - (meta.len() as u16 * 6), HEAD_Y + 7, meta, dim, bg, 1);
        }

        display.draw_hline(PAD_X, RULE1_Y, WIDTH - (2 * PAD_X), line);
        display.draw_hline(PAD_X, RULE2_Y, WIDTH - (2 * PAD_X), line);

        // Initial unlit 28-dot bar
        let bar_w = WIDTH - (2 * PAD_X) - 7;
        for i in 0..S_BAR_DOTS {
            let cx = PAD_X + ((i as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, BAR_Y, dot_off);
        }

        if self.config.show_temp() {
            draw_ascii(display, PAD_X, BOT_LBL_Y, b"T  E  M  P", dim, bg, 1);
        }

        let st_x = WIDTH - PAD_X - 60;
        draw_ascii(display, st_x, BOT_LBL_Y, b"S T A T U S", dim, bg, 1);
        draw_ndot_str(display, st_x, BOT_VAL_Y + 4, status, 2, dim, bg);
    }

    fn draw_dual_shell<D: Display>(
        &self,
        display: &mut D,
        bg: Color,
        fg: Color,
        dim: Color,
        line: Color,
        dot_off: Color,
    ) {
        // Vertical divider
        display.draw_vline(DIV_X, 0, HEIGHT, line);

        // CPU Panel Header
        if self.config.show_label() {
            draw_ndot_str(display, CPU_IX, HEAD_Y, b"CPU", 3, fg, bg);
            draw_ascii(display, CPU_IX + CPU_IW - 44, HEAD_Y + 7, b"4.2 GHZ", dim, bg, 1);
        }

        display.draw_hline(CPU_IX, RULE2_Y, CPU_IW, line);
        if self.config.show_temp() {
            draw_ascii(display, CPU_IX, BOT_LBL_Y, b"T  E  M  P", dim, bg, 1);
        }

        // GPU Panel Header
        if self.config.show_label() {
            draw_ndot_str(display, GPU_IX, HEAD_Y, b"GPU", 3, fg, bg);
            draw_ascii(display, GPU_IX + GPU_IW - 34, HEAD_Y + 7, b"185 W", dim, bg, 1);
        }

        display.draw_hline(GPU_IX, RULE2_Y, GPU_IW, line);
        if self.config.show_temp() {
            draw_ascii(display, GPU_IX, BOT_LBL_Y, b"T  E  M  P", dim, bg, 1);
        }

        // Initial unlit 24-dot bars
        for i in 0..BAR_DOTS {
            let cx = CPU_IX + ((i as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, BAR_Y, dot_off);

            let gx = GPU_IX + ((i as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, gx, BAR_Y, dot_off);
        }
    }

    fn draw_memory_shell<D: Display>(
        &self,
        display: &mut D,
        bg: Color,
        fg: Color,
        dim: Color,
        line: Color,
        dot_off: Color,
    ) {
        if self.config.show_label() {
            draw_ndot_str(display, PAD_X, HEAD_Y, b"MEMORY", 3, fg, bg);
            draw_ascii(display, WIDTH - PAD_X - 35, HEAD_Y + 7, b"32 GB", dim, bg, 1);
        }

        display.draw_hline(PAD_X, RULE1_Y, WIDTH - (2 * PAD_X), line);
        display.draw_hline(PAD_X, 152, WIDTH - (2 * PAD_X), line);
        display.draw_hline(PAD_X, 210, WIDTH - (2 * PAD_X), line);

        draw_ascii(display, 240, VAL_Y + 12, b"RAM IN USE", dim, bg, 1);

        let bar_x = PAD_X + 64;
        let bar_w = WIDTH - bar_x - PAD_X - 60;

        draw_ndot_str(display, PAD_X, 172, b"USED", 2, fg, bg);
        for i in 0..MEM_DOTS {
            let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (MEM_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, 175, dot_off);
        }

        draw_ndot_str(display, PAD_X, 228, b"FREE", 2, dim, bg);
        for i in 0..MEM_DOTS {
            let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (MEM_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, 231, dot_off);
        }
    }

    fn draw_thermal_shell<D: Display>(
        &self,
        display: &mut D,
        bg: Color,
        fg: Color,
        dim: Color,
        line: Color,
        dot_off: Color,
    ) {
        display.draw_vline(DIV_X, 0, HEIGHT, line);

        // CPU
        draw_ndot_str(display, CPU_IX, HEAD_Y, b"CPU", 3, fg, bg);
        draw_ascii(display, CPU_IX + CPU_IW - 44, HEAD_Y + 7, b"TCTL", dim, bg, 1);
        display.draw_hline(CPU_IX, RULE1_Y, CPU_IW, line);
        display.draw_hline(CPU_IX, RULE2_Y, CPU_IW, line);
        draw_ascii(display, CPU_IX, BOT_LBL_Y, b"T H E R M A L", dim, bg, 1);

        // GPU
        draw_ndot_str(display, GPU_IX, HEAD_Y, b"GPU", 3, fg, bg);
        draw_ascii(display, GPU_IX + GPU_IW - 44, HEAD_Y + 7, b"EDGE", dim, bg, 1);
        display.draw_hline(GPU_IX, RULE1_Y, GPU_IW, line);
        display.draw_hline(GPU_IX, RULE2_Y, GPU_IW, line);
        draw_ascii(display, GPU_IX, BOT_LBL_Y, b"T H E R M A L", dim, bg, 1);

        // Initial unlit 24-dot bars
        for i in 0..BAR_DOTS {
            let cx = CPU_IX + ((i as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, BAR_Y, dot_off);

            let gx = GPU_IX + ((i as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, gx, BAR_Y, dot_off);
        }
    }

    fn draw_minimal_shell<D: Display>(
        &self,
        display: &mut D,
        bg: Color,
        dim: Color,
        line: Color,
        dot_off: Color,
    ) {
        let cx = (WIDTH - 55) / 2;
        draw_ndot_str(display, cx, HEAD_Y + 2, b"PULSE", 2, dim, bg);

        display.draw_hline(PAD_X, RULE1_Y, WIDTH - (2 * PAD_X), line);
        display.draw_hline(PAD_X, RULE2_Y, WIDTH - (2 * PAD_X), line);

        let bar_w = WIDTH - (2 * PAD_X) - 7;
        for i in 0..S_BAR_DOTS {
            let dx = PAD_X + ((i as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, dx, BAR_Y, dot_off);
        }

        let lcx = (WIDTH - 50) / 2;
        draw_ndot_str(display, lcx, BOT_VAL_Y, b"LOAD", 3, dim, bg);
    }

    // ── UPDATERS ──────────────────────────────────────────────────────────────

    fn update_single<D: Display, DELAY: DelayMs>(
        &mut self,
        display: &mut D,
        delay: &mut DELAY,
        val: u8,
        temp: u8,
    ) {
        let (bg, fg, _, _, dot_off) = self.get_palette();

        if val != self.prev_val1 {
            self.draw_big_val(display, PAD_X, val, fg, bg);
            self.prev_val1 = val;
        }

        if self.config.show_temp() && temp != self.prev_temp1 {
            self.draw_temp_val(display, PAD_X, temp, fg, bg);
            self.prev_temp1 = temp;
        }

        // Animate 28-dot bar
        let target = ((val.min(100) as u32 * S_BAR_DOTS as u32 + 50) / 100) as u8;
        let bar_w = WIDTH - (2 * PAD_X) - 7;

        while self.curr_dots1 != target {
            if self.curr_dots1 < target {
                let cx = PAD_X + ((self.curr_dots1 as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, cx, BAR_Y, fg);
                self.curr_dots1 += 1;
            } else {
                self.curr_dots1 -= 1;
                let cx = PAD_X + ((self.curr_dots1 as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, cx, BAR_Y, dot_off);
            }
            delay.delay_ms(8);
        }
    }

    fn update_dual<D: Display, DELAY: DelayMs>(
        &mut self,
        display: &mut D,
        delay: &mut DELAY,
        packet: TelemetryPacket,
    ) {
        let (bg, fg, _, _, dot_off) = self.get_palette();
        let red = Color::new(215, 25, 33);
        let cpu_hot = packet.cpu_temp_c >= 80;
        let gpu_hot = packet.gpu_temp_c >= 80;

        // Big numerals (cell = 11, 77px tall, 9px round dots)
        if packet.cpu_percent != self.prev_val1 {
            self.draw_big_val(display, CPU_IX, packet.cpu_percent, fg, bg);
            self.prev_val1 = packet.cpu_percent;
        }
        if packet.gpu_percent != self.prev_val2 {
            self.draw_big_val(display, GPU_IX, packet.gpu_percent, fg, bg);
            self.prev_val2 = packet.gpu_percent;
        }

        // Temperatures (cell = 7, 49px tall, 5px round dots)
        if self.config.show_temp() {
            if packet.cpu_temp_c != self.prev_temp1 {
                let col = if cpu_hot { red } else { fg };
                self.draw_temp_val(display, CPU_IX, packet.cpu_temp_c, col, bg);
                self.prev_temp1 = packet.cpu_temp_c;
            }
            if packet.gpu_temp_c != self.prev_temp2 {
                let col = if gpu_hot { red } else { fg };
                self.draw_temp_val(display, GPU_IX, packet.gpu_temp_c, col, bg);
                self.prev_temp2 = packet.gpu_temp_c;
            }
        }

        // Animate dual bars
        let target_cpu = ((packet.cpu_percent.min(100) as u32 * BAR_DOTS as u32 + 50) / 100) as u8;
        let target_gpu = ((packet.gpu_percent.min(100) as u32 * BAR_DOTS as u32 + 50) / 100) as u8;

        let cpu_col = if cpu_hot { red } else { fg };
        let gpu_col = if gpu_hot { red } else { fg };

        while self.curr_dots1 != target_cpu || self.curr_dots2 != target_gpu {
            if self.curr_dots1 < target_cpu {
                let dx = CPU_IX + ((self.curr_dots1 as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, cpu_col);
                self.curr_dots1 += 1;
            } else if self.curr_dots1 > target_cpu {
                self.curr_dots1 -= 1;
                let dx = CPU_IX + ((self.curr_dots1 as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, dot_off);
            }

            if self.curr_dots2 < target_gpu {
                let dx = GPU_IX + ((self.curr_dots2 as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, gpu_col);
                self.curr_dots2 += 1;
            } else if self.curr_dots2 > target_gpu {
                self.curr_dots2 -= 1;
                let dx = GPU_IX + ((self.curr_dots2 as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, dot_off);
            }

            delay.delay_ms(8);
        }
    }

    fn update_memory<D: Display>(&mut self, display: &mut D, ram: u8, _temp: u8) {
        let (bg, fg, dim, _, dot_off) = self.get_palette();

        if ram != self.prev_val1 {
            // Draw RAM percentage numeral
            self.draw_big_val(display, PAD_X, ram, fg, bg);

            // Live used GB calculation
            let used_mb = (ram.min(100) as u32 * 320) / 100; // e.g. 204 = 20.4G
            let u_int = (used_mb / 10) as u8;
            let u_dec = (used_mb % 10) as u8;
            let f_int = 32u8.saturating_sub(u_int);

            let bar_x = PAD_X + 64;
            let bar_w = WIDTH - bar_x - PAD_X - 60;

            let used_dots = ((ram.min(100) as u32 * MEM_DOTS as u32 + 50) / 100) as usize;
            for i in 0..MEM_DOTS {
                let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (MEM_DOTS as u32 - 1)) as u16;
                let col = if i < used_dots { fg } else { dot_off };
                draw_dot_circle_7px(display, cx, 175, col);
            }
            self.draw_gb_reading(display, WIDTH - PAD_X - 50, 172, u_int, u_dec, fg, bg);

            let free_dots = MEM_DOTS.saturating_sub(used_dots);
            for i in 0..MEM_DOTS {
                let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (MEM_DOTS as u32 - 1)) as u16;
                let col = if i < free_dots { dim } else { dot_off };
                draw_dot_circle_7px(display, cx, 231, col);
            }
            self.draw_gb_reading(display, WIDTH - PAD_X - 50, 228, f_int, 0, dim, bg);

            self.prev_val1 = ram;
        }
    }

    fn update_thermal<D: Display, DELAY: DelayMs>(
        &mut self,
        display: &mut D,
        delay: &mut DELAY,
        cpu_t: u8,
        gpu_t: u8,
    ) {
        let (bg, fg, dim, _, dot_off) = self.get_palette();
        let red = Color::new(215, 25, 33);
        let cpu_hot = cpu_t >= 80;
        let gpu_hot = gpu_t >= 80;

        let cpu_col = if cpu_hot { red } else { fg };
        let gpu_col = if gpu_hot { red } else { fg };

        if cpu_t != self.prev_temp1 {
            self.draw_big_val(display, CPU_IX, cpu_t, cpu_col, bg);
            draw_ndot_char(display, CPU_IX + 120, VAL_Y + 4, b'*', 7, cpu_col, bg);
            draw_ndot_char(display, CPU_IX + 158, VAL_Y + 4, b'C', 7, cpu_col, bg);

            let status = if cpu_hot { b"HOT TEMP" as &[u8] } else { b"NORMAL" };
            draw_ndot_str(display, CPU_IX, BOT_VAL_Y, status, 3, if cpu_hot { red } else { dim }, bg);
            self.prev_temp1 = cpu_t;
        }

        if gpu_t != self.prev_temp2 {
            self.draw_big_val(display, GPU_IX, gpu_t, gpu_col, bg);
            draw_ndot_char(display, GPU_IX + 120, VAL_Y + 4, b'*', 7, gpu_col, bg);
            draw_ndot_char(display, GPU_IX + 158, VAL_Y + 4, b'C', 7, gpu_col, bg);

            let status = if gpu_hot { b"HOT TEMP" as &[u8] } else { b"NORMAL" };
            draw_ndot_str(display, GPU_IX, BOT_VAL_Y, status, 3, if gpu_hot { red } else { dim }, bg);
            self.prev_temp2 = gpu_t;
        }

        let target_cpu = ((cpu_t.min(100) as u32 * BAR_DOTS as u32 + 50) / 100) as u8;
        let target_gpu = ((gpu_t.min(100) as u32 * BAR_DOTS as u32 + 50) / 100) as u8;

        while self.curr_dots1 != target_cpu || self.curr_dots2 != target_gpu {
            if self.curr_dots1 < target_cpu {
                let dx = CPU_IX + ((self.curr_dots1 as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, cpu_col);
                self.curr_dots1 += 1;
            } else if self.curr_dots1 > target_cpu {
                self.curr_dots1 -= 1;
                let dx = CPU_IX + ((self.curr_dots1 as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, dot_off);
            }

            if self.curr_dots2 < target_gpu {
                let dx = GPU_IX + ((self.curr_dots2 as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, gpu_col);
                self.curr_dots2 += 1;
            } else if self.curr_dots2 > target_gpu {
                self.curr_dots2 -= 1;
                let dx = GPU_IX + ((self.curr_dots2 as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, dot_off);
            }
            delay.delay_ms(8);
        }
    }

    fn update_minimal<D: Display, DELAY: DelayMs>(
        &mut self,
        display: &mut D,
        delay: &mut DELAY,
        val: u8,
    ) {
        let (bg, fg, _, _, dot_off) = self.get_palette();

        if val != self.prev_val1 {
            let cx = (WIDTH - 120) / 2;
            self.draw_big_val(display, cx, val, fg, bg);
            self.prev_val1 = val;
        }

        let target = ((val.min(100) as u32 * S_BAR_DOTS as u32 + 50) / 100) as u8;
        let bar_w = WIDTH - (2 * PAD_X) - 7;

        while self.curr_dots1 != target {
            if self.curr_dots1 < target {
                let dx = PAD_X + ((self.curr_dots1 as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, fg);
                self.curr_dots1 += 1;
            } else {
                self.curr_dots1 -= 1;
                let dx = PAD_X + ((self.curr_dots1 as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, dot_off);
            }
            delay.delay_ms(8);
        }
    }

    // ── PRIMITIVES ────────────────────────────────────────────────────────────

    /// Draws a high-contrast 77px tall numeral using cell = 11 with 9px smooth circular dots.
    fn draw_big_val<D: Display>(&self, display: &mut D, ix: u16, val: u8, fg: Color, bg: Color) {
        let val = val.min(100);
        let (_, _, dim, _, _) = self.get_palette();
        let pct_y = VAL_Y + 56;

        if val >= 100 {
            draw_ndot_char(display, ix, VAL_Y, b'1', 11, fg, bg);
            display.fill_rect(ix + 55, VAL_Y, 6, 77, bg);
            draw_ndot_char(display, ix + 61, VAL_Y, b'0', 11, fg, bg);
            display.fill_rect(ix + 116, VAL_Y, 6, 77, bg);
            draw_ndot_char(display, ix + 122, VAL_Y, b'0', 11, fg, bg);

            let tail_x = ix + 122 + 55;
            if tail_x < ix + CPU_IW {
                display.fill_rect(tail_x, VAL_Y, (ix + CPU_IW) - tail_x, 77, bg);
            }
            if self.config.show_units() {
                draw_ascii(display, tail_x + 6, pct_y, b"%", dim, bg, 3);
            }
        } else if val < 10 {
            let d = val + b'0';
            draw_ndot_char(display, ix, VAL_Y, d, 11, fg, bg);
            display.fill_rect(ix + 55, VAL_Y, CPU_IW - 55, 77, bg);
            if self.config.show_units() {
                draw_ascii(display, ix + 61, pct_y, b"%", dim, bg, 3);
            }
        } else {
            let d0 = (val / 10) + b'0';
            let d1 = (val % 10) + b'0';
            draw_ndot_char(display, ix, VAL_Y, d0, 11, fg, bg);
            display.fill_rect(ix + 55, VAL_Y, 11, 77, bg);
            draw_ndot_char(display, ix + 66, VAL_Y, d1, 11, fg, bg);

            let tail_x = ix + 121;
            if tail_x < ix + CPU_IW {
                display.fill_rect(tail_x, VAL_Y, (ix + CPU_IW) - tail_x, 77, bg);
            }
            if self.config.show_units() {
                draw_ascii(display, tail_x + 6, pct_y, b"%", dim, bg, 3);
            }
        }
    }

    /// Draws a 49px tall temperature numeral using cell = 7 with 5px smooth circular dots.
    fn draw_temp_val<D: Display>(&self, display: &mut D, ix: u16, temp: u8, fg: Color, bg: Color) {
        let t = temp.min(99);
        let tens = (t / 10) + b'0';
        let ones = (t % 10) + b'0';

        let mut x = ix;
        draw_ndot_char(display, x, BOT_VAL_Y, tens, 7, fg, bg);
        x += 35 + 7;
        draw_ndot_char(display, x, BOT_VAL_Y, ones, 7, fg, bg);
        x += 35 + 7;
        draw_ndot_char(display, x, BOT_VAL_Y, b'*', 7, fg, bg); // degree symbol
        x += 35 + 7;
        draw_ndot_char(display, x, BOT_VAL_Y, b'C', 7, fg, bg);
    }

    /// Draws a compact gigabyte string like "20.5G" in 2px NDot font.
    fn draw_gb_reading<D: Display>(
        &self,
        display: &mut D,
        x: u16,
        y: u16,
        gb_int: u8,
        gb_dec: u8,
        fg: Color,
        bg: Color,
    ) {
        let mut cx = x;
        if gb_int >= 10 {
            draw_ndot_char(display, cx, y, (gb_int / 10) + b'0', 2, fg, bg);
            cx += 12;
        }
        draw_ndot_char(display, cx, y, (gb_int % 10) + b'0', 2, fg, bg);
        cx += 12;

        if gb_dec > 0 {
            display.fill_rect(cx, y + 10, 2, 2, fg);
            cx += 4;
            draw_ndot_char(display, cx, y, gb_dec + b'0', 2, fg, bg);
            cx += 12;
        }

        draw_ndot_char(display, cx, y, b'G', 2, fg, bg);
    }
}
