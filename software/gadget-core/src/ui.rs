//! PULSE — Nothing-style 480×320 Hardware Monitor Dashboard.
//!
//! Multi-face engine supporting:
//! - Face 0: CPU Grid (Single giant NDot load, top temp, bottom 28-dot bar)
//! - Face 1: GPU Grid (Single giant NDot load, top temp, bottom 28-dot bar)
//! - Face 2: Dual Load (Edge-to-edge dual CPU + GPU panel layout)
//! - Face 3: Memory (RAM percentage + Used/Free gauge bars)
//! - Face 4: Thermal (Side-by-side CPU & GPU temperatures)
//! - Face 5: Minimal (Massive centered load numeral + subtitle)

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

// Vertical offsets inside dual panels
const HEAD_Y: u16 = 20;
const VAL_Y: u16 = 56;     // cell = 11 -> 77px tall numerals
const BAR_Y: u16 = 160;    // 7px dots
const TRULE_Y: u16 = 194;  // hairline rule
const TLBL_Y: u16 = 208;   // TEMP label
const TVAL_Y: u16 = 232;   // cell = 7 -> 49px tall temperature
const BAR_DOTS: usize = 24;

// Single panel (Face 0 & 1) geometry
const S_MARGIN_X: u16 = 24;
const S_VAL_Y: u16 = 70;
const S_BAR_Y: u16 = 270;
const S_BAR_DOTS: usize = 28;

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
            0 => self.draw_single_shell(display, b"CPU", bg, fg, dim, dot_off),
            1 => self.draw_single_shell(display, b"GPU", bg, fg, dim, dot_off),
            2 => self.draw_dual_shell(display, bg, fg, dim, line, dot_off),
            3 => self.draw_memory_shell(display, bg, fg, dim, line),
            4 => self.draw_thermal_shell(display, bg, fg, dim, line),
            5 => self.draw_minimal_shell(display, bg, dim),
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
            4 => self.update_thermal(display, packet.cpu_temp_c, packet.gpu_temp_c),
            5 => self.update_minimal(display, packet.cpu_percent),
            _ => self.update_dual(display, delay, packet),
        }

        self.last = Some(packet);
    }

    // ── SHELL DRAWERS ─────────────────────────────────────────────────────────

    fn draw_single_shell<D: Display>(
        &self,
        display: &mut D,
        lbl: &[u8],
        _bg: Color,
        fg: Color,
        dim: Color,
        dot_off: Color,
    ) {
        let (bg, _, _, _, _) = self.get_palette();
        if self.config.show_label() {
            draw_ndot_str(display, S_MARGIN_X, HEAD_Y, lbl, 3, fg, bg);
        }

        // Draw initial unlit 28-dot bar
        let bar_w = WIDTH - (2 * S_MARGIN_X) - 7;
        for i in 0..S_BAR_DOTS {
            let cx = S_MARGIN_X + ((i as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, S_BAR_Y, dot_off);
        }

        if self.config.show_units() {
            draw_ascii(display, WIDTH - S_MARGIN_X - 12, S_BAR_Y - 2, b"%", dim, bg, 2);
        }
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

        display.draw_hline(CPU_IX, TRULE_Y, CPU_IW, line);
        if self.config.show_temp() {
            draw_ascii(display, CPU_IX, TLBL_Y, b"T  E  M  P", dim, bg, 1);
        }

        // GPU Panel Header
        if self.config.show_label() {
            draw_ndot_str(display, GPU_IX, HEAD_Y, b"GPU", 3, fg, bg);
            draw_ascii(display, GPU_IX + GPU_IW - 34, HEAD_Y + 7, b"185 W", dim, bg, 1);
        }

        display.draw_hline(GPU_IX, TRULE_Y, GPU_IW, line);
        if self.config.show_temp() {
            draw_ascii(display, GPU_IX, TLBL_Y, b"T  E  M  P", dim, bg, 1);
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
        _line: Color,
    ) {
        let (_, _, _, _, dot_off) = self.get_palette();
        if self.config.show_label() {
            draw_ndot_str(display, S_MARGIN_X, HEAD_Y, b"MEMORY", 3, fg, bg);
        }

        let bar_x = S_MARGIN_X + 64;
        let bar_w = WIDTH - bar_x - S_MARGIN_X - 60;
        let mem_dots: usize = 20;

        draw_ndot_str(display, S_MARGIN_X, 190, b"USED", 2, fg, bg);
        for i in 0..mem_dots {
            let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (mem_dots as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, 194, dot_off);
        }

        draw_ndot_str(display, S_MARGIN_X, 230, b"FREE", 2, dim, bg);
        for i in 0..mem_dots {
            let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (mem_dots as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, 234, dot_off);
        }
    }

    fn draw_thermal_shell<D: Display>(
        &self,
        display: &mut D,
        bg: Color,
        fg: Color,
        dim: Color,
        line: Color,
    ) {
        if self.config.show_label() {
            draw_ndot_str(display, S_MARGIN_X, HEAD_Y, b"THERMAL", 3, fg, bg);
        }
        if self.config.show_units() {
            draw_ascii(display, WIDTH - S_MARGIN_X - 16, HEAD_Y + 4, b"*C", dim, bg, 2);
        }

        // Divider
        display.draw_vline(DIV_X, 50, HEIGHT - 50, line);

        // Tags in dot matrix
        draw_ndot_str(display, S_MARGIN_X, 80, b"CPU", 3, dim, bg);
        draw_ndot_str(display, DIV_X + S_MARGIN_X, 80, b"GPU", 3, dim, bg);
    }

    fn draw_minimal_shell<D: Display>(&self, display: &mut D, bg: Color, dim: Color) {
        if self.config.show_label() {
            let cx = (WIDTH - 75) / 2;
            draw_ndot_str(display, cx, 230, b"CPU", 3, dim, bg);
        }
    }

    // ── UPDATERS ──────────────────────────────────────────────────────────────

    fn update_single<D: Display, DELAY: DelayMs>(
        &mut self,
        display: &mut D,
        delay: &mut DELAY,
        val: u8,
        temp: u8,
    ) {
        let (bg, fg, _dim, _, dot_off) = self.get_palette();

        if val != self.prev_val1 {
            // Draw large single load numeral (cell = 14 -> 98px tall)
            self.draw_huge_val(display, S_MARGIN_X, S_VAL_Y, val, fg, bg);
            self.prev_val1 = val;
        }

        if self.config.show_temp() && temp != self.prev_temp1 {
            // Draw top-right temp
            let tx = WIDTH - S_MARGIN_X - 60;
            self.draw_mini_temp(display, tx, HEAD_Y + 4, temp, fg, bg);
            self.prev_temp1 = temp;
        }

        // Animate 28-dot bar
        let target = ((val.min(100) as u32 * S_BAR_DOTS as u32 + 50) / 100) as u8;
        let bar_w = WIDTH - (2 * S_MARGIN_X) - 7;

        while self.curr_dots1 != target {
            if self.curr_dots1 < target {
                let cx = S_MARGIN_X + ((self.curr_dots1 as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, cx, S_BAR_Y, fg);
                self.curr_dots1 += 1;
            } else {
                self.curr_dots1 -= 1;
                let cx = S_MARGIN_X + ((self.curr_dots1 as u32 * bar_w as u32) / (S_BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, cx, S_BAR_Y, dot_off);
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

        // Big numerals
        if packet.cpu_percent != self.prev_val1 {
            self.draw_big_val(display, CPU_IX, packet.cpu_percent, fg, bg);
            self.prev_val1 = packet.cpu_percent;
        }
        if packet.gpu_percent != self.prev_val2 {
            self.draw_big_val(display, GPU_IX, packet.gpu_percent, fg, bg);
            self.prev_val2 = packet.gpu_percent;
        }

        // Temperatures
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

    fn update_memory<D: Display>(&mut self, display: &mut D, ram: u8, temp: u8) {
        let (bg, fg, dim, _line, dot_off) = self.get_palette();

        if ram != self.prev_val1 {
            // Draw RAM percentage numeral
            self.draw_huge_val(display, S_MARGIN_X, S_VAL_Y, ram, fg, bg);

            // Horizontal circular dot bars
            let bar_x = S_MARGIN_X + 64;
            let bar_w = WIDTH - bar_x - S_MARGIN_X - 60;
            let mem_dots: usize = 20;

            let used_dots = ((ram.min(100) as u32 * mem_dots as u32 + 50) / 100) as usize;
            for i in 0..mem_dots {
                let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (mem_dots as u32 - 1)) as u16;
                let col = if i < used_dots { fg } else { dot_off };
                draw_dot_circle_7px(display, cx, 194, col);
            }

            let free_dots = mem_dots.saturating_sub(used_dots);
            for i in 0..mem_dots {
                let cx = bar_x + ((i as u32 * (bar_w as u32 - 7)) / (mem_dots as u32 - 1)) as u16;
                let col = if i < free_dots { dim } else { dot_off };
                draw_dot_circle_7px(display, cx, 234, col);
            }

            self.prev_val1 = ram;
        }

        if self.config.show_temp() && temp != self.prev_temp1 {
            let tx = WIDTH - S_MARGIN_X - 60;
            self.draw_mini_temp(display, tx, HEAD_Y + 4, temp, fg, bg);
            self.prev_temp1 = temp;
        }
    }

    fn update_thermal<D: Display>(&mut self, display: &mut D, cpu_t: u8, gpu_t: u8) {
        let (bg, fg, _, _, _) = self.get_palette();

        if cpu_t != self.prev_temp1 {
            self.draw_huge_val(display, S_MARGIN_X, 130, cpu_t, fg, bg);
            self.prev_temp1 = cpu_t;
        }

        if gpu_t != self.prev_temp2 {
            self.draw_huge_val(display, DIV_X + S_MARGIN_X, 130, gpu_t, fg, bg);
            self.prev_temp2 = gpu_t;
        }
    }

    fn update_minimal<D: Display>(&mut self, display: &mut D, cpu: u8) {
        let (bg, fg, _, _, _) = self.get_palette();

        if cpu != self.prev_val1 {
            let cx = (WIDTH - 150) / 2;
            self.draw_huge_val(display, cx, 110, cpu, fg, bg);
            self.prev_val1 = cpu;
        }
    }

    // ── PRIMITIVES ────────────────────────────────────────────────────────────

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

    fn draw_huge_val<D: Display>(&self, display: &mut D, x: u16, y: u16, val: u8, fg: Color, bg: Color) {
        let val = val.min(100);
        let cell = 14; // 14px per dot cell -> 98px tall numeral
        let digit_w = 5 * cell; // 70px

        if val >= 100 {
            draw_ndot_char(display, x, y, b'1', cell, fg, bg);
            draw_ndot_char(display, x + digit_w + 10, y, b'0', cell, fg, bg);
            draw_ndot_char(display, x + (digit_w + 10) * 2, y, b'0', cell, fg, bg);
        } else if val < 10 {
            draw_ndot_char(display, x, y, val + b'0', cell, fg, bg);
            display.fill_rect(x + digit_w, y, digit_w * 2 + 20, 7 * cell, bg);
        } else {
            draw_ndot_char(display, x, y, (val / 10) + b'0', cell, fg, bg);
            draw_ndot_char(display, x + digit_w + 12, y, (val % 10) + b'0', cell, fg, bg);
            display.fill_rect(x + (digit_w + 12) * 2, y, digit_w, 7 * cell, bg);
        }
    }

    fn draw_temp_val<D: Display>(&self, display: &mut D, ix: u16, temp: u8, fg: Color, bg: Color) {
        let t = temp.min(99);
        let tens = (t / 10) + b'0';
        let ones = (t % 10) + b'0';

        let mut x = ix;
        draw_ndot_char(display, x, TVAL_Y, tens, 7, fg, bg);
        x += 35 + 7;
        draw_ndot_char(display, x, TVAL_Y, ones, 7, fg, bg);
        x += 35 + 7;
        draw_ndot_char(display, x, TVAL_Y, b'*', 7, fg, bg); // degree symbol
        x += 35 + 7;
        draw_ndot_char(display, x, TVAL_Y, b'C', 7, fg, bg);
    }

    fn draw_mini_temp<D: Display>(&self, display: &mut D, x: u16, y: u16, temp: u8, fg: Color, bg: Color) {
        let t = temp.min(99);
        let tens = (t / 10) + b'0';
        let ones = (t % 10) + b'0';
        let mut cx = x;
        draw_ndot_char(display, cx, y, tens, 3, fg, bg);
        cx += 18;
        draw_ndot_char(display, cx, y, ones, 3, fg, bg);
        cx += 18;
        draw_ndot_char(display, cx, y, b'*', 3, fg, bg);
        cx += 18;
        draw_ndot_char(display, cx, y, b'C', 3, fg, bg);
    }
}
