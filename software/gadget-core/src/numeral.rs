//! High-legibility arm's-length 7-segment big numeral engine.
//! Zero heap allocation, zero static SRAM tables, zero UTF-8 dependencies.

use crate::display::Color;
use crate::traits::Display;

pub const DIGIT_WIDTH: u16 = 22;
pub const DIGIT_HEIGHT: u16 = 36;
pub const STROKE_THICKNESS: u16 = 4;
pub const DIGIT_GAP: u16 = 4;
pub const DIGIT_BLANK: u8 = 0xFF;

// Segment bit positions (A through G)
pub const SEG_A: u8 = 1 << 0; // Top horizontal
pub const SEG_B: u8 = 1 << 1; // Top-right vertical
pub const SEG_C: u8 = 1 << 2; // Bottom-right vertical
pub const SEG_D: u8 = 1 << 3; // Bottom horizontal
pub const SEG_E: u8 = 1 << 4; // Bottom-left vertical
pub const SEG_F: u8 = 1 << 5; // Top-left vertical
pub const SEG_G: u8 = 1 << 6; // Center horizontal

/// Returns 7-segment active mask for a decimal digit (0..9).
/// Implemented as a const fn match to generate direct Flash immediate instructions (0 SRAM bytes).
#[inline(always)]
pub const fn segment_mask(digit: u8) -> u8 {
    match digit {
        0 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F,         // 0x3F
        1 => SEG_B | SEG_C,                                         // 0x06
        2 => SEG_A | SEG_B | SEG_D | SEG_E | SEG_G,                 // 0x5B
        3 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_G,                 // 0x4F
        4 => SEG_B | SEG_C | SEG_F | SEG_G,                         // 0x66
        5 => SEG_A | SEG_C | SEG_D | SEG_F | SEG_G,                 // 0x6D
        6 => SEG_A | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G,         // 0x7D
        7 => SEG_A | SEG_B | SEG_C,                                 // 0x07
        8 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G, // 0x7F
        9 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_F | SEG_G,         // 0x6F
        _ => 0x00,
    }
}

/// Decomposes u8 (0..255) into right-aligned digits [hundreds, tens, ones]
/// using DIGIT_BLANK for leading blanks without any heap or UTF-8 formatting.
#[inline]
pub fn u8_to_digits_right_aligned(val: u8) -> [u8; 3] {
    if val >= 100 {
        let d0 = val / 100;
        let rem = val % 100;
        let d1 = rem / 10;
        let d2 = rem % 10;
        [d0, d1, d2]
    } else if val >= 10 {
        let d1 = val / 10;
        let d2 = val % 10;
        [DIGIT_BLANK, d1, d2]
    } else {
        [DIGIT_BLANK, DIGIT_BLANK, val]
    }
}

/// Format u8 (0..255) into stack-allocated digits [u8; 3] with leading blanks.
#[inline]
pub fn format_u8_digits(val: u8) -> [u8; 3] {
    u8_to_digits_right_aligned(val)
}

/// Renders a single 22x36 big digit at (x, y) using 9 non-overlapping rectangular fills.
/// Inactive segments and hollows are explicitly filled with bg to guarantee clean differential overwrite.
pub fn draw_big_digit<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    digit: u8,
    fg: Color,
    bg: Color,
) {
    if digit == DIGIT_BLANK {
        display.fill_rect(x, y, DIGIT_WIDTH, DIGIT_HEIGHT, bg);
        return;
    }

    let mask = segment_mask(digit);
    let color_a = if (mask & SEG_A) != 0 { fg } else { bg };
    let color_b = if (mask & SEG_B) != 0 { fg } else { bg };
    let color_c = if (mask & SEG_C) != 0 { fg } else { bg };
    let color_d = if (mask & SEG_D) != 0 { fg } else { bg };
    let color_e = if (mask & SEG_E) != 0 { fg } else { bg };
    let color_f = if (mask & SEG_F) != 0 { fg } else { bg };
    let color_g = if (mask & SEG_G) != 0 { fg } else { bg };

    // Row slice 1 (Segment A): width 22, height 4
    display.fill_rect(x, y, 22, 4, color_a);

    // Row slice 2 (Segment F, top hollow, Segment B): height 12
    display.fill_rect(x, y + 4, 4, 12, color_f);
    display.fill_rect(x + 4, y + 4, 14, 12, bg);
    display.fill_rect(x + 18, y + 4, 4, 12, color_b);

    // Row slice 3 (Segment G): width 22, height 4
    display.fill_rect(x, y + 16, 22, 4, color_g);

    // Row slice 4 (Segment E, bottom hollow, Segment C): height 12
    display.fill_rect(x, y + 20, 4, 12, color_e);
    display.fill_rect(x + 4, y + 20, 14, 12, bg);
    display.fill_rect(x + 18, y + 20, 4, 12, color_c);

    // Row slice 5 (Segment D): width 22, height 4
    display.fill_rect(x, y + 32, 22, 4, color_d);
}

/// Renders a 3-digit fixed-width numeral field (right-aligned) at (x, y).
/// Leading slots with DIGIT_BLANK are cleanly erased to bg.
/// Returns total width rendered: 74 pixels (3 * 22px + 2 * 4px gap).
pub fn draw_big_numeral_fixed3<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    val: u8,
    fg: Color,
    bg: Color,
) -> u16 {
    let digits = u8_to_digits_right_aligned(val);
    draw_big_digit(display, x, y, digits[0], fg, bg);
    draw_big_digit(display, x + DIGIT_WIDTH + DIGIT_GAP, y, digits[1], fg, bg);
    draw_big_digit(display, x + (DIGIT_WIDTH + DIGIT_GAP) * 2, y, digits[2], fg, bg);
    (DIGIT_WIDTH * 3) + (DIGIT_GAP * 2) // 74px
}

/// Renders a big numeral (0..255) at (x, y) with height 36px.
/// Returns bounding width rendered (74 pixels for stable differential updates).
pub fn draw_big_numeral<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    val: u8,
    fg: Color,
    bg: Color,
) -> u16 {
    draw_big_numeral_fixed3(display, x, y, val, fg, bg)
}

/// Renders a compact big numeral without leading blank slots.
/// Returns rendered width: 22 (1 digit), 48 (2 digits), or 74 (3 digits).
pub fn draw_big_numeral_compact<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    val: u8,
    fg: Color,
    bg: Color,
) -> u16 {
    if val >= 100 {
        let d0 = val / 100;
        let rem = val % 100;
        let d1 = rem / 10;
        let d2 = rem % 10;
        draw_big_digit(display, x, y, d0, fg, bg);
        draw_big_digit(display, x + DIGIT_WIDTH + DIGIT_GAP, y, d1, fg, bg);
        draw_big_digit(display, x + (DIGIT_WIDTH + DIGIT_GAP) * 2, y, d2, fg, bg);
        (DIGIT_WIDTH * 3) + (DIGIT_GAP * 2)
    } else if val >= 10 {
        let d0 = val / 10;
        let d1 = val % 10;
        draw_big_digit(display, x, y, d0, fg, bg);
        draw_big_digit(display, x + DIGIT_WIDTH + DIGIT_GAP, y, d1, fg, bg);
        (DIGIT_WIDTH * 2) + DIGIT_GAP
    } else {
        draw_big_digit(display, x, y, val, fg, bg);
        DIGIT_WIDTH
    }
}

/// Renders a chunky '%' symbol at (x, y). Returns width (18 pixels).
pub fn draw_percent<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    // Clear 18x36 bounding box
    display.fill_rect(x, y, 18, DIGIT_HEIGHT, bg);

    // Upper-left loop (7x8 with 3x4 cutout)
    display.fill_rect(x + 1, y + 3, 7, 8, fg);
    display.fill_rect(x + 3, y + 5, 3, 4, bg);

    // Diagonal slash (stepped 3px rects)
    display.fill_rect(x + 14, y + 3, 3, 5, fg);
    display.fill_rect(x + 12, y + 8, 3, 5, fg);
    display.fill_rect(x + 9, y + 13, 3, 5, fg);
    display.fill_rect(x + 7, y + 18, 3, 5, fg);
    display.fill_rect(x + 4, y + 23, 3, 5, fg);
    display.fill_rect(x + 1, y + 28, 3, 5, fg);

    // Lower-right loop (7x8 with 3x4 cutout)
    display.fill_rect(x + 10, y + 25, 7, 8, fg);
    display.fill_rect(x + 12, y + 27, 3, 4, bg);

    18
}

/// Renders a chunky '%' symbol at (x, y). Alias for draw_percent.
pub fn draw_unit_percent<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    draw_percent(display, x, y, fg, bg)
}

/// Renders a degree symbol ('°') at (x, y) in superscript position.
/// Returns width (8 pixels).
pub fn draw_degree<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    display.fill_rect(x, y, 8, DIGIT_HEIGHT, bg);
    display.fill_rect(x, y + 2, 8, 8, fg);
    display.fill_rect(x + 2, y + 4, 4, 4, bg);
    8
}

/// Renders a Celsius symbol ('C') at (x, y). Returns width (20 pixels).
pub fn draw_celsius<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    display.fill_rect(x, y, 20, DIGIT_HEIGHT, bg);
    // Left vertical spine
    display.fill_rect(x, y, 4, 36, fg);
    // Top horizontal bar
    display.fill_rect(x + 4, y, 16, 4, fg);
    // Bottom horizontal bar
    display.fill_rect(x + 4, y + 32, 16, 4, fg);
    20
}

/// Renders degree + Celsius ('°C') at (x, y). Returns width (31 pixels).
pub fn draw_degree_celsius<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    display.fill_rect(x, y, 31, DIGIT_HEIGHT, bg);
    draw_degree(display, x, y, fg, bg);
    draw_celsius(display, x + 11, y, fg, bg);
    31
}

/// Renders degree + Celsius ('°C') at (x, y). Alias for draw_degree_celsius.
pub fn draw_unit_celsius<D: Display>(
    display: &mut D,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    draw_degree_celsius(display, x, y, fg, bg)
}

/// Renders a single 7-segment digit scaled by pixel multiplier `s`.
/// At s=1: 22×36 px. At s=2: 44×72 px. Zero heap; all math is compile-time scalable.
pub fn draw_big_digit_scaled<D: Display>(
    display: &mut D,
    x: u16, y: u16,
    digit: u8,
    fg: Color, bg: Color,
    s: u16,
) {
    let dw = DIGIT_WIDTH * s;
    let dh = DIGIT_HEIGHT * s;
    if digit == DIGIT_BLANK {
        display.fill_rect(x, y, dw, dh, bg);
        return;
    }
    let mask = segment_mask(digit);
    let ca = if (mask & SEG_A) != 0 { fg } else { bg };
    let cb = if (mask & SEG_B) != 0 { fg } else { bg };
    let cc = if (mask & SEG_C) != 0 { fg } else { bg };
    let cd = if (mask & SEG_D) != 0 { fg } else { bg };
    let ce = if (mask & SEG_E) != 0 { fg } else { bg };
    let cf = if (mask & SEG_F) != 0 { fg } else { bg };
    let cg = if (mask & SEG_G) != 0 { fg } else { bg };

    display.fill_rect(x,        y,        22*s, 4*s,  ca); // A: top horiz
    display.fill_rect(x,        y + 4*s,  4*s,  12*s, cf); // F: top-left vert
    display.fill_rect(x + 4*s,  y + 4*s,  14*s, 12*s, bg); // hollow top
    display.fill_rect(x + 18*s, y + 4*s,  4*s,  12*s, cb); // B: top-right vert
    display.fill_rect(x,        y + 16*s, 22*s, 4*s,  cg); // G: center horiz
    display.fill_rect(x,        y + 20*s, 4*s,  12*s, ce); // E: bot-left vert
    display.fill_rect(x + 4*s,  y + 20*s, 14*s, 12*s, bg); // hollow bot
    display.fill_rect(x + 18*s, y + 20*s, 4*s,  12*s, cc); // C: bot-right vert
    display.fill_rect(x,        y + 32*s, 22*s, 4*s,  cd); // D: bot horiz
}

/// Renders a right-aligned 3-digit field at pixel scale `s`.
/// Leading DIGIT_BLANK slots are erased to `bg` for clean differential redraws.
/// Returns bounding width = (DIGIT_WIDTH * 3 + DIGIT_GAP * 2) * s.
pub fn draw_big_numeral_fixed3_scaled<D: Display>(
    display: &mut D,
    x: u16, y: u16,
    val: u8,
    fg: Color, bg: Color,
    s: u16,
) -> u16 {
    let digits = u8_to_digits_right_aligned(val);
    let dw = DIGIT_WIDTH * s;
    let gap = DIGIT_GAP * s;
    draw_big_digit_scaled(display, x,              y, digits[0], fg, bg, s);
    draw_big_digit_scaled(display, x + dw + gap,   y, digits[1], fg, bg, s);
    draw_big_digit_scaled(display, x + (dw+gap)*2, y, digits[2], fg, bg, s);
    dw * 3 + gap * 2
}
