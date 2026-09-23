use gadget_core::display::{Color, HEIGHT, WIDTH};
use gadget_core::font::{draw_ascii, draw_char, draw_text, get_glyph_5x7};
use gadget_core::numeral::{
    draw_big_digit, draw_big_numeral, draw_big_numeral_compact, draw_big_numeral_fixed3,
    draw_celsius, draw_degree, draw_degree_celsius, draw_percent, draw_unit_celsius,
    draw_unit_percent, format_u8_digits, segment_mask, u8_to_digits_right_aligned, DIGIT_BLANK,
    DIGIT_GAP, DIGIT_HEIGHT, DIGIT_WIDTH,
};
use gadget_core::traits::Display;

use std::alloc::{GlobalAlloc, Layout, System};
use std::cell::Cell;

// Thread-local allocation tracking to verify zero dynamic heap allocations in rendering engine
struct TrackingAlloc;

thread_local! {
    static THREAD_TRACKING: Cell<bool> = const { Cell::new(false) };
    static THREAD_ALLOC_COUNT: Cell<usize> = const { Cell::new(0) };
}

unsafe impl GlobalAlloc for TrackingAlloc {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let _ = THREAD_TRACKING.try_with(|tracking| {
            if tracking.get() {
                let _ = THREAD_ALLOC_COUNT.try_with(|count| {
                    count.set(count.get() + 1);
                });
            }
        });
        System.alloc(layout)
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        System.dealloc(ptr, layout)
    }
}

#[global_allocator]
static GLOBAL: TrackingAlloc = TrackingAlloc;

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct RectCall {
    pub x: u16,
    pub y: u16,
    pub w: u16,
    pub h: u16,
    pub color: Color,
}

pub struct MockDisplay {
    pub pixels: Box<[[Color; WIDTH as usize]; HEIGHT as usize]>,
    pub rect_calls: Vec<RectCall>,
}

impl MockDisplay {
    pub fn new() -> Self {
        Self {
            pixels: vec![[Color::BLACK; WIDTH as usize]; HEIGHT as usize]
                .into_boxed_slice()
                .try_into()
                .unwrap_or_else(|_| panic!("Buffer allocation failed")),
            rect_calls: Vec::with_capacity(512),
        }
    }
}

impl Default for MockDisplay {
    fn default() -> Self {
        Self::new()
    }
}

impl MockDisplay {

    pub fn reset(&mut self) {
        for row in self.pixels.iter_mut() {
            row.fill(Color::BLACK);
        }
        self.rect_calls.clear();
    }

    pub fn pixel_at(&self, x: u16, y: u16) -> Color {
        assert!(x < WIDTH && y < HEIGHT, "Coordinates out of bounds ({}, {})", x, y);
        self.pixels[y as usize][x as usize]
    }

    pub fn bounding_box_of(&self, color: Color) -> Option<(u16, u16, u16, u16)> {
        let mut min_x = u16::MAX;
        let mut max_x = 0;
        let mut min_y = u16::MAX;
        let mut max_y = 0;
        let mut found = false;

        for y in 0..HEIGHT {
            for x in 0..WIDTH {
                if self.pixels[y as usize][x as usize] == color {
                    found = true;
                    min_x = min_x.min(x);
                    max_x = max_x.max(x);
                    min_y = min_y.min(y);
                    max_y = max_y.max(y);
                }
            }
        }

        if found {
            Some((min_x, min_y, max_x, max_y))
        } else {
            None
        }
    }

    pub fn count_colored_pixels(&self, color: Color) -> usize {
        let mut count = 0;
        for y in 0..HEIGHT {
            for x in 0..WIDTH {
                if self.pixels[y as usize][x as usize] == color {
                    count += 1;
                }
            }
        }
        count
    }
}

impl Display for MockDisplay {
    fn fill_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color) {
        if w == 0 || h == 0 || x >= WIDTH || y >= HEIGHT {
            return;
        }
        self.rect_calls.push(RectCall { x, y, w, h, color });
        let x_end = (x + w).min(WIDTH);
        let y_end = (y + h).min(HEIGHT);
        for py in y..y_end {
            for px in x..x_end {
                self.pixels[py as usize][px as usize] = color;
            }
        }
    }

    fn draw_pixel(&mut self, x: u16, y: u16, color: Color) {
        if x < WIDTH && y < HEIGHT {
            self.fill_rect(x, y, 1, 1, color);
        }
    }
}

// Zero-allocation mock display for allocator verification test
struct ZeroAllocMockDisplay;

impl Display for ZeroAllocMockDisplay {
    #[inline(always)]
    fn fill_rect(&mut self, _x: u16, _y: u16, _w: u16, _h: u16, _color: Color) {}

    #[inline(always)]
    fn draw_pixel(&mut self, _x: u16, _y: u16, _color: Color) {}
}

// =========================================================================
// Suite 1: Big Digit Geometry & Height Assertion (R2 Compliance)
// =========================================================================

#[test]
fn test_all_digits_height_between_28_and_36px() {
    let mut display = MockDisplay::new();
    let fg = Color::WHITE;
    let bg = Color::BLACK;

    for digit in 0..=9 {
        display.reset();
        draw_big_digit(&mut display, 100, 100, digit, fg, bg);

        let (min_x, min_y, max_x, max_y) = display
            .bounding_box_of(fg)
            .unwrap_or_else(|| panic!("Digit {} drew zero foreground pixels!", digit));

        let height = max_y - min_y + 1;
        let width = max_x - min_x + 1;

        assert!(
            height >= 28,
            "Digit {} height {}px is less than 28px minimum required for arm's length readability!",
            digit,
            height
        );
        assert!(
            height <= 36,
            "Digit {} height {}px exceeds 36px maximum layout ceiling!",
            digit,
            height
        );
        assert!(
            (4..=24).contains(&width),
            "Digit {} width {}px is out of expected proportions [4..24]px!",
            digit,
            width
        );

        // Assert strictly inside bounding box [100..100+22, 100..100+36]
        assert!(
            min_x >= 100 && max_x < 100 + DIGIT_WIDTH,
            "Digit {} x overflow: {}..{}",
            digit,
            min_x,
            max_x
        );
        assert!(
            min_y >= 100 && max_y < 100 + DIGIT_HEIGHT,
            "Digit {} y overflow: {}..{}",
            digit,
            min_y,
            max_y
        );
    }
}

#[test]
fn test_all_digits_visually_unique() {
    let mut display = MockDisplay::new();
    let fg = Color::WHITE;
    let bg = Color::BLACK;

    let mut patterns = Vec::new();
    for digit in 0..=9 {
        display.reset();
        draw_big_digit(&mut display, 50, 50, digit, fg, bg);

        let mut pixel_set = Vec::new();
        for y in 50..50 + DIGIT_HEIGHT {
            for x in 50..50 + DIGIT_WIDTH {
                if display.pixel_at(x, y) == fg {
                    pixel_set.push((x - 50, y - 50));
                }
            }
        }
        for (other_digit, other_pattern) in patterns.iter().enumerate() {
            assert_ne!(
                &pixel_set, other_pattern,
                "Digit {} and Digit {} produced identical pixel output!",
                digit, other_digit
            );
        }
        patterns.push(pixel_set);
    }
}

// =========================================================================
// Suite 2: Integer Formatting & Value Coverage (0..=100 and Edge Cases)
// =========================================================================

#[test]
fn test_numeral_values_0_to_100_coverage() {
    let mut display = MockDisplay::new();
    let fg = Color::CYAN;
    let bg = Color::DARK_BG;

    for val in 0..=100 {
        display.reset();
        let rendered_width = draw_big_numeral(&mut display, 10, 10, val, fg, bg);

        assert!(
            rendered_width > 0 && rendered_width <= 80,
            "Value {} returned invalid width {}",
            val,
            rendered_width
        );

        let (min_x, min_y, max_x, max_y) = display
            .bounding_box_of(fg)
            .unwrap_or_else(|| panic!("Value {} rendered zero foreground pixels!", val));

        let height = max_y - min_y + 1;
        assert!(
            (28..=36).contains(&height),
            "Value {} height {}px is outside 28..36px!",
            val,
            height
        );

        // Ensure no stray pixels outside [10, 10+80) x [10, 10+36)
        assert!(min_x >= 10 && max_x < 10 + 80);
        assert!(min_y >= 10 && max_y < 10 + 36);
    }
}

#[test]
fn test_numeral_edge_cases() {
    let mut display = MockDisplay::new();
    let fg = Color::YELLOW;
    let bg = Color::BLACK;

    let edge_cases = [0u8, 1, 9, 10, 99, 100, 105, 255];
    for &val in &edge_cases {
        display.reset();
        let w = draw_big_numeral(&mut display, 20, 20, val, fg, bg);

        let (min_x, min_y, max_x, max_y) = display
            .bounding_box_of(fg)
            .unwrap_or_else(|| panic!("Edge case {} failed to render pixels", val));

        assert!(max_y - min_y + 1 >= 28);
        assert!(max_x - min_x < w);
    }
}

#[test]
fn test_compact_numeral_widths() {
    let mut display = MockDisplay::new();
    let fg = Color::GREEN;
    let bg = Color::BLACK;

    // 1-digit
    display.reset();
    let w1 = draw_big_numeral_compact(&mut display, 0, 0, 7, fg, bg);
    assert_eq!(w1, DIGIT_WIDTH);

    // 2-digit
    display.reset();
    let w2 = draw_big_numeral_compact(&mut display, 0, 0, 42, fg, bg);
    assert_eq!(w2, (DIGIT_WIDTH * 2) + DIGIT_GAP);

    // 3-digit
    display.reset();
    let w3 = draw_big_numeral_compact(&mut display, 0, 0, 100, fg, bg);
    assert_eq!(w3, (DIGIT_WIDTH * 3) + (DIGIT_GAP * 2));
}

#[test]
fn test_u8_digit_formatting() {
    assert_eq!(format_u8_digits(0), [DIGIT_BLANK, DIGIT_BLANK, 0]);
    assert_eq!(format_u8_digits(5), [DIGIT_BLANK, DIGIT_BLANK, 5]);
    assert_eq!(format_u8_digits(10), [DIGIT_BLANK, 1, 0]);
    assert_eq!(format_u8_digits(99), [DIGIT_BLANK, 9, 9]);
    assert_eq!(format_u8_digits(100), [1, 0, 0]);
    assert_eq!(format_u8_digits(255), [2, 5, 5]);

    assert_eq!(u8_to_digits_right_aligned(42), [DIGIT_BLANK, 4, 2]);
    assert_eq!(segment_mask(0), 0x3F);
    assert_eq!(segment_mask(8), 0x7F);
    assert_eq!(segment_mask(1), 0x06);
}

// =========================================================================
// Suite 3: Unit Symbols ('%', '°', 'C', '°C')
// =========================================================================

#[test]
fn test_unit_symbols_rendering() {
    let mut display = MockDisplay::new();
    let fg = Color::WHITE;
    let bg = Color::BLACK;

    // 1. Percent Symbol (%)
    display.reset();
    let w_pct = draw_percent(&mut display, 50, 50, fg, bg);
    assert!((14..=22).contains(&w_pct), "Percent width {} out of spec", w_pct);
    let (min_x, min_y, max_x, max_y) = display
        .bounding_box_of(fg)
        .expect("Percent rendered no pixels");
    assert!(max_y - min_y + 1 >= 24, "Percent height too small");
    assert!(min_x >= 50 && max_x < 50 + w_pct);

    // 2. Degree Symbol (°)
    display.reset();
    let w_deg = draw_degree(&mut display, 50, 50, fg, bg);
    assert!((6..=12).contains(&w_deg), "Degree width {} out of spec", w_deg);
    let (_, min_y, _, max_y) = display
        .bounding_box_of(fg)
        .expect("Degree rendered no pixels");
    assert!(max_y - min_y < 12, "Degree height should be compact superscript");

    // 3. Celsius Symbol (C)
    display.reset();
    let w_c = draw_celsius(&mut display, 50, 50, fg, bg);
    assert!((14..=24).contains(&w_c), "Celsius width {} out of spec", w_c);
    let (_, min_y, _, max_y) = display
        .bounding_box_of(fg)
        .expect("Celsius rendered no pixels");
    assert!(max_y - min_y + 1 >= 28, "Celsius height must be >= 28px");

    // 4. Combined Degree + Celsius (°C)
    display.reset();
    let w_dc = draw_degree_celsius(&mut display, 50, 50, fg, bg);
    assert_eq!(w_dc, 31, "Combined °C width should be 31px");
    let (dc_min_x, dc_min_y, dc_max_x, dc_max_y) = display
        .bounding_box_of(fg)
        .expect("Degree+Celsius rendered no pixels");
    assert!(dc_max_y - dc_min_y + 1 >= 28);
    assert!(dc_min_x >= 50 && dc_max_x < 50 + w_dc);

    // 5. Test alias functions
    assert_eq!(draw_unit_percent(&mut display, 0, 0, fg, bg), w_pct);
    assert_eq!(draw_unit_celsius(&mut display, 0, 0, fg, bg), w_dc);
}

// =========================================================================
// Suite 4: Differential Overwrite & Erasure Verification
// =========================================================================

#[test]
fn test_clean_differential_overwrite_no_ghost_pixels() {
    let mut display = MockDisplay::new();
    let fg = Color::WHITE;
    let bg = Color::BLACK;

    // Render '8' (all 7 segments lit)
    draw_big_digit(&mut display, 40, 40, 8, fg, bg);
    let count_8 = display.count_colored_pixels(fg);

    // Overwrite with '1' (only 2 segments lit) at the exact same location
    draw_big_digit(&mut display, 40, 40, 1, fg, bg);
    let count_1 = display.count_colored_pixels(fg);

    // Verify inactive segments of '8' were cleared back to bg
    assert!(
        count_1 < count_8,
        "Inactive segments were not cleared! Pixel count did not drop from 8 to 1"
    );

    // Re-render '1' on a clean background to compare exact pixel count
    let mut clean_display = MockDisplay::new();
    draw_big_digit(&mut clean_display, 40, 40, 1, fg, bg);
    assert_eq!(
        count_1,
        clean_display.count_colored_pixels(fg),
        "Overwritten digit '1' left residual ghost pixels from previous digit '8'!"
    );
}

#[test]
fn test_blank_slot_clears_bounding_box() {
    let mut display = MockDisplay::new();
    let fg = Color::WHITE;
    let bg = Color::BLACK;

    // Draw digit 8
    draw_big_digit(&mut display, 20, 20, 8, fg, bg);
    assert!(display.count_colored_pixels(fg) > 0);

    // Overwrite with DIGIT_BLANK
    draw_big_digit(&mut display, 20, 20, DIGIT_BLANK, fg, bg);
    assert_eq!(
        display.count_colored_pixels(fg),
        0,
        "DIGIT_BLANK did not clear all foreground pixels!"
    );
}

// =========================================================================
// Suite 5: Zero-Heap Allocation Assertion via Global Tracking Allocator
// =========================================================================

#[test]
fn test_strictly_zero_heap_allocations() {
    let mut display = ZeroAllocMockDisplay;

    THREAD_ALLOC_COUNT.with(|c| c.set(0));
    THREAD_TRACKING.with(|t| t.set(true));

    // Execute complete numeral and symbol rendering workload
    for val in 0..=100 {
        draw_big_numeral(&mut display, 10, 10, val, Color::WHITE, Color::BLACK);
    }
    draw_big_numeral(&mut display, 10, 10, 255, Color::WHITE, Color::BLACK);
    draw_big_numeral_compact(&mut display, 10, 10, 42, Color::WHITE, Color::BLACK);

    for digit in 0..10 {
        draw_big_digit(&mut display, 10, 10, digit, Color::WHITE, Color::BLACK);
    }
    draw_big_digit(&mut display, 10, 10, DIGIT_BLANK, Color::WHITE, Color::BLACK);

    draw_percent(&mut display, 10, 10, Color::WHITE, Color::BLACK);
    draw_celsius(&mut display, 10, 10, Color::WHITE, Color::BLACK);
    draw_degree(&mut display, 10, 10, Color::WHITE, Color::BLACK);
    draw_degree_celsius(&mut display, 10, 10, Color::WHITE, Color::BLACK);

    THREAD_TRACKING.with(|t| t.set(false));

    let count = THREAD_ALLOC_COUNT.with(|c| c.get());
    assert_eq!(
        count, 0,
        "VIOLATION: Numeral rendering performed {} dynamic heap allocations!",
        count
    );
}

// =========================================================================
// Suite 6: SPI Window / Draw Call Budget
// =========================================================================

#[test]
fn test_draw_call_efficiency_budget() {
    let mut display = MockDisplay::new();
    draw_big_digit(&mut display, 50, 50, 8, Color::WHITE, Color::BLACK);

    // Digit 8 has 7 segments + 2 hollows = 9 non-overlapping fill_rect calls
    assert!(
        display.rect_calls.len() <= 9,
        "Digit 8 made {} fill_rect calls, exceeding SPI budget of 9!",
        display.rect_calls.len()
    );
}

// =========================================================================
// Suite 7: Zero-SRAM Font Flash Table Verification
// =========================================================================

#[test]
fn test_font_glyph_ascii_coverage() {
    let mut display = MockDisplay::new();

    // Verify all printable ASCII characters 32..=126 can be rendered without panic
    for c in 32u8..=126u8 {
        let glyph = get_glyph_5x7(c);
        // Non-space characters should have at least one pixel lit
        if c != b' ' {
            let has_pixel = glyph.iter().any(|&col| col != 0);
            assert!(has_pixel, "Character '{}' (ASCII {}) has empty glyph!", c as char, c);
        }
    }

    // Verify draw_ascii and draw_text work with MockDisplay
    display.reset();
    draw_ascii(&mut display, 0, 0, b"CPU: 45%", Color::CYAN, Color::BLACK, 1);
    assert!(display.count_colored_pixels(Color::CYAN) > 0);

    display.reset();
    draw_text(&mut display, 0, 0, "GPU TEMP", Color::GREEN, Color::BLACK, 2);
    assert!(display.count_colored_pixels(Color::GREEN) > 0);

    display.reset();
    draw_char(&mut display, 0, 0, 'A', Color::WHITE, Color::BLACK, 1);
    assert!(display.count_colored_pixels(Color::WHITE) > 0);

    display.reset();
    draw_char(&mut display, 0, 0, '°', Color::YELLOW, Color::BLACK, 1);
    assert!(display.count_colored_pixels(Color::YELLOW) > 0);

    display.reset();
    let w_fix = draw_big_numeral_fixed3(&mut display, 0, 0, 50, Color::WHITE, Color::BLACK);
    assert_eq!(w_fix, 74);
}

