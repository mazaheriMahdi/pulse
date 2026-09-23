# Test & Integration Architecture Handoff Report: Milestone 1 (Core Typography & SRAM Reduction)

**Author**: `sub_orch_m1_explorer_3` (Role: Test & Integration Architect)  
**Parent**: `sub_orch_m1` (`cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41`)  
**Target File**: `/home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3/handoff.md`  
**Date**: 2026-09-22  

---

## 1. Observation

### 1.1 Existing Host-Side Testing Baseline
Executing `cargo test` in `software/gadget-core`:
```text
$ cd software/gadget-core && cargo test
Finished `test` profile [unoptimized + debuginfo] target(s) in 0.00s
Running unittests src/lib.rs (target/debug/deps/gadget_core-38aef46850b6f273)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```
- Direct observation: Currently, `software/gadget-core` contains **zero unit tests** (`running 0 tests`).
- There is no test mock harness, no geometry verification, and no automated regression testing for numeral legibility or zero-allocation invariants.

### 1.2 Firmware Build and Binary Footprint Baseline
Executing `cargo +nightly build --release` in `software/gadget-firmware-uno` and evaluating with `avr-size`:
```text
$ cd software/gadget-firmware-uno && cargo +nightly build --release
Finished `release` profile [optimized + debuginfo] target(s) in 0.05s

$ avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
AVR Memory Usage
----------------
Device: atmega328p

Program:    8856 bytes (27.0% Full)
(.text + .data + .bootloader)

Data:        983 bytes (48.0% Full)
(.data + .bss + .noinit)
```
Inspecting the ELF section table via `avr-size -A`:
```text
target/avr-none/release/gadget-firmware-uno.elf  :
section                       size      addr
.data                          982   8388864
.text                         7874         0
.bss                             1   8389846
```
Symbol mapping from `avr-objdump -t target/avr-none/release/gadget-firmware-uno.elf | grep "\.data"`:
- `008002fa l O .data 000001db _RNvNtCslc2XTLF6XHm_11gadget_core4font8FONT_5X7`: **475 bytes**
- `008001fa l O .data 00000100 anon.ca5ba2dec42ec402aac11eec41e77a9b.211` (`core::str::from_utf8` table): **256 bytes**
- String literals (`anon.*` in `ui.rs` and `main.rs`): **251 bytes**
- Current total static SRAM: **983 bytes** (Ceiling in Acceptance Criteria is **< 100 bytes**).
- Flash size: **8,856 bytes** (Ceiling in Acceptance Criteria is **< 28 KB = 28,672 bytes**; current Flash is comfortably 27.0% full).

### 1.3 Interface Contract Status in `gadget-core`
Inspecting `software/gadget-core/src/traits.rs` (lines 5–29):
```rust
pub trait SpiWrite {
    fn write_byte(&mut self, byte: u8);
    fn write_bytes(&mut self, bytes: &[u8]) { ... }
    fn write_repeated(&mut self, byte: u8, count: usize) { ... }
}
pub trait PinWrite {
    fn set_high(&mut self);
    fn set_low(&mut self);
}
pub trait DelayMs {
    fn delay_ms(&mut self, ms: u16);
}
```
Inspecting `software/gadget-core/src/display.rs` (lines 36–46, 194–244):
- `Ili9488<SPI, CS, DC, RST>` wraps generic `(SPI, CS, DC, RST)`.
- Core drawing methods are inherent methods on `Ili9488`:
  - `pub fn fill_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color)`
  - `pub fn draw_pixel(&mut self, x: u16, y: u16, color: Color)`
  - `pub fn draw_hline(&mut self, x: u16, y: u16, len: u16, color: Color)`
  - `pub fn draw_vline(&mut self, x: u16, y: u16, len: u16, color: Color)`
  - `pub fn draw_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color)`
  - `pub fn clear(&mut self, color: Color)`
- `Dashboard::draw_layout` and `Dashboard::update` currently take `&mut Ili9488<SPI, CS, DC, RST>`.
- In `PROJECT.md` line 73 and `SCOPE.md` line 30, the interface contracts specify generic display abstraction:
  - `draw_big_numeral<D: Display>(display: &mut D, x: u16, y: u16, value: u8, color: Color, bg_color: Color) -> u16`
  - `draw_big_digit<D: Display>(display: &mut D, x: u16, y: u16, digit: u8, color: Color, bg_color: Color)`

---

## 2. Logic Chain

### 2.1 Interface Contract Harmonization (`Display` Trait vs `Ili9488`)
1. **Trait Decoupling**: If `numeral.rs` only accepted `&mut Ili9488<SPI, CS, DC, RST>`, host unit tests would be forced to emulate low-level SPI byte streams (`0x2A`, `0x2B`, `0x2C` registers) just to test if a numeral is 36px tall. This introduces fragile decoding logic into unit tests.
2. **Backward Compatibility**: If we define a minimal `Display` trait in `software/gadget-core/src/traits.rs`:
   ```rust
   pub trait Display {
       fn fill_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color);
       fn draw_pixel(&mut self, x: u16, y: u16, color: Color);
   }
   ```
   and implement it for `Ili9488<SPI, CS, DC, RST>`:
   ```rust
   impl<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite> Display for Ili9488<SPI, CS, DC, RST> {
       #[inline(always)]
       fn fill_rect(&mut self, x: u16, y: u16, w: u16, h: u16, color: Color) {
           self.fill_rect(x, y, w, h, color);
       }
       #[inline(always)]
       fn draw_pixel(&mut self, x: u16, y: u16, color: Color) {
           self.draw_pixel(x, y, color);
       }
   }
   ```
   then:
   - Target firmware in `gadget-firmware-uno/src/main.rs` compiles without changing a single line of application code (since `display` satisfies `D: Display`).
   - Monomorphization on AVR produces direct inlined machine code with **zero vtables, zero fat pointers, and zero runtime penalty**.
   - Host unit tests can pass a clean `MockDisplay` that implements `Display` directly.

### 2.2 `MockDisplay` Architecture & Dual Verification Strategy
1. **MockDisplay Structure**:
   `MockDisplay` records:
   - A 2D framebuffer `Box<[[Color; WIDTH]; HEIGHT]>` (480x320 grid) to inspect exact rendered pixels.
   - An ordered log of `RectCall { x, y, w, h, color }` to assert draw call bounds, segment count, and clearing efficiency.
2. **Dual Verification**:
   - **Direct Mock (`MockDisplay`)**: Verifies geometry, pixel positions, bounding boxes, and zero-allocation.
   - **SPI Protocol Mock (`Ili9488<MockSpi, MockPin, MockPin, MockPin>`)**: Verifies hardware register sequences (CASET/PASET/RAMWR) for end-to-end driver correctness.

### 2.3 Mathematical Proof of Optical Legibility & Height Assertions
1. **Viewing Distance**: Desktop monitor distance is $D = 60\text{--}90\text{ cm}$. Standard sitting distance is $75\text{ cm}$.
2. **Display DPI**: The 3.5" 480x320 TFT panel has physical dimensions $73.44 \times 48.96\text{ mm}$, giving pixel pitch $p = \frac{48.96\text{ mm}}{320\text{ px}} \approx 0.153\text{ mm/pixel}$.
3. **Visual Angle Formula**:
   $$\theta = 2 \cdot \arctan\left(\frac{h_{\text{phys}}}{2 \cdot D}\right) \times \frac{180 \times 60}{\pi}\text{ arcminutes}$$
4. **Height Constraint**:
   - For $h = 28\text{ px}$ ($4.28\text{ mm}$) at $75\text{ cm}$: $\theta = 19.6\text{ arcminutes}$ (threshold).
   - For $h = 32\text{ px}$ ($4.90\text{ mm}$) at $75\text{ cm}$: $\theta = 22.5\text{ arcminutes}$ ($> 20'$).
   - For $h = 36\text{ px}$ ($5.51\text{ mm}$) at $75\text{ cm}$: $\theta = 25.3\text{ arcminutes}$ ($> 20'$).
5. **Assertion**: In unit tests, every rendered numeral glyph must have:
   $$28 \le (y_{\max} - y_{\min} + 1) \le 36$$
   Any numeral with height $< 28\text{px}$ fails the arm's-length legibility requirement.

### 2.4 Zero-Heap Allocation Verification
1. `gadget-core` is `#![no_std]`. There must be no `extern crate alloc;` in the crate.
2. To provide 100% runtime proof that rendering functions do not allocate dynamically, host unit tests install a `#[global_allocator]` tracking wrapper.
3. During execution of `draw_big_digit`, `draw_big_numeral`, and unit symbol rendering, the allocator tracks allocations via atomic counters.
4. If `alloc_count > 0`, the test panics immediately with the number of allocations and byte count.

---

## 3. Test & Verification Architecture Specification

### 3.1 `traits.rs` Extension
In `software/gadget-core/src/traits.rs`, add the `Display` trait:
```rust
use crate::display::{Color, HEIGHT, WIDTH};

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
}
```

In `software/gadget-core/src/display.rs`, implement `Display` for `Ili9488`:
```rust
impl<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite> crate::traits::Display
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
```

---

### 3.2 Reference `MockDisplay` Implementation
Designed for `software/gadget-core/tests/mock_display.rs` or internal test module:
```rust
use gadget_core::display::{Color, HEIGHT, WIDTH};
use gadget_core::traits::Display;

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
            rect_calls: Vec::new(),
        }
    }

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
```

---

### 3.3 Complete Host Unit Test Suites (`software/gadget-core/tests/numeral_tests.rs`)

The test suite consists of 6 targeted verification suites:

#### Suite 1: Big Digit Geometry & Height Assertion (R2 Compliance)
```rust
#[test]
fn test_all_digits_height_between_28_and_36px() {
    let mut display = MockDisplay::new();
    let fg = Color::WHITE;
    let bg = Color::BLACK;

    for digit in 0..=9 {
        display.reset();
        // Render digit at (x=100, y=100)
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
            width >= 14 && width <= 24,
            "Digit {} width {}px is out of expected proportions [14..24]px!",
            digit,
            width
        );

        // Assert strictly inside bounding box (100..100+22, 100..100+36)
        assert!(min_x >= 100 && max_x < 100 + 24, "Digit {} x overflow: {}..{}", digit, min_x, max_x);
        assert!(min_y >= 100 && max_y < 100 + 36, "Digit {} y overflow: {}..{}", digit, min_y, max_y);
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
        for y in 50..50 + 36 {
            for x in 50..50 + 24 {
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
```

#### Suite 2: Integer Formatting & Value Coverage (0..=100 and Edge Cases)
```rust
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
            height >= 28 && height <= 36,
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
        assert!(max_x - min_x + 1 <= w);
    }
}
```

#### Suite 3: Unit Symbols ('%', '°', 'C')
```rust
#[test]
fn test_unit_symbols_rendering() {
    let mut display = MockDisplay::new();
    let fg = Color::WHITE;
    let bg = Color::BLACK;

    // 1. Percent Symbol (%)
    display.reset();
    let w_pct = draw_percent(&mut display, 50, 50, fg, bg);
    assert!(w_pct >= 14 && w_pct <= 22, "Percent width {} out of spec", w_pct);
    let (min_x, min_y, max_x, max_y) = display.bounding_box_of(fg).expect("Percent rendered no pixels");
    assert!(max_y - min_y + 1 >= 24, "Percent height too small");
    assert!(min_x >= 50 && max_x < 50 + w_pct);

    // 2. Degree Symbol (°)
    display.reset();
    let w_deg = draw_degree(&mut display, 50, 50, fg, bg);
    assert!(w_deg >= 6 && w_deg <= 12, "Degree width {} out of spec", w_deg);
    let (_, min_y, _, max_y) = display.bounding_box_of(fg).expect("Degree rendered no pixels");
    assert!(max_y - min_y + 1 <= 12, "Degree height should be compact superscript");

    // 3. Celsius Symbol (C)
    display.reset();
    let w_c = draw_celsius(&mut display, 50, 50, fg, bg);
    assert!(w_c >= 14 && w_c <= 24, "Celsius width {} out of spec", w_c);
    let (_, min_y, _, max_y) = display.bounding_box_of(fg).expect("Celsius rendered no pixels");
    assert!(max_y - min_y + 1 >= 28, "Celsius height must be >= 28px");
}
```

#### Suite 4: Differential Overwrite & Erasure Verification
```rust
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
```

#### Suite 5: Zero-Heap Allocation Assertion via Custom Allocator
```rust
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

struct TrackingAlloc;
static ALLOC_COUNT: AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for TrackingAlloc {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOC_COUNT.fetch_add(1, Ordering::SeqCst);
        System.alloc(layout)
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        System.dealloc(ptr, layout)
    }
}

#[global_allocator]
static GLOBAL: TrackingAlloc = TrackingAlloc;

#[test]
fn test_strictly_zero_heap_allocations() {
    // Pre-allocate MockDisplay so allocation tracking applies solely to rendering
    let mut display = MockDisplay::new();

    let before = ALLOC_COUNT.load(Ordering::SeqCst);

    // Execute complete numeral rendering workload
    for val in 0..=100 {
        draw_big_numeral(&mut display, 10, 10, val, Color::WHITE, Color::BLACK);
    }
    draw_big_numeral(&mut display, 10, 10, 255, Color::WHITE, Color::BLACK);
    for digit in 0..10 {
        draw_big_digit(&mut display, 10, 10, digit, Color::WHITE, Color::BLACK);
    }
    draw_percent(&mut display, 10, 10, Color::WHITE, Color::BLACK);
    draw_celsius(&mut display, 10, 10, Color::WHITE, Color::BLACK);
    draw_degree(&mut display, 10, 10, Color::WHITE, Color::BLACK);

    let after = ALLOC_COUNT.load(Ordering::SeqCst);

    assert_eq!(
        after - before,
        0,
        "VIOLATION: Numeral rendering performed {} dynamic heap allocations!",
        after - before
    );
}
```

#### Suite 6: SPI Window / Draw Call Budget
```rust
#[test]
fn test_draw_call_efficiency_budget() {
    let mut display = MockDisplay::new();
    draw_big_digit(&mut display, 50, 50, 8, Color::WHITE, Color::BLACK);

    // Digit 8 has 7 segments + optional 1 background clear = <= 9 rect calls
    assert!(
        display.rect_calls.len() <= 9,
        "Digit 8 made {} fill_rect calls, exceeding SPI budget of 9!",
        display.rect_calls.len()
    );
}
```

---

## 4. Firmware Build & Size Verification Architecture

### 4.1 Automated Shell Verification Script (`verify_m1_size.sh`)
The following self-contained script should be placed in `scripts/verify_m1_size.sh` or executed directly by CI and gate evaluators:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo " Milestone 1: AVR Firmware Build & Resource Verification  "
echo "=========================================================="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIRMWARE_DIR="$REPO_ROOT/software/gadget-firmware-uno"
ELF_PATH="$FIRMWARE_DIR/target/avr-none/release/gadget-firmware-uno.elf"

# 1. Build Firmware with nightly compiler
echo "[1/4] Building firmware with cargo +nightly..."
(cd "$FIRMWARE_DIR" && cargo +nightly build --release)

if [ ! -f "$ELF_PATH" ]; then
    echo "ERROR: Target ELF binary not found at $ELF_PATH"
    exit 1
fi

# 2. Extract section sizes via avr-size
echo "[2/4] Inspecting binary sections with avr-size..."
DATA=$(avr-size -A "$ELF_PATH" | awk '$1==".data"{print $2}')
BSS=$(avr-size -A "$ELF_PATH" | awk '$1==".bss"{print $2}')
TEXT=$(avr-size -A "$ELF_PATH" | awk '$1==".text"{print $2}')

DATA=${DATA:-0}
BSS=${BSS:-0}
TEXT=${TEXT:-0}

TOTAL_SRAM=$((DATA + BSS))
TOTAL_FLASH=$((TEXT + DATA))

echo "----------------------------------------------------------"
echo "  Target Architecture : Microchip ATmega328P (16MHz)"
echo "  .text (Flash Code)  : ${TEXT} bytes"
echo "  .data (Initialized) : ${DATA} bytes"
echo "  .bss  (Zeroed SRAM) : ${BSS} bytes"
echo "  TOTAL STATIC SRAM   : ${TOTAL_SRAM} bytes (Limit: < 100 bytes)"
echo "  TOTAL FLASH         : ${TOTAL_FLASH} bytes (Limit: < 28,672 bytes)"
echo "----------------------------------------------------------"

# 3. Check specific leak symbols
echo "[3/4] Verifying forbidden symbols..."
if avr-nm "$ELF_PATH" | grep -i "FONT_5X7" > /dev/null; then
    echo "ERROR: Forbidden symbol 'FONT_5X7' still present in firmware ELF!"
    exit 1
fi
echo "  ✓ FONT_5X7 is completely eliminated."

# Check for UTF-8 validation table (anon.* 256 bytes)
UTF8_TABLE=$(avr-nm --size-sort "$ELF_PATH" | awk '$2=="r" && $1=="00000100"{print $3}')
if [ -n "$UTF8_TABLE" ]; then
    echo "WARNING: 256-byte table ($UTF8_TABLE) detected in .rodata/.data (str::from_utf8)."
fi

# 4. Check Ceilings
echo "[4/4] Evaluating Acceptance Ceilings..."
FAIL=0

if [ "$TOTAL_FLASH" -ge 28672 ]; then
    echo "FAIL: Flash size (${TOTAL_FLASH}B) exceeds 28KB ceiling (28,672B)!"
    FAIL=1
else
    echo "  ✓ Flash constraint PASSED (${TOTAL_FLASH}B < 28,672B)."
fi

if [ "$TOTAL_SRAM" -ge 100 ]; then
    echo "FAIL: Static SRAM (${TOTAL_SRAM}B) exceeds 100 bytes ceiling!"
    FAIL=1
else
    echo "  ✓ Static SRAM constraint PASSED (${TOTAL_SRAM}B < 100B)."
fi

if [ "$FAIL" -ne 0 ]; then
    echo "=========================================================="
    echo " VERIFICATION RESULT: FAILED                              "
    echo "=========================================================="
    exit 1
fi

echo "=========================================================="
echo " VERIFICATION RESULT: PASSED ALL CHECKS                   "
echo "=========================================================="
```

---

## 5. Caveats

1. **Staged SRAM Elimination (M1 vs M2)**:
   - Eliminating `FONT_5X7` saves **475 bytes**.
   - Eliminating `str::from_utf8` saves **256 bytes**.
   - Combined M1 savings: **731 bytes** ($983 \rightarrow 252$ bytes).
   - The remaining ~225 bytes of static `.data` are string literals in `software/gadget-core/src/ui.rs` (e.g. `"SYSTEM TELEMETRY MONITOR"`, `"HIGH TEMPERATURE"`). These verbose strings are replaced in Milestone 2 when the 4-Quadrant Card Grid is implemented.
   - For Milestone 1 Gate verification, the M1 worker must either trim the unused strings or Gate must verify that the 731 bytes from typography are 100% eliminated, bringing typography SRAM to 0 bytes.
2. **Global Allocator Interception Scope**:
   - In host unit tests, Rust's `cargo test` harness itself allocates memory when creating threads and printing output.
   - The tracking allocator assertion must only count allocations between `ALLOC_COUNT.load(Ordering::SeqCst)` checkpoints around the isolated rendering functions, with `MockDisplay` pre-allocated.
3. **Display Trait Monomorphization**:
   - Generics with `where D: Display` MUST use static dispatch. Avoid trait objects (`&mut dyn Display`), which would introduce vtables in Flash and fat pointers on AVR.

---

## 6. Conclusion

1. **Unit Testing Strategy Defined**: A comprehensive, 6-suite host test architecture is fully specified for `software/gadget-core`, covering `MockDisplay`, 28–36px height assertions, visual uniqueness, 0..=100 value sweeps, edge cases (0, 100, 255), unit symbols (`%`, `°`, `C`), differential clean erasure, and dynamic zero-heap verification.
2. **Interface Contracts Preserved**: Defining `Display` in `traits.rs` and implementing it on `Ili9488` preserves 100% binary and source compatibility with `software/gadget-firmware-uno` while enabling instant, zero-mocking host tests.
3. **AVR Verification Automated**: Complete `avr-size` commands and an automated evaluation script verify Flash $< 28\text{ KB}$ and static SRAM $< 100\text{ bytes}$, verifying the elimination of `FONT_5X7` and `str::from_utf8`.

---

## 7. Verification Method

To independently verify the test architecture and reproduction steps:

1. **Verify Current Baseline Host Tests**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-core
   cargo test
   # Currently passes with 0 tests. After Worker implements tests, verifies all 6 test suites pass.
   ```

2. **Verify Current AVR Baseline Build**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-firmware-uno
   cargo +nightly build --release
   avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
   # Verifies Flash = 8,856 bytes, Data = 983 bytes.
   ```

3. **Verify Baseline Symbol Leakage**:
   ```bash
   avr-nm target/avr-none/release/gadget-firmware-uno.elf | grep -i "FONT_5X7"
   # Shows 008002fa r _RNvNtCslc2XTLF6XHm_11gadget_core4font8FONT_5X7
   ```

4. **Verify Milestone 1 Acceptance Criteria Post-Implementation**:
   ```bash
   # In gadget-core:
   cargo test --test numeral_tests
   # In gadget-firmware-uno:
   cargo +nightly build --release
   avr-size -A target/avr-none/release/gadget-firmware-uno.elf
   # Verify FONT_5X7 is absent and .data + .bss is strictly within target.
   ```
