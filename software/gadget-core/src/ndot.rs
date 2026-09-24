//! NDot 5×7 Dot-Matrix Font and Circular Dot Rasterizer.
//! Implements Nothing OS design language:
//! - Pure Flash const lookup (0 bytes SRAM).
//! - Smooth geometric circular dots.
//! - Simultaneous ON/OFF cell rasterization (zero flicker).

use crate::display::Color;
use crate::traits::Display;

/// Returns the 7-row bitmask for a 5×7 NDot glyph.
/// Bit 4 is col 0, bit 0 is col 4.
#[inline(always)]
pub const fn get_ndot_glyph(c: u8) -> [u8; 7] {
    match c {
        b'0' => [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
        b'1' => [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
        b'2' => [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
        b'3' => [0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110],
        b'4' => [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
        b'5' => [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
        b'6' => [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
        b'7' => [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
        b'8' => [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
        b'9' => [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
        b'C' | b'c' => [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
        b'P' | b'p' => [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
        b'U' | b'u' => [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
        b'G' | b'g' => [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111],
        b'L' | b'l' => [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
        b'S' | b's' => [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
        b'E' | b'e' => [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
        b'D' | b'd' => [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
        b'A' | b'a' => [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
        b'M' | b'm' => [0b10001, 0b11011, 0b10101, 0b10001, 0b10001, 0b10001, 0b10001],
        b'O' | b'o' => [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
        b'R' | b'r' => [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
        b'Y' | b'y' => [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
        b'T' | b't' => [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
        b'H' | b'h' => [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
        b'N' | b'n' => [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
        b'I' | b'i' => [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
        b'%' => [0b11001, 0b11010, 0b00100, 0b01000, 0b01011, 0b10011, 0b00000],
        b' ' => [0; 7],
        // Degree symbol '°' (ASCII 176 / 223 / '*')
        b'*' | 176 | 223 => [0b01100, 0b10010, 0b10010, 0b01100, 0b00000, 0b00000, 0b00000],
        _ => [0; 7],
    }
}

/// Draws a single 5×7 NDot glyph at cell size `cell`.
/// Automatically renders circular dots for cells >= 7, square dots for smaller cells.
pub fn draw_ndot_char<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    c: u8,
    cell: u16,
    fg: Color,
    bg: Color,
) {
    let glyph = get_ndot_glyph(c);

    for row in 0..7 {
        let row_bits = glyph[row as usize];
        let cy = y + row * cell;

        for col in 0..5 {
            let is_on = ((row_bits >> (4 - col)) & 1) != 0;
            let cx = x + col * cell;

            if cell == 14 {
                // Giant 14×14 cell with smooth 12px circular dot
                display.fill_rect(cx, cy, 14, 14, bg);
                if is_on {
                    display.fill_rect(cx + 4, cy + 1, 6, 1, fg);
                    display.fill_rect(cx + 2, cy + 2, 10, 1, fg);
                    display.fill_rect(cx + 1, cy + 3, 12, 8, fg);
                    display.fill_rect(cx + 2, cy + 11, 10, 1, fg);
                    display.fill_rect(cx + 4, cy + 12, 6, 1, fg);
                }
            } else if cell == 11 {
                // Giant 11×11 cell with smooth 9px circular dot
                display.fill_rect(cx, cy, 11, 11, bg);
                if is_on {
                    display.fill_rect(cx + 4, cy + 1, 3, 1, fg);
                    display.fill_rect(cx + 2, cy + 2, 7, 2, fg);
                    display.fill_rect(cx + 1, cy + 4, 9, 3, fg);
                    display.fill_rect(cx + 2, cy + 7, 7, 2, fg);
                    display.fill_rect(cx + 4, cy + 9, 3, 1, fg);
                }
            } else if cell == 9 {
                // Big 9×9 cell with smooth 7px circular dot
                display.fill_rect(cx, cy, 9, 9, bg);
                if is_on {
                    display.fill_rect(cx + 3, cy + 1, 3, 1, fg);
                    display.fill_rect(cx + 1, cy + 2, 7, 5, fg);
                    display.fill_rect(cx + 3, cy + 7, 3, 1, fg);
                }
            } else if cell == 7 {
                // Medium 7×7 cell with smooth 5px circular dot
                display.fill_rect(cx, cy, 7, 7, bg);
                if is_on {
                    display.fill_rect(cx + 2, cy + 1, 3, 1, fg);
                    display.fill_rect(cx + 1, cy + 2, 5, 3, fg);
                    display.fill_rect(cx + 2, cy + 5, 3, 1, fg);
                }
            } else if cell == 4 {
                // 4×4 cell with 4px circular dot
                display.fill_rect(cx, cy, 4, 4, bg);
                if is_on {
                    display.fill_rect(cx + 1, cy, 2, 1, fg);
                    display.fill_rect(cx, cy + 1, 4, 2, fg);
                    display.fill_rect(cx + 1, cy + 3, 2, 1, fg);
                }
            } else if cell == 3 {
                // Small 3×3 cell with 2×2 dot
                display.fill_rect(cx, cy, 3, 3, bg);
                if is_on {
                    display.fill_rect(cx, cy, 2, 2, fg);
                }
            } else {
                // Generic cell
                let col_color = if is_on { fg } else { bg };
                display.fill_rect(cx, cy, cell, cell, col_color);
            }
        }
    }
}

/// Draws an ASCII string in NDot dot-matrix format.
/// Returns the total width rendered in pixels.
pub fn draw_ndot_str<D: Display>(
    display: &mut D,
    mut x: u16,
    y: u16,
    text: &[u8],
    cell: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    let char_w = 5 * cell;
    let gap_x = cell;
    let mut total_w = 0;

    for (i, &b) in text.iter().enumerate() {
        if i > 0 {
            display.fill_rect(x, y, gap_x, 7 * cell, bg);
            x += gap_x;
            total_w += gap_x;
        }
        draw_ndot_char(display, x, y, b, cell, fg, bg);
        x += char_w;
        total_w += char_w;
    }
    total_w
}

/// Draws a smooth circular dot of diameter 5px.
pub fn draw_dot_circle_5px<D: Display>(display: &mut D, x: u16, y: u16, color: Color) {
    display.fill_rect(x + 1, y, 3, 1, color);
    display.fill_rect(x, y + 1, 5, 3, color);
    display.fill_rect(x + 1, y + 4, 3, 1, color);
}

/// Draws a smooth circular dot of diameter 6px.
pub fn draw_dot_circle_6px<D: Display>(display: &mut D, x: u16, y: u16, color: Color) {
    display.fill_rect(x + 1, y, 4, 1, color);
    display.fill_rect(x, y + 1, 6, 4, color);
    display.fill_rect(x + 1, y + 5, 4, 1, color);
}

/// Draws a smooth circular dot of diameter 7px.
pub fn draw_dot_circle_7px<D: Display>(display: &mut D, x: u16, y: u16, color: Color) {
    display.fill_rect(x + 2, y, 3, 1, color);
    display.fill_rect(x + 1, y + 1, 5, 1, color);
    display.fill_rect(x, y + 2, 7, 3, color);
    display.fill_rect(x + 1, y + 5, 5, 1, color);
    display.fill_rect(x + 2, y + 6, 3, 1, color);
}
