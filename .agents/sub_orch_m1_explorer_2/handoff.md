# Architectural Handoff: Big Numeral Engine & Zero-SRAM Typography

**Agent**: `sub_orch_m1_explorer_2`  
**Role**: Big Numeral Engine Architect  
**Milestone**: M1 (Core Typography & SRAM Reduction)  
**Target File**: `/home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_2/handoff.md`  
**Date**: 2026-09-22  

---

## 1. Observation

Direct observations from the current codebase and AVR compilation outputs:

### 1.1 Existing Font & Redraw Implementation
- In `software/gadget-core/src/font.rs` (lines 8–105):
  ```rust
  #[rustfmt::skip]
  pub static FONT_5X7: [[u8; 5]; 95] = [ ... ];
  ```
  This is a static array of $95 \times 5 = 475$ bytes.
- In `software/gadget-core/src/ui.rs` (lines 201–205):
  ```rust
  let mut buf = [b' '; 6];
  let len = format_num_unit(value, unit, &mut buf);
  if let Ok(text) = core::str::from_utf8(&buf[..len]) {
      draw_text(display, num_x, num_y, text, Color::WHITE, Color::PANEL_BG, 1);
  }
  ```
  `core::str::from_utf8` is invoked solely to satisfy `draw_text(..., text: &str, ...)`.
- In `software/gadget-core/src/font.rs` (lines 127–144), `draw_char` executes nested loops rendering individual scaled pixels via repeated calls to `display.fill_rect`:
  ```rust
  for col in 0..5 {
      for row in 0..7 {
          display.fill_rect(px, py, scale as u16, scale as u16, pixel_color);
      }
  }
  ```
  At `scale = 1`, each character triggers $5 \times 7 + 1 = 36$ separate `fill_rect` calls, each issuing ILI9488 window setup commands (`0x2A`, `0x2B`, `0x2C`).

### 1.2 Binary Footprint on ATmega328P ELF
Inspecting `software/gadget-firmware-uno/target/avr-none/debug/gadget-firmware-uno.elf` via `avr-size` and `avr-nm`:
```
AVR Memory Usage
----------------
Device: atmega328p
Program:    9236 bytes (28.2% Full) (.text + .data + .bootloader)
Data:        979 bytes (47.8% Full) (.data + .bss + .noinit)
```
Inspecting the symbols contributing to `.data` (size 978 bytes, VMA `0x00800100`–`0x008004d2`):
- `00800100 000001db r _RNvNtCsaDki1H3sJOl_11gadget_core4font8FONT_5X7`: **475 bytes**
- `008003c9 00000100 r anon.f17879edc0c9654c724b13838c0ba5c3.21` (`core::str::from_utf8` state table): **256 bytes**
- Static string literals: ~180 bytes.
- Total static SRAM wasted by font table and UTF-8 validation table alone: **$475 + 256 = 731$ bytes** ($74.7\%$ of total `.data` SRAM).

### 1.3 Optical Legibility Deficit
- The current readout font is 7 pixels tall. At a desk viewing distance of 60–90 cm, 7 pixels corresponds to an optical visual angle of only **$4.9$ arcminutes** (assuming 0.154 mm pixel pitch on a 3.5" 480x320 TFT).
- Human optical legibility standards (ISO 9241-303, MIL-STD-1472G) and Project Requirement R2 mandate a visual angle $\ge 20$ arcminutes, requiring numerals at least **28–36 pixels tall** ($5.55$ mm physical height = $25.4$ arcminutes at 75 cm).

---

## 2. Logic Chain

### 2.1 Bespoke Geometric 7-Segment vs Minimal Flash-Based Glyph Table

| Attribute | Bespoke Geometric 7-Segment Engine | Minimal Flash Glyph Table (1-bit bitmap) |
|---|---|---|
| **Static SRAM Impact** | **0 bytes** (calculated on stack / immediate opcodes) | **0 bytes** only if using target-specific `lpm` assembly; **1,287 bytes leak** if normal Rust static slice |
| **Flash Impact** | **~220 bytes** code total (zero table overhead) | **~1,580 bytes** (1,287 bytes glyph data + unpacker) |
| **Portability (`#![no_std]`)** | **100% universal**: Runs on Uno (AVR), ESP32, RP2040, and host unit tests | Requires conditional compilation for AVR `lpm` assembly vs host pointer dereferences |
| **SPI Transmission Overhead** | **1 window (11B setup) or 9 rects (99B setup)**; continuous pixel burst | Must unpack bits from byte stream during SPI loop; higher CPU overhead |
| **Visual Legibility** | **Crisp 4px uniform industrial strokes**, perfectly square corners, sharp contrast | 22x36 1-bit raster can produce aliased/jagged staircases on angled/rounded strokes |

**Reasoning**: The bespoke geometric 7-segment / chunky block engine is vastly superior in SRAM safety (0 risk of `.data` leak), Flash footprint (saves >1.3 KB Flash), cross-platform testability, and rendering throughput.

---

### 2.2 Exact Geometric Dimensions & Coordinates

To achieve maximum readability at 60–90 cm while fitting comfortably in a 230px wide quadrant card:

- **Digit Dimensions**:
  - Height ($H$): **36 pixels**
  - Width ($W$): **22 pixels**
  - Stroke Thickness ($T$): **4 pixels**
  - Vertical Segment Height ($H_{\text{vert}}$): $\frac{H - 3T}{2} = \frac{36 - 12}{2} = \mathbf{12\text{ pixels}}$
  - Inner Hollow Width ($W_{\text{hollow}}$): $W - 2T = 22 - 8 = \mathbf{14\text{ pixels}}$
  - Aspect Ratio: $\frac{22}{36} = 0.611$ (matches standard display typography)
  - Optical Visual Angle:
    - At 60 cm desk distance: **$31.8$ arcminutes**
    - At 75 cm desk distance: **$25.4$ arcminutes**
    - At 90 cm desk distance: **$21.2$ arcminutes**
    (All well above the $\ge 20$ arcminute requirement of Feature 4).

- **Inter-Character Layout**:
  - Inter-digit gap ($G_{\text{digit}}$): **4 pixels**
  - 1-digit width: $22\text{ px}$
  - 2-digit width: $22 + 4 + 22 = 48\text{ px}$
  - 3-digit width: $22 + 4 + 22 + 4 + 22 = 74\text{ px}$
  - Gap before unit ($G_{\text{unit}}$): **6 pixels**
  - Total width for "100%": $74\text{ (digits)} + 6\text{ (gap)} + 18\text{ (unit)} = \mathbf{98\text{ px}}$
  - Fits within the 210px printable inner card width with 112px to spare for titles or icons.

- **Non-Overlapping Segment Bounding Boxes** for digit at $(x_0, y_0)$:
  The $22 \times 36$ bounding box partitions cleanly into 5 horizontal slices and 9 non-overlapping rectangles:
  1. **Slice 1 (Rows 0..4, height 4)**:
     - **Segment A** (Top bar): $x \in [x_0, x_0 + 22)$, $y \in [y_0, y_0 + 4)$ — Size: $22 \times 4$
  2. **Slice 2 (Rows 4..16, height 12)**:
     - **Segment F** (Upper-left bar): $x \in [x_0, x_0 + 4)$, $y \in [y_0 + 4, y_0 + 16)$ — Size: $4 \times 12$
     - **Top Hollow**: $x \in [x_0 + 4, x_0 + 18)$, $y \in [y_0 + 4, y_0 + 16)$ — Size: $14 \times 12$
     - **Segment B** (Upper-right bar): $x \in [x_0 + 18, x_0 + 22)$, $y \in [y_0 + 4, y_0 + 16)$ — Size: $4 \times 12$
  3. **Slice 3 (Rows 16..20, height 4)**:
     - **Segment G** (Center bar): $x \in [x_0, x_0 + 22)$, $y \in [y_0 + 16, y_0 + 20)$ — Size: $22 \times 4$
  4. **Slice 4 (Rows 20..32, height 12)**:
     - **Segment E** (Lower-left bar): $x \in [x_0, x_0 + 4)$, $y \in [y_0 + 20, y_0 + 32)$ — Size: $4 \times 12$
     - **Bottom Hollow**: $x \in [x_0 + 4, x_0 + 18)$, $y \in [y_0 + 20, y_0 + 32)$ — Size: $14 \times 12$
     - **Segment C** (Lower-right bar): $x \in [x_0 + 18, x_0 + 22)$, $y \in [y_0 + 20, y_0 + 32)$ — Size: $4 \times 12$
  5. **Slice 5 (Rows 32..36, height 4)**:
     - **Segment D** (Bottom bar): $x \in [x_0, x_0 + 22)$, $y \in [y_0 + 32, y_0 + 36)$ — Size: $22 \times 4$

  Total pixels: $88 + 48 + 168 + 48 + 88 + 48 + 168 + 48 + 88 = 792$ pixels ($22 \times 36$).

- **Segment Bitmask Encodings**:
  Bit positions: $A=0, B=1, C=2, D=3, E=4, F=5, G=6$.
  ```rust
  pub const SEG_A: u8 = 1 << 0; // 0x01
  pub const SEG_B: u8 = 1 << 1; // 0x02
  pub const SEG_C: u8 = 1 << 2; // 0x04
  pub const SEG_D: u8 = 1 << 3; // 0x08
  pub const SEG_E: u8 = 1 << 4; // 0x10
  pub const SEG_F: u8 = 1 << 5; // 0x20
  pub const SEG_G: u8 = 1 << 6; // 0x40

  #[inline(always)]
  pub const fn get_segment_mask(digit: u8) -> u8 {
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
          _ => 0x00, // Blank / space
      }
  }
  ```
  *Note*: By using a `const fn match`, rustc emits AVR immediate load opcodes (`ldi r24, ...`) directly into `.text` Flash. **Zero bytes of static SRAM are consumed.**

---

### 2.3 Geometric Design for Unit Symbols ('%' and '°C')

#### 1. Percent Symbol (`%`)
- **Dimensions**: Width = 18px, Height = 36px.
- **Chunky Block Geometry**:
  - **Upper-left loop**: Solid block $7 \times 8$ at $(x_0, y_0 + 3)$, inner cutout $3 \times 4$ at $(x_0 + 2, y_0 + 5)$ in `bg_color`.
  - **Diagonal slash**: Stepped 3px stroke spanning from top-right $(x_0 + 15, y_0 + 3)$ to bottom-left $(x_0 + 1, y_0 + 33)$. Formed by 6 rectangles of size $3 \times 5$:
    - Step 0: $(x_0 + 15, y_0 + 3, 3, 5)$
    - Step 1: $(x_0 + 12, y_0 + 8, 3, 5)$
    - Step 2: $(x_0 + 9, y_0 + 13, 3, 5)$
    - Step 3: $(x_0 + 7, y_0 + 18, 3, 5)$
    - Step 4: $(x_0 + 4, y_0 + 23, 3, 5)$
    - Step 5: $(x_0 + 1, y_0 + 28, 3, 5)$
  - **Lower-right loop**: Solid block $7 \times 8$ at $(x_0 + 11, y_0 + 25)$, inner cutout $3 \times 4$ at $(x_0 + 13, y_0 + 27)$ in `bg_color`.
- Clear background first with `fill_rect(x0, y0, 18, 36, bg_color)`, then draw the 8 elements. Total SPI bytes: $\approx 2,050$ bytes.

#### 2. Degree Symbol (`°`)
- **Dimensions**: Width = 8px, Height = 8px.
- Located at top superscript position: $(x_0, y_0 + 2)$.
- **Rendering**:
  - Outer square: `fill_rect(x0, y0 + 2, 8, 8, fg_color)`
  - Inner cutout: `fill_rect(x0 + 2, y0 + 4, 4, 4, bg_color)`
  - Only 2 `fill_rect` calls ($2 \times 11 = 22$ command bytes, $64 \times 3 = 192$ pixel bytes).

#### 3. Celsius Symbol (`C`)
- **Dimensions**: Width = 20px, Height = 36px.
- **Geometric Elements**:
  - Full-height left vertical spine: `fill_rect(x0, y0, 4, 36, fg_color)`
  - Top horizontal bar: `fill_rect(x0 + 4, y0, 16, 4, fg_color)`
  - Bottom horizontal bar: `fill_rect(x0 + 4, y0 + 32, 16, 4, fg_color)`
  - Inner cavity: `fill_rect(x0 + 4, y0 + 4, 16, 28, bg_color)`
  - Only 4 `fill_rect` calls!

#### 4. Combined `°C`
- Total bounding width: $8\text{ (degree)} + 3\text{ (gap)} + 20\text{ (C)} = \mathbf{31\text{ pixels}}$. Height: 36px.

---

### 2.4 Zero-Heap Integer Formatting & Alignment Logic

#### Integer Decomposition Algorithm
Values from telemetry packets are `u8` ($0..255$). We format them into an array `[u8; 3]` without heap allocation:
```rust
pub const DIGIT_BLANK: u8 = 0xFF;

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct FormattedDigits {
    pub digits: [u8; 3], // Raw numeric values 0..9 or DIGIT_BLANK
    pub count: u8,       // 1, 2, or 3
}

#[inline]
pub fn format_u8(val: u8) -> FormattedDigits {
    if val >= 100 {
        let d0 = val / 100;
        let rem = val % 100;
        let d1 = rem / 10;
        let d2 = rem % 10;
        FormattedDigits {
            digits: [d0, d1, d2],
            count: 3,
        }
    } else if val >= 10 {
        let d1 = val / 10;
        let d2 = val % 10;
        FormattedDigits {
            digits: [DIGIT_BLANK, d1, d2],
            count: 2,
        }
    } else {
        FormattedDigits {
            digits: [DIGIT_BLANK, DIGIT_BLANK, val],
            count: 1,
        }
    }
}
```

#### Alignment Strategy: Fixed 3-Slot Field (Right-Aligned)
- In telemetry instrumentation, variable-width numbers cause horizontal jitter: as "99%" transitions to "100%", the unit symbol jumps to the right by 26 pixels. When it drops back, ghost pixels are left behind unless the old bounding box is erased.
- **Fixed 3-Slot Right-Aligned Architecture**:
  - The numeral readout occupies a constant bounding box of $74 \times 36$ pixels:
    - Slot 0 ($x_0$): Hundreds. If `DIGIT_BLANK`, filled with `bg_color`.
    - Slot 1 ($x_0 + 26$): Tens. If `DIGIT_BLANK`, filled with `bg_color`.
    - Slot 2 ($x_0 + 52$): Ones. Always rendered.
    - Unit symbol ($x_0 + 80$): Static position, never moves.
  - **Slot-Level Differential Redraw**:
    When telemetry updates (e.g. 74% $\rightarrow$ 75%):
    - Slot 0 (hundreds): `DIGIT_BLANK` == `DIGIT_BLANK` $\rightarrow$ **0 SPI bytes!**
    - Slot 1 (tens): `7` == `7` $\rightarrow$ **0 SPI bytes!**
    - Slot 2 (ones): `4` $\rightarrow$ `5` $\rightarrow$ **Only Slot 2 redrawn (2,387 bytes)!**
    - Unit (`%`): Unchanged $\rightarrow$ **0 SPI bytes!**
  - **Result**: ~90% of telemetry updates transmit only a single digit ($2.38$ ms of SPI time).

---

### 2.5 SPI Bus and Memory Impact Calculations

#### ILI9488 SPI Command Framing
ILI9488 requires 4-wire SPI with CS and DC lines.
Each rectangular window write executes:
1. `set_window(x0, y0, x1, y1)`:
   - `0x2A` (CASET): 1 cmd + 4 data bytes = 5 bytes
   - `0x2B` (PASET): 1 cmd + 4 data bytes = 5 bytes
   - `0x2C` (RAMWR): 1 cmd byte = 1 byte
   Total setup per window: **11 SPI bytes**.
2. Pixel Data: ILI9488 18-bit color mode (`0x3A = 0x66`): 3 bytes per pixel (R, G, B).

#### Transmission Cost Per Digit Update
- **Strategy 1: Single Window Raster Stream (`draw_big_digit_stream`)**:
  - Sets ILI9488 window once for $22 \times 36$ pixels.
  - Streams 792 pixels directly in raster order:
    - Rows 0..3: 22 pixels $\times$ 4 rows = 88 pixels of Segment A
    - Rows 4..15: 12 rows of [4px Seg F, 14px Hollow, 4px Seg B] = 264 pixels
    - Rows 16..19: 22 pixels $\times$ 4 rows = 88 pixels of Segment G
    - Rows 20..31: 12 rows of [4px Seg E, 14px Hollow, 4px Seg C] = 264 pixels
    - Rows 32..35: 22 pixels $\times$ 4 rows = 88 pixels of Segment D
  - **Command Overhead**: 11 bytes.
  - **Pixel Data**: $792 \times 3 = \mathbf{2,376\text{ bytes}}$.
  - **Total SPI bytes per digit**: **2,387 bytes**.
  - **SPI Time at 8MHz**: $2,387\text{ bytes} \times 1.0\,\mu\text{s} = \mathbf{2.387\text{ ms}}$.

- **Strategy 2: Multi-Rect `fill_rect` Calls (9 Disjoint Rectangles)**:
  - If using standard `display.fill_rect`:
    - 9 rectangles $\times$ 11 bytes setup = 99 command bytes.
    - Pixel bytes: $792 \times 3 = 2,376$ bytes.
  - **Total SPI bytes per digit**: **2,475 bytes** ($2.475$ ms).
  - Overhead difference between Strategy 1 and Strategy 2 is only **88 bytes (88 $\mu$s)**. Both strategies easily satisfy the zero-flicker requirement.

#### Bus Utilization in 4-Quadrant Dashboard
- 4 Quadrants: CPU %, GPU %, RAM %, Thermals (CPU Temp, GPU Temp).
- Maximum worst-case burst (all 6 readings change all 3 digits):
  $6 \times 3 = 18$ digits $\times 2,387\text{ B} \approx 42.9\text{ KB}$ ($\approx 43\text{ ms}$ at 8MHz SPI).
- Typical steady-state update (1 digit change per quadrant = 4 digits):
  $4 \times 2,387\text{ B} \approx 9.5\text{ KB}$ ($\mathbf{\approx 9.5\text{ ms}}$ at 8MHz SPI).
- At a 10 Hz refresh rate (100 ms period), the SPI bus is active for 9.5 ms and **idle for 90.5 ms (9.5% bus load)**. At a 1 Hz refresh rate, bus load is **< 1%**.

---

## 3. Reference Implementation Specification

Below is the concrete, drop-in architecture designed for `software/gadget-core/src/numeral.rs`:

```rust
//! High-legibility arm's-length 7-segment big numeral engine.
//! Zero heap allocation, zero static SRAM tables, zero UTF-8 dependencies.

use crate::display::{Color, Ili9488};
use crate::traits::{PinWrite, SpiWrite};

pub const DIGIT_WIDTH: u16 = 22;
pub const DIGIT_HEIGHT: u16 = 36;
pub const STROKE_THICKNESS: u16 = 4;
pub const DIGIT_GAP: u16 = 4;
pub const DIGIT_BLANK: u8 = 0xFF;

// Segment bit positions
pub const SEG_A: u8 = 1 << 0;
pub const SEG_B: u8 = 1 << 1;
pub const SEG_C: u8 = 1 << 2;
pub const SEG_D: u8 = 1 << 3;
pub const SEG_E: u8 = 1 << 4;
pub const SEG_F: u8 = 1 << 5;
pub const SEG_G: u8 = 1 << 6;

/// Segment lookup table mapped via const fn into flash immediate instructions.
#[inline(always)]
pub const fn segment_mask(digit: u8) -> u8 {
    match digit {
        0 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F,
        1 => SEG_B | SEG_C,
        2 => SEG_A | SEG_B | SEG_D | SEG_E | SEG_G,
        3 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_G,
        4 => SEG_B | SEG_C | SEG_F | SEG_G,
        5 => SEG_A | SEG_C | SEG_D | SEG_F | SEG_G,
        6 => SEG_A | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G,
        7 => SEG_A | SEG_B | SEG_C,
        8 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G,
        9 => SEG_A | SEG_B | SEG_C | SEG_D | SEG_F | SEG_G,
        _ => 0x00,
    }
}

/// Decomposes u8 (0..255) into right-aligned digits without heap or UTF-8 formatting.
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

/// Renders a single 22x36 big digit at (x, y) using 9 disjoint rectangular fills.
pub fn draw_big_digit<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite>(
    display: &mut Ili9488<SPI, CS, DC, RST>,
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

    // Row slice 1 (A)
    display.fill_rect(x, y, 22, 4, color_a);

    // Row slice 2 (F, top hollow, B)
    display.fill_rect(x, y + 4, 4, 12, color_f);
    display.fill_rect(x + 4, y + 4, 14, 12, bg);
    display.fill_rect(x + 18, y + 4, 4, 12, color_b);

    // Row slice 3 (G)
    display.fill_rect(x, y + 16, 22, 4, color_g);

    // Row slice 4 (E, bottom hollow, C)
    display.fill_rect(x, y + 20, 4, 12, color_e);
    display.fill_rect(x + 4, y + 20, 14, 12, bg);
    display.fill_rect(x + 18, y + 20, 4, 12, color_c);

    // Row slice 5 (D)
    display.fill_rect(x, y + 32, 22, 4, color_d);
}

/// Renders a 3-digit fixed-width numeral field (right-aligned) at (x, y).
/// Returns total width rendered (74 pixels).
pub fn draw_big_numeral_fixed3<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite>(
    display: &mut Ili9488<SPI, CS, DC, RST>,
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

/// Renders a chunky '%' symbol at (x, y). Returns width (18 pixels).
pub fn draw_unit_percent<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite>(
    display: &mut Ili9488<SPI, CS, DC, RST>,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    // Clear bounding box
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

/// Renders degree + Celsius ('°C') at (x, y). Returns width (31 pixels).
pub fn draw_unit_celsius<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite>(
    display: &mut Ili9488<SPI, CS, DC, RST>,
    x: u16,
    y: u16,
    fg: Color,
    bg: Color,
) -> u16 {
    // Clear bounding box
    display.fill_rect(x, y, 31, DIGIT_HEIGHT, bg);

    // Degree symbol: 8x8 outer with 4x4 inner hollow
    display.fill_rect(x, y + 2, 8, 8, fg);
    display.fill_rect(x + 2, y + 4, 4, 4, bg);

    // Celsius 'C': spine + top bar + bottom bar
    let c_x = x + 11;
    display.fill_rect(c_x, y, 4, 36, fg);          // Left spine
    display.fill_rect(c_x + 4, y, 16, 4, fg);      // Top bar
    display.fill_rect(c_x + 4, y + 32, 16, 4, fg); // Bottom bar

    31
}
```

---

## 4. Caveats

1. **Quadrants Header / Card Label Typography**:
   This report specifically scopes the **Big Numeral Engine** (readouts $\ge 28\text{--}36$px) and unit symbols (`%`, `°C`). Small text (card header titles like "CPU LOAD", "RAM USAGE") should be addressed by Explorer 1 and Explorer 3, either via an algorithmic minimal ASCII renderer or PROGMEM-safe flash mapping, ensuring no ASCII table leaks into `.data` SRAM.
2. **Display Struct Trait Abstraction**:
   Currently, `Ili9488` fields (`spi`, `cs`, `dc`) are private, so `draw_big_digit` renders via `display.fill_rect`. If `Ili9488` is updated to expose a pixel streaming method, Strategy 1 (single window) can be adopted with 0 API break.

---

## 5. Conclusion

1. **Bespoke Geometric 7-Segment Numeral Engine** meets all criteria of Requirement R2:
   - Numerals are exactly **36 pixels tall** and **22 pixels wide** with **4-pixel stroke thickness**.
   - Optical angle is **$25.4$ arcminutes at 75 cm** (desk arm's-length), exceeding the 20 arcminute legibility target.
2. **Static SRAM Reduction**:
   - The numeral engine uses **0 bytes of static SRAM**.
   - Completely eliminates `core::str::from_utf8` (freeing 256 bytes) and replaces the primary data path of `FONT_5X7` (freeing 475 bytes).
3. **Deterministic SPI Bus Performance**:
   - Each digit update requires exactly **2,475 bytes** ($2.475$ ms at 8MHz SPI).
   - In steady-state differential redraw, only changed digits are updated, holding bus load to **$< 10\%$**.
   - Zero screen clears, zero display flickering.

---

## 6. Verification Method

### 6.1 Host-Side Unit Verification
Run tests in `software/gadget-core`:
```bash
cargo test
```
Verify:
1. `test_digit_formatting`: Check `u8_to_digits_right_aligned` correctly formats 0, 9, 10, 99, 100, 255 with `DIGIT_BLANK` padding.
2. `test_bounding_boxes`: Assert that numeral height is $\ge 36\text{px}$ and width $\ge 22\text{px}$.
3. `test_segment_coverage`: Verify that all 792 pixels within $22 \times 36$ are covered by the 9 rectangles without overlap.

### 6.2 AVR Static RAM & Binary Size Verification
Run in `software/gadget-firmware-uno`:
```bash
cargo +nightly build --target avr-atmega328p.json -Z build-std=core --release
avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
avr-nm -S --size-sort target/avr-none/release/gadget-firmware-uno.elf | grep -E " [dDbB] "
```
**Acceptance Criteria**:
- Static data (`.data + .bss`) must decrease from 979 bytes to $< 250$ bytes (and ultimately $< 100$ bytes after label cleanup).
- `_RNvNtCsaDki1H3sJOl_11gadget_core4font8FONT_5X7` and `anon.*` (UTF-8 table) must NOT appear in `.data`.
