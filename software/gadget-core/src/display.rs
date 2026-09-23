//! ILI9488 SPI Display Driver (embedded-hal agnostic)
//! Supports 480x320 landscape orientation with 18-bit color mode (3 bytes per pixel).

use crate::traits::{DelayMs, PinWrite, SpiWrite};

pub const WIDTH: u16 = 480;
pub const HEIGHT: u16 = 320;

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct Color {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}

impl Color {
    pub const fn new(r: u8, g: u8, b: u8) -> Self {
        Self { r, g, b }
    }

    pub const BLACK: Color = Color::new(0, 0, 0);
    pub const WHITE: Color = Color::new(255, 255, 255);
    pub const DARK_BG: Color = Color::new(18, 22, 34);       // Deep navy background
    pub const PANEL_BG: Color = Color::new(28, 34, 52);      // Card background
    pub const BORDER: Color = Color::new(50, 62, 90);        // Card border
    pub const TEXT_MUTED: Color = Color::new(130, 145, 175);
    pub const CYAN: Color = Color::new(0, 220, 225);
    pub const GREEN: Color = Color::new(10, 210, 110);
    pub const YELLOW: Color = Color::new(255, 215, 40);
    pub const ORANGE: Color = Color::new(255, 150, 30);
    pub const RED: Color = Color::new(255, 55, 60);
    pub const PINK: Color = Color::new(255, 120, 160);
    pub const PURPLE: Color = Color::new(170, 100, 250);
}

pub struct Ili9488<SPI, CS, DC, RST> {
    spi: SPI,
    cs: CS,
    dc: DC,
    rst: RST,
}

impl<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite> Ili9488<SPI, CS, DC, RST> {
    pub fn new(spi: SPI, cs: CS, dc: DC, rst: RST) -> Self {
        Self { spi, cs, dc, rst }
    }

    #[inline]
    fn write_cmd(&mut self, cmd: u8) {
        self.dc.set_low();
        self.spi.write_byte(cmd);
    }

    #[inline]
    fn write_data(&mut self, data: u8) {
        self.dc.set_high();
        self.spi.write_byte(data);
    }

    pub fn init<D: DelayMs>(&mut self, delay: &mut D) {
        // Hardware Reset sequence
        self.cs.set_high();
        self.rst.set_high();
        delay.delay_ms(10);
        self.rst.set_low();
        delay.delay_ms(20);
        self.rst.set_high();
        delay.delay_ms(120);

        self.cs.set_low();

        // PGAMCTRL (Positive Gamma Control)
        self.write_cmd(0xE0);
        self.write_data(0x00);
        self.write_data(0x07);
        self.write_data(0x10);
        self.write_data(0x09);
        self.write_data(0x17);
        self.write_data(0x0B);
        self.write_data(0x41);
        self.write_data(0x89);
        self.write_data(0x4B);
        self.write_data(0x0A);
        self.write_data(0x0C);
        self.write_data(0x0E);
        self.write_data(0x18);
        self.write_data(0x1B);
        self.write_data(0x0F);

        // NGAMCTRL (Negative Gamma Control)
        self.write_cmd(0xE1);
        self.write_data(0x00);
        self.write_data(0x17);
        self.write_data(0x1A);
        self.write_data(0x04);
        self.write_data(0x0E);
        self.write_data(0x06);
        self.write_data(0x2F);
        self.write_data(0x45);
        self.write_data(0x43);
        self.write_data(0x02);
        self.write_data(0x0A);
        self.write_data(0x09);
        self.write_data(0x32);
        self.write_data(0x36);
        self.write_data(0x0F);

        // Power Control 1
        self.write_cmd(0xC0);
        self.write_data(0x11);
        self.write_data(0x09);

        // Power Control 2
        self.write_cmd(0xC1);
        self.write_data(0x41);

        // VCOM Control
        self.write_cmd(0xC5);
        self.write_data(0x00);
        self.write_data(0x0A);
        self.write_data(0x80);

        // Memory Access Control (Landscape 480x320 for ILI9488)
        // 0xA8 = MV (row/col exchange) | MY (row address order) | BGR (0x20 | 0x80 | 0x08)
        // This is the standard un-mirrored landscape orientation from the ILI9488 driver spec.
        self.write_cmd(0x36);
        self.write_data(0xA8);

        // Interface Pixel Format: 18-bit (3 bytes/pixel)
        self.write_cmd(0x3A);
        self.write_data(0x66);

        // Frame Rate Control
        self.write_cmd(0xB1);
        self.write_data(0xB0);
        self.write_data(0x11);

        // Display Inversion Control
        self.write_cmd(0xB4);
        self.write_data(0x02);

        // Display Function Control
        self.write_cmd(0xB6);
        self.write_data(0x02);
        self.write_data(0x22);

        // Entry Mode Set
        self.write_cmd(0xB7);
        self.write_data(0xC6);

        // Pump Ratio Control
        self.write_cmd(0xF7);
        self.write_data(0xA9);
        self.write_data(0x51);
        self.write_data(0x2C);
        self.write_data(0x82);

        // Sleep OUT
        self.write_cmd(0x11);
        self.cs.set_high();

        delay.delay_ms(120);

        // Display ON
        self.cs.set_low();
        self.write_cmd(0x29);
        self.cs.set_high();
    }

    pub fn set_window(&mut self, x0: u16, y0: u16, x1: u16, y1: u16) {
        let x0 = x0.min(WIDTH - 1);
        let x1 = x1.min(WIDTH - 1);
        let y0 = y0.min(HEIGHT - 1);
        let y1 = y1.min(HEIGHT - 1);

        // Column Address Set
        self.write_cmd(0x2A);
        self.write_data((x0 >> 8) as u8);
        self.write_data((x0 & 0xFF) as u8);
        self.write_data((x1 >> 8) as u8);
        self.write_data((x1 & 0xFF) as u8);

        // Page Address Set
        self.write_cmd(0x2B);
        self.write_data((y0 >> 8) as u8);
        self.write_data((y0 & 0xFF) as u8);
        self.write_data((y1 >> 8) as u8);
        self.write_data((y1 & 0xFF) as u8);

        // Memory Write
        self.write_cmd(0x2C);
    }

    pub fn fill_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color) {
        if w == 0 || h == 0 || x >= WIDTH || y >= HEIGHT {
            return;
        }
        let x1 = (x + w - 1).min(WIDTH - 1);
        let y1 = (y + h - 1).min(HEIGHT - 1);
        let pixel_count = ((x1 - x + 1) as u32) * ((y1 - y + 1) as u32);

        self.cs.set_low();
        self.set_window(x, y, x1, y1);

        self.dc.set_high();
        let r = color.r;
        let g = color.g;
        let b = color.b;
        for _ in 0..pixel_count {
            self.spi.write_byte(r);
            self.spi.write_byte(g);
            self.spi.write_byte(b);
        }
        self.cs.set_high();
    }

    pub fn draw_pixel(&mut self, x: u16, y: u16, color: Color) {
        if x >= WIDTH || y >= HEIGHT {
            return;
        }
        self.cs.set_low();
        self.set_window(x, y, x, y);
        self.dc.set_high();
        self.spi.write_byte(color.r);
        self.spi.write_byte(color.g);
        self.spi.write_byte(color.b);
        self.cs.set_high();
    }

    pub fn draw_hline(&mut self, x: u16, y: u16, len: u16, color: Color) {
        self.fill_rect(x, y, len, 1, color);
    }

    pub fn draw_vline(&mut self, x: u16, y: u16, len: u16, color: Color) {
        self.fill_rect(x, y, 1, len, color);
    }

    pub fn draw_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color) {
        self.draw_hline(x, y, w, color);
        self.draw_hline(x, y + h - 1, w, color);
        self.draw_vline(x, y, h, color);
        self.draw_vline(x + w - 1, y, h, color);
    }

    pub fn clear(&mut self, color: Color) {
        self.fill_rect(0, 0, WIDTH, HEIGHT, color);
    }
}
