# Handoff Report: Typography & SRAM Architecture Exploration (Milestone 1)

## 1. Observation

### 1.1 Firmware Memory Baseline (`target/avr-none/release/gadget-firmware-uno.elf`)
Running `avr-size -C --mcu=atmega328p` on the compiled release firmware:
```text
AVR Memory Usage
----------------
Device: atmega328p

Program:    8856 bytes (27.0% Full)
(.text + .data + .bootloader)

Data:        983 bytes (48.0% Full)
(.data + .bss + .noinit)
```
- **Total Static SRAM consumed**: **983 bytes** (48.0% of ATmega328P's 2,048-byte physical SRAM).
- **Static SRAM Ceiling in Acceptance Criteria**: `< 100 bytes`.
- **Violation**: The current firmware exceeds the static SRAM ceiling by **883 bytes** (almost 10x over budget).

### 1.2 ELF Section Breakdown (`avr-objdump -h`)
```text
Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .data         000003d6  00800100  00001ec2  00001f76  2**0
                  CONTENTS, ALLOC, LOAD, READONLY, DATA
  1 .text         00001ec2  00000000  00000000  000000b4  2**1
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
  2 .bss          00000001  008004d6  008004d6  0000234c  2**0
                  ALLOC
```
- `.data` section size: `0x03d6` = **982 bytes**
- `.bss` section size: `0x0001` = **1 byte**
- Total static SRAM: `982 + 1 = 983 bytes`.

### 1.3 Exact SRAM Symbol Census (`avr-nm -C` and `avr-objdump -s -j .data`)
Inspecting the 982 bytes of `.data` starting at SRAM address `0x00800100`:

| Address Range | Size (Bytes) | Category | Symbol / Source | Description |
|---|---|---|---|---|
| `0x00800100` – `0x008001f9` | **250 B** | String Literals | `anon.fad58de7366495db4650cfefac2fcd61.0..31` in `ui.rs` & `main.rs` | "SYSTEM TELEMETRY MONITOR", "LIVE", "[ CPU & MEMORY ]", "DEVICE HARDWARE:", "HIGH TEMPERATURE", "! CRITICAL HOT !", "CPU LOAD", "CPU TEMP", "GPU LOAD", "GPU TEMP", "RAM USAGE", "BATTERY", "[ GPU & GRAPHICS ]", "NVIDIA RTX 4050", "THERMAL STATUS:", "%", "C", "COOL & NORMAL", "ACK\n", "GADGET_READY\n" |
| `0x008001fa` – `0x008002f9` | **256 B** | UTF-8 Validation Table | `anon.ca5ba2dec42ec402aac11eec41e77a9b.211` (`core::str::validations::UTF8_CHAR_WIDTH`) | Pulled by `core::str::from_utf8` call at `software/gadget-core/src/ui.rs:203` |
| `0x008002fa` – `0x008004d5` | **475 B** | Full ASCII Font Table | `gadget_core::font::FONT_5X7` | `pub static FONT_5X7: [[u8; 5]; 95]` at `software/gadget-core/src/font.rs:9` (95 glyphs × 5 columns) |
| `0x008004d6` – `0x008004d6` | **1 B** | Alignment | Linker padding | Alignment to `.bss` boundary |
| `0x008004d6` – `0x008004d7` | **1 B** | `.bss` | `DEVICE_PERIPHERALS` | Peripherals singleton in `arduino_hal` |
| **TOTAL** | **983 B** | | | **48.0% of total ATmega328P SRAM** |

Verbatim excerpt from `avr-objdump -s -j .data`:
```text
 800100 1216221c 2234323e 5a535953 54454d20  .."."42>ZSYSTEM 
 800110 54454c45 4d455452 59204d4f 4e49544f  TELEMETRY MONITO
 800120 52ffffff 4c495645 41434b0a 0ad26e5b  R...LIVEACK...n[
 ...
 8001f0 4745545f 52454144 590a0101 01010101  GET_READY.......
 800200 01010101 01010101 01010101 01010101  ................
 800210 01010101 01010101 01010101 01010101  ................
 ...
 8002f0 00000000 00000000 00000000 00000000  ................
 800300 005f0000 00070007 00147f14 7f14242a  ._............$*
```

### 1.4 Code References
1. `software/gadget-core/src/font.rs:9`:
   ```rust
   pub static FONT_5X7: [[u8; 5]; 95] = [ ... ];
   ```
   Referenced **only once** across the entire workspace, at `font.rs:110`:
   ```rust
   FONT_5X7[(code - 32) as usize]
   ```
2. `software/gadget-core/src/ui.rs:201-205`:
   ```rust
   let mut buf = [b' '; 6];
   let len = format_num_unit(value, unit, &mut buf);
   if let Ok(text) = core::str::from_utf8(&buf[..len]) {
       draw_text(display, num_x, num_y, text, Color::WHITE, Color::PANEL_BG, 1);
   }
   ```
   Here, integers formatted into raw bytes are validated via `core::str::from_utf8` solely to pass a `&str` into `draw_text`.
3. `software/gadget-core/src/font.rs:146-159`:
   ```rust
   pub fn draw_text<...>(display: &mut ..., mut x: u16, y: u16, text: &str, ...) {
       let char_width = 6 * (scale as u16);
       for c in text.chars() {
           draw_char(display, x, y, c, fg, bg, scale);
           x += char_width;
       }
   }
   ```
   `text.chars()` iterates Unicode code points rather than ASCII bytes.

---

## 2. Logic Chain

### 2.1 Why `FONT_5X7` Leaks into AVR SRAM
1. **Harvard Architecture**: The ATmega328P has distinct address spaces for Flash (Program Memory) and SRAM (Data Memory). Flash is read via the `LPM` (Load Program Memory) instruction; SRAM is read via `LD`/`LDS`/`LDD`.
2. **Rust LLVM Uniform Pointer Model**: Rust pointers (`&T`, `*const T`) on AVR are 16-bit pointers assumed to point to SRAM. LLVM emits `LD`/`LDS` instructions to dereference standard pointers. There is no generic architecture-agnostic way in `#![no_std]` Rust to declare a pointer that automatically generates `LPM` instructions when dereferenced without using target-specific crates (like `avr-progmem`).
3. **Linker Script Behavior**: Because normal Rust code dereferencing `&FONT_5X7` emits `LD`, the AVR GNU linker script must place read-only static data (`.rodata`) into the `.data` load image so that it resides in SRAM at runtime.
4. **C-Runtime Initialization**: The AVR startup code (`crt1.S` / `__do_copy_data`) copies the entire `.data` section from Flash (LMA `0x00001ec2`) into SRAM (VMA `0x00800100`) before `main()` executes.
5. **Conclusion**: Defining `pub static FONT_5X7: [[u8; 5]; 95]` causes all 475 bytes to be duplicated into SRAM at boot.

### 2.2 Why `core::str::from_utf8` Leaks 256 Bytes into SRAM
1. In `core::str::validations`, UTF-8 byte classification is implemented using a static lookup table `UTF8_CHAR_WIDTH: [u8; 256]`.
2. Calling `core::str::from_utf8(&buf[..len])` in `ui.rs:203` introduces a dependency on `UTF8_CHAR_WIDTH`.
3. Following the exact same mechanism as `FONT_5X7`, `UTF8_CHAR_WIDTH` is placed into `.rodata` and copied into SRAM (`anon.ca5ba2dec42ec402aac11eec41e77a9b.211`, 256 bytes).
4. Eliminating `core::str::from_utf8` immediately frees **256 bytes** of SRAM with zero side effects.

### 2.3 Why String Literals Consume 250 Bytes of SRAM
1. In the current `ui.rs`, extensive boilerplate labels ("SYSTEM TELEMETRY MONITOR", "DEVICE HARDWARE:", "NVIDIA RTX 4050", "THERMAL STATUS:", "HIGH TEMPERATURE", etc.) are defined as `&str` literals.
2. In AVR Rust, string literals reside in `.rodata`, which is copied into SRAM at boot.
3. The new 4-Quadrant Big Block UI/UX replaces all verbose boilerplate with 4 simple card headers ("CPU", "GPU", "RAM", "TMP"), unit indicators ("%", "C"), and status tags ("PEAK").
4. The new label set totals fewer than 25 characters, reducing string literal SRAM from ~250 bytes to ~25 bytes.

---

## 3. Technical Recommendations

### 3.1 Design of `software/gadget-core/src/numeral.rs` (Big Block Numerals)
To satisfy **Requirement R2** (numerals >= 28–36px tall, optical angle >= 20 arcminutes at 60–90 cm) with **zero SRAM tables**:

#### Geometric 7-Segment Block Engine
- **Glyph Dimensions**:
  - `DIGIT_WIDTH`: 18 pixels
  - `DIGIT_HEIGHT`: 32 pixels (satisfies 28–36px height requirement)
  - `STROKE_WIDTH`: 4 pixels
  - `DIGIT_GAP`: 4 pixels
- **Optical Viewing Angle**:
  - At 70 cm desk viewing distance, 32px (5.4 mm on 3.5" 150 DPI display) subtends **26.5 arcminutes**, easily surpassing the 20 arcminute minimum.
- **Segment Mask (0 SRAM bytes)**:
  Implemented as a pure `const fn` with a `match` expression:
  ```rust
  pub const fn segment_bits(digit: u8) -> u8 {
      match digit {
          0 => 0x3F, // A, B, C, D, E, F
          1 => 0x06, // B, C
          2 => 0x5B, // A, B, D, E, G
          3 => 0x4F, // A, B, C, D, G
          4 => 0x66, // B, C, F, G
          5 => 0x6D, // A, C, D, F, G
          6 => 0x7D, // A, C, D, E, F, G
          7 => 0x07, // A, B, C
          8 => 0x7F, // A, B, C, D, E, F, G
          9 => 0x6F, // A, B, C, D, F, G
          _ => 0x00, // Blank / space
      }
  }
  ```
  In AVR assembly, this generates immediate `ldi` instructions in `.text` (Flash) and **0 bytes of `.data` / SRAM**.
- **Segment Coordinates (32×18 px, 4px stroke)**:
  - `A` (Top horizontal): `(x + 2, y, 14, 4)`
  - `B` (Top-right vertical): `(x + 14, y + 2, 4, 13)`
  - `C` (Bottom-right vertical): `(x + 14, y + 17, 4, 13)`
  - `D` (Bottom horizontal): `(x + 2, y + 28, 14, 4)`
  - `E` (Bottom-left vertical): `(x, y + 17, 4, 13)`
  - `F` (Top-left vertical): `(x, y + 2, 4, 13)`
  - `G` (Middle horizontal): `(x + 2, y + 14, 14, 4)`
- **Render Functions**:
  1. `draw_big_digit<SPI, CS, DC, RST>(display, x, y, digit: u8, color: Color, bg_color: Color)`:
     - Clears the 18×32 bounding box with `display.fill_rect(x, y, 18, 32, bg_color)`.
     - Draws active segments via `display.fill_rect(...)`.
     - At most 8 `fill_rect` calls per digit.
  2. `draw_big_numeral<SPI, CS, DC, RST>(display, x, y, value: u8, color: Color, bg_color: Color) -> u16`:
     - Decomposes `value` (0..255) using integer arithmetic:
       ```rust
       let d0 = value / 100;
       let d1 = (value / 10) % 10;
       let d2 = value % 10;
       ```
     - For 3-digit fixed-width layout: renders 3 digits with leading zero suppression (renders blank for leading zeros, maintaining a stable 62px bounding box).
     - Returns total width: `3 * 18 + 2 * 4 = 62` pixels.
     - **Allocations**: 0 bytes. **SRAM tables**: 0 bytes. **`from_utf8` calls**: 0.

### 3.2 Refactoring `software/gadget-core/src/font.rs` (Zero-SRAM Labels)
To support card headers ("CPU", "GPU", "RAM", "TMP"), unit indicators ("%", "C"), and badges without keeping a 475-byte table:

1. **Delete `pub static FONT_5X7`**:
   Remove the 475-byte static array entirely.
2. **Implement `get_glyph_5x7(c: u8) -> [u8; 5]` via Flash `match`**:
   ```rust
   pub fn get_glyph_5x7(c: u8) -> [u8; 5] {
       match c {
           b' ' => [0x00, 0x00, 0x00, 0x00, 0x00],
           b'%' => [0x23, 0x13, 0x08, 0x64, 0x62],
           b'A' => [0x7E, 0x11, 0x11, 0x11, 0x7E],
           b'C' => [0x3E, 0x41, 0x41, 0x41, 0x22],
           b'E' => [0x7F, 0x49, 0x49, 0x49, 0x41],
           b'G' => [0x3E, 0x41, 0x49, 0x49, 0x7A],
           b'K' => [0x7F, 0x08, 0x14, 0x22, 0x41],
           b'M' => [0x7F, 0x02, 0x0C, 0x02, 0x7F],
           b'P' => [0x7F, 0x09, 0x09, 0x09, 0x06],
           b'R' => [0x7F, 0x09, 0x19, 0x29, 0x46],
           b'T' => [0x01, 0x01, 0x7F, 0x01, 0x01],
           b'U' => [0x3F, 0x40, 0x40, 0x40, 0x3F],
           b'[' => [0x00, 0x7F, 0x41, 0x41, 0x00],
           b']' => [0x00, 0x41, 0x41, 0x7F, 0x00],
           b':' => [0x00, 0x36, 0x36, 0x00, 0x00],
           b'0'..=b'9' => [ ... ], // optional 10 digit fallback
           _ => [0x00, 0x00, 0x00, 0x00, 0x00],
       }
   }
   ```
   - Returning `[u8; 5]` from a `match` expression generates inline `ldi` instructions in `.text`.
   - **Static SRAM consumed**: **0 bytes**.
3. **Refactor `draw_text` and Add `draw_ascii`**:
   ```rust
   pub fn draw_ascii<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite>(
       display: &mut Ili9488<SPI, CS, DC, RST>,
       mut x: u16,
       y: u16,
       bytes: &[u8],
       fg: Color,
       bg: Color,
       scale: u8,
   ) {
       let char_width = 6 * (scale.max(1) as u16);
       for &b in bytes {
           draw_char_byte(display, x, y, b, fg, bg, scale);
           x += char_width;
       }
   }

   pub fn draw_text<SPI: SpiWrite, CS: PinWrite, DC: PinWrite, RST: PinWrite>(
       display: &mut Ili9488<SPI, CS, DC, RST>,
       x: u16,
       y: u16,
       text: &str,
       fg: Color,
       bg: Color,
       scale: u8,
   ) {
       draw_ascii(display, x, y, text.as_bytes(), fg, bg, scale);
   }
   ```
   - `text.as_bytes()` avoids `text.chars()` Unicode decoding.
   - Eliminates all needs for `core::str::from_utf8`.

### 3.3 Expected Post-Refactor SRAM Breakdown
| Item | Baseline SRAM | Post-M1 SRAM | Savings |
|---|---|---|---|
| `FONT_5X7` static table | 475 B | 0 B | -475 B |
| `core::str::from_utf8` table | 256 B | 0 B | -256 B |
| String literals (`ui.rs` + `main.rs`) | 250 B | ~25 B | -225 B |
| `DEVICE_PERIPHERALS` (`.bss`) | 1 B | 1 B | 0 B |
| **Total Static SRAM** | **983 B** | **~26 B** | **-957 B (97.4% reduction)** |

The firmware static SRAM drops to **~26 bytes**, comfortably below the 100-byte ceiling.

---

## 4. Caveats
1. **Flash Code Size Tradeoff**: Returning glyph arrays from `match` branches uses instructions in `.text` (Flash) instead of `.rodata`. Since our current Flash footprint is only 8.8 KB out of 32 KB (27% full), spending ~200–300 bytes of Flash to save 475 bytes of SRAM is an ideal tradeoff for the ATmega328P.
2. **Unsupported Lowercase Characters**: If `get_glyph_5x7` is restricted to uppercase letters and punctuation, any lowercase string will render as blanks. This is intentional for the 4-Quadrant UI (all card headers and labels are uppercase). If lowercase characters are ever required in future milestones, their 5-byte patterns can be added to the match statement without any SRAM penalty.
3. **SPI Window Overhead**: While the geometric 7-segment digit performs 8 `fill_rect` calls (each establishing an SPI window), this is ~4.5x fewer SPI window commands than the 35 `fill_rect` calls required by a scaled 5x7 bitmap font.

---

## 5. Conclusion
1. **Root cause confirmed**: 74.4% (731 bytes) of the 983 bytes of SRAM consumption in `gadget-firmware-uno` is directly attributable to `pub static FONT_5X7` (475B) and `core::str::from_utf8` (256B), with the remaining 250 bytes coming from verbose string literals.
2. **Complete elimination is viable and low-risk**:
   - `FONT_5X7` is only referenced internally in `font.rs:110` and can be completely eliminated without breaking external contracts.
   - `core::str::from_utf8` can be eliminated by refactoring `ui.rs` to format integer digits directly via arithmetic division and rendering byte slices `&[u8]`.
   - Primary numerals can be rendered with high arm's-length legibility (32px height, 18px width, 4px stroke) via a bespoke 7-segment engine in `src/numeral.rs` that consumes 0 bytes of SRAM.
   - Quadrant headers and unit labels can be rendered via a code-embedded `match` function in `src/font.rs` that consumes 0 bytes of SRAM.
3. **Projected SRAM outcome**: Static SRAM will reduce from **983 bytes to ~26 bytes**, easily satisfying the `< 100 bytes` ceiling in Acceptance Criteria R4 / Feature 14.

---

## 6. Verification Method

To verify these findings independently:

1. **Verify Baseline SRAM & Sections**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-firmware-uno
   cargo +nightly build --release
   avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
   avr-objdump -h target/avr-none/release/gadget-firmware-uno.elf
   ```
2. **Inspect Specific Symbols in `.data`**:
   ```bash
   avr-nm -C target/avr-none/release/gadget-firmware-uno.elf | grep -v ' [tTwW] '
   # Look for gadget_core::font::FONT_5X7 at 0x008002fa (size 475)
   # Look for anon.*.211 (UTF-8 table) at 0x008001fa (size 256)
   ```
3. **Verify Removal during Milestone 1 Implementation**:
   After Worker implements `numeral.rs` and refactors `font.rs`:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-firmware-uno
   cargo +nightly build --release
   avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
   # Verify Data (.data + .bss) is < 100 bytes (expected ~26 bytes).
   ```
4. **Host Unit Tests**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-core
   cargo test
   # Test numeral formatting for all 0..=255 values, digit bounding boxes, and zero-allocation rendering.
   ```
