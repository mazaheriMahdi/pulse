//! PULSE — Nothing-style 480×320 Hardware Monitor Dashboard.
//!
//! Exact implementation of the Nothing OS design language:
//! - Pure black canvas (#000000)
//! - Giant 77px tall 5×7 NDot numerals with 9px circular dots
//! - Low-positioned 24-dot Glyph progress bars with chunky 7px circular dots
//! - Smooth parallel filling/draining animation on load changes
//! - Hairline rules (#262626), near-zero radius
//! - Nothing red (#D71921) reserved for warnings and top status indicator
//! - Dual-panel layout: CPU on left, GPU on right

use crate::display::Color;
use crate::font::draw_ascii;
use crate::ndot::{draw_dot_circle_6px, draw_dot_circle_7px, draw_ndot_char, draw_ndot_str};
use crate::traits::{DelayMs, Display};
use gadget_common::TelemetryPacket;

// ── Palette (Nothing Design Language) ─────────────────────────────────────────
pub const BG: Color = Color::new(0, 0, 0);               // #000000 pure black
pub const LINE: Color = Color::new(38, 38, 38);          // #262626 hairline rule
pub const TEXT_WHITE: Color = Color::new(255, 255, 255); // #ffffff pure white
pub const DIM: Color = Color::new(107, 107, 107);        // #6b6b6b dim text
pub const DIMMER: Color = Color::new(31, 31, 31);        // #1f1f1f inactive ticks
pub const DOT_OFF: Color = Color::new(28, 28, 28);       // #1c1c1c dot off
pub const RED: Color = Color::new(215, 25, 33);          // #d71921 Nothing red

// ── Screen Geometry (480 × 320) ───────────────────────────────────────────────
const SCREEN_PAD: u16 = 12;
const CONTENT_X0: u16 = SCREEN_PAD;
const CONTENT_X1: u16 = 480 - SCREEN_PAD; // 468 px
const CONTENT_W: u16 = CONTENT_X1 - CONTENT_X0; // 456 px

const TOPBAR_Y: u16 = 16;
const RULE_Y: u16 = 44;
const DIV_X: u16 = 240;

const PANEL_Y0: u16 = 45;
const PANEL_Y1: u16 = 308;
const PANEL_H: u16 = PANEL_Y1 - PANEL_Y0;

// Panel inner bounds
const CPU_IX: u16 = 24;
const CPU_IW: u16 = 204;

const GPU_IX: u16 = 253;
const GPU_IW: u16 = 203;

// Internal vertical offsets inside panels (balanced, zero empty gap)
const HEAD_Y: u16 = 56;
const VAL_Y: u16 = 82;     // cell = 11 -> 77px tall numerals (82..159)
const BAR_Y: u16 = 186;    // moved lower, 7px dots (186..193)
const TRULE_Y: u16 = 216;  // hairline rule
const TLBL_Y: u16 = 227;   // TEMP label
const TVAL_Y: u16 = 242;   // cell = 7 -> 49px tall temperature (242..291)

const BAR_DOTS: usize = 24;

// ── Dashboard State ───────────────────────────────────────────────────────────
pub struct Dashboard {
    last: Option<TelemetryPacket>,
    initialized: bool,
    tick: u8,
    prev_cpu_val: u8,
    prev_gpu_val: u8,
    prev_cpu_temp: u8,
    prev_gpu_temp: u8,
    curr_cpu_dots: u8,
    curr_gpu_dots: u8,
}

impl Dashboard {
    pub fn new() -> Self {
        Self {
            last: None,
            initialized: false,
            tick: 0,
            prev_cpu_val: 255,
            prev_gpu_val: 255,
            prev_cpu_temp: 255,
            prev_gpu_temp: 255,
            curr_cpu_dots: 0,
            curr_gpu_dots: 0,
        }
    }

    /// Draws the complete static shell once on boot.
    pub fn draw_layout<D: Display>(&mut self, display: &mut D) {
        // 1. Pure black canvas
        display.fill_rect(0, 0, 480, 320, BG);

        // 2. Outer hairline screen border (1px)
        display.draw_rect(0, 0, 480, 320, LINE);

        // 3. Top bar: "PULSE" wordmark + Nothing red dot
        draw_ndot_str(display, CONTENT_X0, TOPBAR_Y, b"PULSE", 2, TEXT_WHITE, BG);
        // Red dot: 6px diameter circle next to PULSE
        draw_dot_circle_6px(display, CONTENT_X0 + 64, TOPBAR_Y + 4, RED);

        // Glyph tick strip (5 vertical marks)
        self.draw_glyph_strip(display);

        // 4. Horizontal hairline divider below top bar
        display.draw_hline(CONTENT_X0, RULE_Y, CONTENT_W, LINE);

        // 5. Vertical center hairline divider between CPU and GPU
        display.draw_vline(DIV_X, PANEL_Y0, PANEL_H, LINE);

        // 6. CPU Panel Shell
        draw_ndot_str(display, CPU_IX, HEAD_Y, b"CPU", 3, TEXT_WHITE, BG);
        draw_ascii(display, CPU_IX + CPU_IW - 44, HEAD_Y + 7, b"4.2 GHZ", DIM, BG, 1);

        display.draw_hline(CPU_IX, TRULE_Y, CPU_IW, LINE);
        draw_ascii(display, CPU_IX, TLBL_Y, b"T  E  M  P", DIM, BG, 1);

        // 7. GPU Panel Shell
        draw_ndot_str(display, GPU_IX, HEAD_Y, b"GPU", 3, TEXT_WHITE, BG);
        draw_ascii(display, GPU_IX + GPU_IW - 34, HEAD_Y + 7, b"185 W", DIM, BG, 1);

        display.draw_hline(GPU_IX, TRULE_Y, GPU_IW, LINE);
        draw_ascii(display, GPU_IX, TLBL_Y, b"T  E  M  P", DIM, BG, 1);

        // Initial unlit 24-dot bars
        for i in 0..BAR_DOTS {
            let cx = CPU_IX + ((i as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, cx, BAR_Y, DOT_OFF);

            let gx = GPU_IX + ((i as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
            draw_dot_circle_7px(display, gx, BAR_Y, DOT_OFF);
        }

        self.initialized = true;
    }

    /// Differential update: redraws dynamic metrics and animates progress bars filling/draining.
    pub fn update<D: Display, DELAY: DelayMs>(
        &mut self,
        display: &mut D,
        delay: &mut DELAY,
        packet: TelemetryPacket,
    ) {
        if !self.initialized {
            self.draw_layout(display);
        }

        self.tick = (self.tick + 1) % 5;
        self.draw_glyph_strip(display);

        let cpu_hot = packet.cpu_temp_c >= 80;
        let gpu_hot = packet.gpu_temp_c >= 80;

        // ── Big Numerals (cell = 11, 77px tall) ──────────────────────────────
        if packet.cpu_percent != self.prev_cpu_val {
            self.draw_big_val(display, CPU_IX, packet.cpu_percent);
            self.prev_cpu_val = packet.cpu_percent;
        }

        if packet.gpu_percent != self.prev_gpu_val {
            self.draw_big_val(display, GPU_IX, packet.gpu_percent);
            self.prev_gpu_val = packet.gpu_percent;
        }

        // ── Temperature Readouts ──────────────────────────────────────────────
        if packet.cpu_temp_c != self.prev_cpu_temp {
            self.draw_temp_val(display, CPU_IX, packet.cpu_temp_c, cpu_hot);
            self.prev_cpu_temp = packet.cpu_temp_c;
        }

        if packet.gpu_temp_c != self.prev_gpu_temp {
            self.draw_temp_val(display, GPU_IX, packet.gpu_temp_c, gpu_hot);
            self.prev_gpu_temp = packet.gpu_temp_c;
        }

        // ── Animated Progress Bars (Chunky 7px Dots) ──────────────────────────
        let target_cpu = ((packet.cpu_percent.min(100) as u32 * BAR_DOTS as u32 + 50) / 100) as u8;
        let target_gpu = ((packet.gpu_percent.min(100) as u32 * BAR_DOTS as u32 + 50) / 100) as u8;

        let cpu_on_col = if cpu_hot { RED } else { TEXT_WHITE };
        let gpu_on_col = if gpu_hot { RED } else { TEXT_WHITE };

        // Animate both bars in lockstep
        while self.curr_cpu_dots != target_cpu || self.curr_gpu_dots != target_gpu {
            if self.curr_cpu_dots < target_cpu {
                let dx = CPU_IX + ((self.curr_cpu_dots as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, cpu_on_col);
                self.curr_cpu_dots += 1;
            } else if self.curr_cpu_dots > target_cpu {
                self.curr_cpu_dots -= 1;
                let dx = CPU_IX + ((self.curr_cpu_dots as u32 * (CPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, DOT_OFF);
            }

            if self.curr_gpu_dots < target_gpu {
                let dx = GPU_IX + ((self.curr_gpu_dots as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, gpu_on_col);
                self.curr_gpu_dots += 1;
            } else if self.curr_gpu_dots > target_gpu {
                self.curr_gpu_dots -= 1;
                let dx = GPU_IX + ((self.curr_gpu_dots as u32 * (GPU_IW as u32 - 7)) / (BAR_DOTS as u32 - 1)) as u16;
                draw_dot_circle_7px(display, dx, BAR_Y, DOT_OFF);
            }

            delay.delay_ms(10);
        }

        self.last = Some(packet);
    }

    // ── Metric Renderers ──────────────────────────────────────────────────────

    /// Draws giant 5×7 dot-matrix load numeral (cell = 11, 77px tall, 9px dots).
    /// Strictly left-aligned at `ix` regardless of whether value is 1, 2, or 3 digits.
    /// The `%` symbol dynamically hugs the right side of the final digit with a 6px gap.
    fn draw_big_val<D: Display>(&self, display: &mut D, ix: u16, val: u8) {
        let val = val.min(100);
        let pct_y = VAL_Y + 56;

        if val >= 100 {
            // 3 digits: '1', '0', '0'
            draw_ndot_char(display, ix, VAL_Y, b'1', 11, TEXT_WHITE, BG);
            display.fill_rect(ix + 55, VAL_Y, 6, 77, BG);
            draw_ndot_char(display, ix + 61, VAL_Y, b'0', 11, TEXT_WHITE, BG);
            display.fill_rect(ix + 116, VAL_Y, 6, 77, BG);
            draw_ndot_char(display, ix + 122, VAL_Y, b'0', 11, TEXT_WHITE, BG);

            let pct_x = ix + 122 + 55 + 6;
            draw_ascii(display, pct_x, pct_y, b"%", DIM, BG, 3);
            let clear_x = pct_x + 18;
            if clear_x < ix + CPU_IW {
                display.fill_rect(clear_x, VAL_Y, (ix + CPU_IW) - clear_x, 77, BG);
            }
        } else if val < 10 {
            // Single digit: strictly left-aligned at `ix`!
            let d = val + b'0';
            draw_ndot_char(display, ix, VAL_Y, d, 11, TEXT_WHITE, BG);

            // '%' follows immediately after the single digit
            let pct_x = ix + 55 + 6;
            draw_ascii(display, pct_x, pct_y, b"%", DIM, BG, 3);

            // Clean up any trailing pixels where previous 2nd digit or % was
            let clear_x = pct_x + 18;
            if clear_x < ix + CPU_IW {
                display.fill_rect(clear_x, VAL_Y, (ix + CPU_IW) - clear_x, 77, BG);
            }
        } else {
            // Two digits: strictly left-aligned at `ix`!
            let d0 = (val / 10) + b'0';
            let d1 = (val % 10) + b'0';
            draw_ndot_char(display, ix, VAL_Y, d0, 11, TEXT_WHITE, BG);
            display.fill_rect(ix + 55, VAL_Y, 11, 77, BG);
            draw_ndot_char(display, ix + 66, VAL_Y, d1, 11, TEXT_WHITE, BG);

            // '%' follows immediately after the 2nd digit
            let pct_x = ix + 121 + 6;
            draw_ascii(display, pct_x, pct_y, b"%", DIM, BG, 3);

            // Clean up any trailing pixels beyond %
            let clear_x = pct_x + 18;
            if clear_x < ix + CPU_IW {
                display.fill_rect(clear_x, VAL_Y, (ix + CPU_IW) - clear_x, 77, BG);
            }
        }
    }

    /// Draws temperature in 5×7 dot-matrix (cell = 7, 49px tall, 5px dots).
    fn draw_temp_val<D: Display>(&self, display: &mut D, ix: u16, temp: u8, hot: bool) {
        let col = if hot { RED } else { TEXT_WHITE };
        let t = temp.min(99);
        let tens = (t / 10) + b'0';
        let ones = (t % 10) + b'0';

        let mut x = ix;
        draw_ndot_char(display, x, TVAL_Y, tens, 7, col, BG);
        x += 35 + 7;
        draw_ndot_char(display, x, TVAL_Y, ones, 7, col, BG);
        x += 35 + 7;
        draw_ndot_char(display, x, TVAL_Y, b'*', 7, col, BG); // degree symbol
        x += 35 + 7;
        draw_ndot_char(display, x, TVAL_Y, b'C', 7, col, BG);
    }

    /// Draws the Nothing glyph tick marks on the top right.
    fn draw_glyph_strip<D: Display>(&self, display: &mut D) {
        let base_x = CONTENT_X1 - 30;
        let y = TOPBAR_Y + 2;

        for i in 0..5 {
            let x = base_x + i * 7;
            let col = if i == 4 {
                DIMMER
            } else {
                TEXT_WHITE
            };
            display.fill_rect(x, y, 2, 12, col);
        }
    }
}
