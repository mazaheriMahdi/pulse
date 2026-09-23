//! Platform-agnostic HAL traits for gadget-core.
//! These minimal traits allow gadget-core to run unchanged on Arduino Uno,
//! ESP32 (esp-idf-hal or esp-hal), RP2040, STM32, or test harnesses.

pub trait SpiWrite {
    fn write_byte(&mut self, byte: u8);

    fn write_bytes(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.write_byte(b);
        }
    }

    fn write_repeated(&mut self, byte: u8, count: usize) {
        for _ in 0..count {
            self.write_byte(byte);
        }
    }
}

pub trait PinWrite {
    fn set_high(&mut self);
    fn set_low(&mut self);
}

pub trait DelayMs {
    fn delay_ms(&mut self, ms: u16);
}

use crate::display::{Color, Ili9488, HEIGHT, WIDTH};

/// Platform-agnostic display drawing trait.
pub trait Display {
    fn fill_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color);
    fn draw_pixel(&mut self, x: u16, y: u16, color: Color);

    #[inline(always)]
    fn draw_hline(&mut self, x: u16, y: u16, len: u16, color: Color) {
        self.fill_rect(x, y, len, 1, color);
    }

    #[inline(always)]
    fn draw_vline(&mut self, x: u16, y: u16, len: u16, color: Color) {
        self.fill_rect(x, y, 1, len, color);
    }

    #[inline(always)]
    fn draw_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color) {
        self.draw_hline(x, y, w, color);
        self.draw_hline(x, y + h - 1, w, color);
        self.draw_vline(x, y, h, color);
        self.draw_vline(x + w - 1, y, h, color);
    }

    #[inline(always)]
    fn clear(&mut self, color: Color) {
        self.fill_rect(0, 0, WIDTH, HEIGHT, color);
    }

    fn draw_line(&mut self, mut x0: u16, mut y0: u16, x1: u16, y1: u16, color: Color) {
        if y0 == y1 {
            let min_x = x0.min(x1);
            let len = (x0 as i16 - x1 as i16).unsigned_abs() as u16 + 1;
            self.draw_hline(min_x, y0, len, color);
            return;
        }
        if x0 == x1 {
            let min_y = y0.min(y1);
            let len = (y0 as i16 - y1 as i16).unsigned_abs() as u16 + 1;
            self.draw_vline(x0, min_y, len, color);
            return;
        }

        let dx = (x1 as i16 - x0 as i16).abs();
        let dy = -(y1 as i16 - y0 as i16).abs();
        let sx: i16 = if x0 < x1 { 1 } else { -1 };
        let sy: i16 = if y0 < y1 { 1 } else { -1 };
        let mut err = dx + dy;

        loop {
            self.draw_pixel(x0, y0, color);
            if x0 == x1 && y0 == y1 {
                break;
            }
            let e2 = 2 * err;
            if e2 >= dy {
                err += dy;
                x0 = (x0 as i16 + sx) as u16;
            }
            if e2 <= dx {
                err += dx;
                y0 = (y0 as i16 + sy) as u16;
            }
        }
    }
}

impl<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite> Display
    for Ili9488<SPI, CS, DC, RST>
{
    #[inline(always)]
    fn fill_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color) {
        self.fill_rect(x, y, w, h, color);
    }

    #[inline(always)]
    fn draw_pixel(&mut self, x: u16, y: u16, color: Color) {
        self.draw_pixel(x, y, color);
    }
}

