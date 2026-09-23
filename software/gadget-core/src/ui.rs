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
use crate::ndot::{draw_dot_circle_7px, draw_ndot_char, draw_ndot_str};
use crate::traits::{DelayMs, Display};
use gadget_common::TelemetryPacket;

// ── Palette (Nothing Design Language) ─────────────────────────────────────────
pub const BG: Color = Color::new(0, 0, 0);               // #000000 pure black
pub const LINE: Color = Color::new(38, 38, 38);          // #262626 hairline rule
pub const TEXT_WHITE: Color = Color::new(255, 255, 255); // #ffffff pure white
pub const DIM: Color = Color::new(107, 107, 107);        // #6b6b6b dim text
pub const DOT_OFF: Color = Color::new(28, 28, 28);       // #1c1c1c dot off
pub const RED: Color = Color::new(215, 25, 33);          // #d71921 Nothing red

// ── Screen Geometry (480 × 320) ───────────────────────────────────────────────
const DIV_X: u16 = 240;

// Panel inner bounds
const CPU_IX: u16 = 16;
const CPU_IW: u16 = 208;

const GPU_IX: u16 = 256;
const GPU_IW: u16 = 208;

// Internal vertical offsets inside panels (balanced, edge-to-edge)
const HEAD_Y: u16 = 20;
const VAL_Y: u16 = 56;     // cell = 11 -> 77px tall numerals (56..133)
const BAR_Y: u16 = 160;    // 7px dots (160..167)
const TRULE_Y: u16 = 194;  // hairline rule
const TLBL_Y: u16 = 208;   // TEMP label
const TVAL_Y: u16 = 232;   // cell = 7 -> 49px tall temperature (232..281)

const BAR_DOTS: usize = 24;

// ── Dashboard State ───────────────────────────────────────────────────────────
pub struct Dashboard {
    last: Option<TelemetryPacket>,
    initialized: bool,
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

        // 2. Vertical center hairline divider between CPU and GPU
        display.draw_vline(DIV_X, 0, 320, LINE);

        // 3. CPU Panel Shell
        draw_ndot_str(display, CPU_IX, HEAD_Y, b"CPU", 3, TEXT_WHITE, BG);
        draw_ascii(display, CPU_IX + CPU_IW - 44, HEAD_Y + 7, b"4.2 GHZ", DIM, BG, 1);

        display.draw_hline(CPU_IX, TRULE_Y, CPU_IW, LINE);
        draw_ascii(display, CPU_IX, TLBL_Y, b"T  E  M  P", DIM, BG, 1);

        // 4. GPU Panel Shell
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
    /// Wipes the entire right-hand area cleanly so zero leftover artifacts from previous digits remain.
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

            // Clean right area beyond 3rd digit
            let tail_x = ix + 122 + 55;
            if tail_x < ix + CPU_IW {
                display.fill_rect(tail_x, VAL_Y, (ix + CPU_IW) - tail_x, 77, BG);
            }
            draw_ascii(display, tail_x + 6, pct_y, b"%", DIM, BG, 3);
        } else if val < 10 {
            // Single digit: strictly left-aligned at `ix`!
            let d = val + b'0';
            draw_ndot_char(display, ix, VAL_Y, d, 11, TEXT_WHITE, BG);

            // Wipe ENTIRE area to the right of digit 1 (wipes all traces of previous 2nd digit and old %)
            display.fill_rect(ix + 55, VAL_Y, CPU_IW - 55, 77, BG);

            // Draw '%' cleanly after the single digit
            let pct_x = ix + 55 + 6;
            draw_ascii(display, pct_x, pct_y, b"%", DIM, BG, 3);
        } else {
            // Two digits: strictly left-aligned at `ix`!
            let d0 = (val / 10) + b'0';
            let d1 = (val % 10) + b'0';
            draw_ndot_char(display, ix, VAL_Y, d0, 11, TEXT_WHITE, BG);
            display.fill_rect(ix + 55, VAL_Y, 11, 77, BG);
            draw_ndot_char(display, ix + 66, VAL_Y, d1, 11, TEXT_WHITE, BG);

            // Wipe ENTIRE area to the right of digit 2 (wipes any old 3rd digit or previous % positions)
            let tail_x = ix + 121;
            if tail_x < ix + CPU_IW {
                display.fill_rect(tail_x, VAL_Y, (ix + CPU_IW) - tail_x, 77, BG);
            }

            // Draw '%' cleanly after digit 2
            let pct_x = tail_x + 6;
            draw_ascii(display, pct_x, pct_y, b"%", DIM, BG, 3);
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
}
