# Firmware Core Survey & Architectural Analysis Report

## 1. Observation

### 1.1 Codebase Structure & Workspace Layout
- `software/gadget-core`:
  - `src/lib.rs` (lines 1–11): Declares `#![no_std]`, modules `display`, `font`, `traits`, `ui`. Notice `pet.rs` is present on disk (241 lines, companion pet sprite engine) but is commented out / not exported in `lib.rs`.
  - `src/traits.rs` (lines 1–29): Minimal platform-agnostic HAL traits:
    - `SpiWrite`: `write_byte(&mut self, byte: u8)`, `write_bytes(&mut self, bytes: &[u8])`, `write_repeated(&mut self, byte: u8, count: usize)`.
    - `PinWrite`: `set_high(&mut self)`, `set_low(&mut self)`.
    - `DelayMs`: `delay_ms(&mut self, ms: u16)`.
  - `src/display.rs` (lines 1–246): Implements `Ili9488<SPI, CS, DC, RST>` for 480x320 landscape display.
    - Uses standard MIPI DCS commands: `0x2A` (CASET), `0x2B` (PASET), `0x2C` (RAMWR), `0x36` (MADCTL = `0xA8`: MV | MY | BGR), `0x3A` (COLMOD = `0x66`: 18-bit RGB666, 3 bytes per pixel).
    - `Color` struct contains `r: u8, g: u8, b: u8`.
    - Drawing primitives: `fill_rect`, `draw_pixel`, `draw_hline`, `draw_vline`, `draw_rect`, `clear`.
  - `src/font.rs` (lines 1–161):
    - Static ASCII 5x7 font table `FONT_5X7: [[u8; 5]; 95]` (line 9).
    - Character renderer `draw_char` (lines 118–144): loops over 5 columns and 7 rows, invoking `display.fill_rect` for every single cell (36 calls to `fill_rect` per character, each call issuing separate CS toggle and 11 command bytes).
  - `src/ui.rs` (lines 1–261):
    - Layout: Two vertical panels ("Left Panel: CPU & Memory", "Right Panel: GPU & Graphics", plus a top header "SYSTEM TELEMETRY MONITOR LIVE" and info box "NVIDIA RTX 4050").
    - Redraw engine: `Dashboard::update` compares `last_packet` to new `packet` field by field. When dirty, calls `update_gauge`, which clears a fixed 60x16 box with `fill_rect` and draws scale-1 5x7 font, and fills bar from 0 to `fill_w`.
- `software/gadget-firmware-uno`:
  - `.cargo/config.toml` (lines 1–10): Target `avr-none`, `rustflags = ["-C", "target-cpu=atmega328p"]`, runner `ravedude`, `unstable.build-std = ["core"]`.
  - `Cargo.toml` (lines 1–41): Depends on `arduino-hal` (git revision `e5c8f37f...`), `gadget-core`, `gadget-common`, `ufmt`, `nb`, `panic-halt`. Profile `release` has `opt-level = "s"`, `lto = true`, `codegen-units = 1`.
  - `src/main.rs` (lines 1–132):
    - Configures hardware SPI at 8 MHz (`spi::SerialClockRate::OscfOver2`).
    - Adapts Arduino pins: CS on D10, DC on D9, RST on D8.
    - Implements non-blocking USART RX loop at 57,600 baud for 8-byte `TelemetryPacket` with framing header `0xAA 0x55`.
- `software/gadget-common`:
  - `src/lib.rs` (lines 1–64): Defines `TelemetryPacket` (8 bytes total: `MAGIC_0 0xAA`, `MAGIC_1 0x55`, `cpu_percent`, `cpu_temp_c`, `ram_percent`, `gpu_percent`, `gpu_temp_c`, `battery_percent`).
- `software/gadget-host`:
  - `src/main.rs` (lines 1–245): Laptop daemon querying Linux `/proc/stat` (CPU), `/proc/meminfo` (RAM), `/sys/class/hwmon` (CPU temp), and `nvidia-smi` / drm sysfs (GPU load & GPU temp). Streams 8-byte packets at 1000ms intervals over serial port.

### 1.2 Toolchain & Build Verification
Commands executed and results:
- `rustc --version`: `rustc 1.96.0 (ac68faa20 2026-05-25)`
- `cargo +nightly --version`: `cargo 1.100.0-nightly (495c385d0 2026-09-16)`
- `which avr-size avr-gcc ravedude`:
  - `/usr/bin/avr-size`
  - `/usr/bin/avr-gcc`
  - `/home/mahdi/.cargo/bin/ravedude`
- Build command: `cargo +nightly build --release` in `software/gadget-firmware-uno`:
  - Result: Success (0 warnings, 0 errors, finished in 21.56s).
  - Output binary: `software/gadget-firmware-uno/target/avr-none/release/gadget-firmware-uno.elf`.

### 1.3 Memory Footprint Measurements
Executed command:
`avr-size -C --mcu=atmega328p software/gadget-firmware-uno/target/avr-none/release/gadget-firmware-uno.elf`
Verbatim output:
```text
AVR Memory Usage
----------------
Device: atmega328p

Program:    8856 bytes (27.0% Full)
(.text + .data + .bootloader)

Data:        983 bytes (48.0% Full)
(.data + .bss + .noinit)
```

Detailed section breakdown (`avr-size -A` and `avr-objdump -t`):
- `.text`: 7,874 bytes (Flash instructions)
- `.data`: 982 bytes (Static data in SRAM loaded from Flash at startup)
- `.bss`: 1 byte (`008004d6 00000001 B DEVICE_PERIPHERALS`)
- Total Flash: 7,874 + 982 = 8,856 bytes (Ceiling: 28,672 bytes / 28 KB. Current usage is 30.9%).
- Total Static SRAM: 982 (.data) + 1 (.bss) = 983 bytes (Ceiling: 100 bytes. Current usage violates requirement by 883 bytes!).

### 1.4 Detailed SRAM Content Disassembly
Disassembly of symbols linked into `.data` (`avr-objdump -s -j .data` and `avr-nm -S`):
1. `_RNvNtCslc2XTLF6XHm_11gadget_core4font8FONT_5X7`: 475 bytes (0x1db)
   - Location: `software/gadget-core/src/font.rs:9`
   - Cause: `pub static FONT_5X7: [[u8; 5]; 95]` static array.
2. `anon.ca5ba2dec42ec402aac11eec41e77a9b.211`: 256 bytes (0x100)
   - Location: Pulled by `core::str::from_utf8(&buf[..len])` in `software/gadget-core/src/ui.rs:203`.
   - Cause: Standard library UTF-8 validation lookup table.
3. String Literals: ~250 bytes
   - In `software/gadget-core/src/ui.rs`: `"SYSTEM TELEMETRY MONITOR"`, `"LIVE"`, `"[ CPU & MEMORY ]"`, `"[ GPU & GRAPHICS ]"`, `"CPU LOAD"`, `"CPU TEMP"`, `"GPU LOAD"`, `"GPU TEMP"`, `"RAM USAGE"`, `"BATTERY"`, `"DEVICE HARDWARE: NVIDIA RTX 4050"`, `"THERMAL STATUS:"`, `"! CRITICAL HOT !"`, `"HIGH TEMPERATURE"`, `"COOL & NORMAL"`.
   - In `software/gadget-firmware-uno/src/main.rs`: `"GADGET_READY\n"`, `"ACK\n"`.

---

## 2. Logic Chain

### 2.1 Why Data is 983 Bytes and How to Reach < 100 Bytes Static SRAM
1. **Observation 1.3 & 1.4**: GNU ld for AVR links all `.rodata` sections directly into `.data` in SRAM (`*(.rodata*)` inside `.data` in the default linker script), because standard 16-bit pointers in Rust/C dereference data using SRAM memory load instructions (`ld`/`ldd`). Only `.progmem` sections reside solely in Flash and require the `lpm` assembly instruction.
2. **Observation 1.4**: The 982 bytes in `.data` consist entirely of read-only constants:
   - 475 bytes for `FONT_5X7`
   - 256 bytes for `core::str::from_utf8` validation table
   - ~250 bytes of string literals from the obsolete 2-column UI
   - Dynamic/mutable SRAM is only 1 byte (`DEVICE_PERIPHERALS` in `.bss`).
3. **Logic**:
   - Eliminating `core::str::from_utf8` by working directly with ASCII byte slices `&[u8]` removes 256 bytes immediately.
   - Replacing the static 95-character `FONT_5X7` with a bespoke 7-segment / chunky numeral generator for big numerals (which uses only a 10-byte segment mask `[u8; 10]`) removes 465 bytes.
   - Replacing long string literals with short quadrant labels (`b"CPU"`, `b"GPU"`, `b"RAM"`, `b"TMP"`, `b"%"`, `b"C"`) eliminates over 220 bytes.
   - Summing remaining static SRAM:
     - 10 bytes: 7-segment lookup mask
     - ~20 bytes: Quadrant label string bytes
     - ~17 bytes: Serial strings (`GADGET_READY`, `ACK`)
     - 1 byte: `.bss` peripheral singleton
     - **Projected Static SRAM: ~48 bytes**, well below the 100-byte ceiling!

### 2.2 Display Driver Timing & Differential Redraw Bottleneck
1. **Observation 1.1**: The display operates at 480x320 resolution with 18-bit color (3 bytes per pixel) over an 8 MHz SPI bus.
2. **Calculation**:
   - 1 full frame = 480 * 320 = 153,600 pixels.
   - At 3 bytes/pixel = 460,800 bytes.
   - At 8 MHz SPI (1 byte per 1 µs) = 460.8 ms (~2.17 frames per second).
3. **Inference**: Any full screen clear or card-level clear causes severe, visible tearing (half a second wipe). Zero-flicker can ONLY be achieved by restricting redraws to tight dirty bounding boxes.
4. **Current Inefficiency**:
   - In `font.rs:118-144`, `draw_char` calls `fill_rect` 36 times per character. For a 3-digit number scaled to arm's-length size (scale 4, ~28px tall), this incurs 108 separate SPI window transactions (each sending 11 command bytes + CS toggling).
   - In `ui.rs:216-220`, the bar fill is redrawn completely from 0 to `fill_w` on every update, rather than only filling or clearing the incremental delta `|fill_w_new - fill_w_old|`.
5. **Architectural Fix**:
   - Big numerals rendered via 7-segment geometric bars require only 1 bounding box clear + up to 6 segment fills per digit (total ~7 transactions vs 36).
   - Bar updates should only touch the delta between `old_fill_w` and `new_fill_w` (unless crossing a color-shift threshold, where the bar is recolored).

---

## 3. Gap Analysis & Proposed Architectural Blueprint

| Requirement | Current State | Required Architecture / Changes | Target File(s) |
|---|---|---|---|
| **R1: 4-Quadrant Layout** | 2 vertical panels + top header bar + device info card (225x260 each). Tiny crowded layout. | Divide 480x320 into 4 distinct cards (~230x146 each): Q1 (Top-Left): CPU Load (%), Q2 (Top-Right): GPU Load (%), Q3 (Bottom-Left): RAM Usage (%), Q4 (Bottom-Right): Thermals (CPU & GPU in °C with peak highlight). | `software/gadget-core/src/ui.rs` |
| **R2: Arm's-Length Typography** | 5x7 bitmap font rendered at scale 1 (5x7px, ~6px wide, unreadable past 20cm). | Primary readings rendered with bold, prominent numerals (32–34px tall) readable at 60–90cm desk distance. Bespoke 7-segment / chunky block glyph engine. | `software/gadget-core/src/font.rs` or `src/numeral.rs` |
| **R3: Dynamic Color Coding & Chunky Meters** | Continuous thin 10px bar with generic green/yellow/red palette. | - CPU: Electric Cyan (`#00D2D3`) → Alert Coral (`#FF6B6B`)<br>- GPU: Neon Green (`#10AC84`) → Warning Orange (`#FF9F43`)<br>- RAM: Vivid Violet (`#A55EEA`) → Danger Red (`#EB3B5A`)<br>- Thermals: Mint (`<60°C`) → Gold (`60–75°C`) → Crimson (`>75°C`). Chunky 14–16px segmented or bold track. | `software/gadget-core/src/display.rs`, `src/ui.rs` |
| **R4: Differential Redraw & Zero-Heap** | Zero heap maintained, but redraws entire bar and makes 36 SPI window calls per char. Static SRAM is 983B (fails 100B ceiling). | - Eliminate `core::str::from_utf8` (saves 256B).<br>- Replace static `FONT_5X7` with 10-byte segment mask + minimal ASCII byte table.<br>- Differential dirty update: only clear/fill changed digit boxes and bar deltas.<br>- Result: Static SRAM < 50B, Flash < 10KB. | `software/gadget-core/src/ui.rs`, `src/font.rs` |
| **R5: HAL Portability & Host Telemetry** | Trait boundaries (`SpiWrite`, `PinWrite`, `DelayMs`) clean and agnostic. Host queries `/proc/stat`, `/proc/meminfo`, `hwmon`, `nvidia-smi`. | Retain `embedded-hal` trait abstraction in `gadget-core`. `TelemetryPacket` in `gadget-common` already has all 5 required fields (`cpu_percent`, `gpu_percent`, `ram_percent`, `cpu_temp_c`, `gpu_temp_c`). 100% compatible. | `software/gadget-common/src/lib.rs`, `software/gadget-host/src/main.rs` |

### Detailed Layout Geometry Specification (480x320)
- Screen bounds: X: 0..480, Y: 0..320
- Margins: Left/Right = 6px, Top/Bottom = 8px
- Gutters: Center horizontal gap = 8px, Center vertical gap = 10px
- Card Dimensions: Width = 230px, Height = 147px
  - **Quadrant 1 (Top-Left, CPU)**: `x: 6, y: 8, w: 230, h: 147`
  - **Quadrant 2 (Top-Right, GPU)**: `x: 244, y: 8, w: 230, h: 147`
  - **Quadrant 3 (Bottom-Left, RAM)**: `x: 6, y: 165, w: 230, h: 147`
  - **Quadrant 4 (Bottom-Right, Thermals)**: `x: 244, y: 165, w: 230, h: 147`
- Card Internals:
  - Header Label: `y + 8`, height 10px (e.g., "CPU LOAD", "GPU LOAD", "RAM USAGE", "THERMALS")
  - Big Numerals: `y + 26`, height 34px, width ~70px (e.g., 3 digits of 20px width + 4px spacing).
  - Unit Symbol: `y + 36`, `%` or `°C`
  - Chunky Meter Track: `y + 112`, width 206px, height 16px (segmented into 12–15 blocks or bold bar).

---

## 4. Caveats
1. **Target Hardware Verification**: Code build and binary analysis were performed on the actual host compiler toolchain with `cargo +nightly` targeting `avr-none` (`atmega328p`), but physical display hardware was not connected during this read-only survey.
2. **Display Controller Compatibility**: The driver in `gadget-core/src/display.rs` is titled `Ili9488`. ST7796S and ILI9488 share standard MIPI DCS commands (`0x2A`, `0x2B`, `0x2C`, `0x36`, `0x3A`), but ST7796S supports 16-bit RGB565 over SPI while ILI9488 silicon errata mandates 18-bit RGB666 (3 bytes/pixel). The current driver is verified for ILI9488 18-bit mode. If an ST7796 display is used in 18-bit mode (`COLMOD = 0x66`), it behaves identically.
3. **Companion Pet Module**: `software/gadget-core/src/pet.rs` is currently present in the codebase but unlinked in `src/lib.rs`. It does not contribute to the binary footprint. If restored in the future, it should reside in flash.

---

## 5. Conclusion & Actionable Recommendations
1. **Feasibility**: All user requirements (R1–R5) are completely feasible within the ATmega328P hardware limits (28 KB Flash, 2 KB total SRAM).
2. **Root Cause of Memory Ceiling Violation**: The current 983-byte static SRAM footprint is caused by constant font tables and UTF-8 decode tables leaking into SRAM via GNU ld's `.rodata` mapping. There is virtually zero dynamic SRAM usage (1 byte `.bss`).
3. **Exact Redesign Path for Implementer**:
   - In `gadget-core/src/font.rs` (or a dedicated `numeral.rs`): Implement a 7-segment / chunky numeral renderer (`draw_big_digit`, height 32–34px) driven by a 10-byte segment mask. Eliminate `FONT_5X7` static array from SRAM.
   - In `gadget-core/src/ui.rs`:
     - Eliminate `core::str::from_utf8`. Replace with raw ASCII byte formatting into stack buffers (`[u8; 4]`).
     - Restructure `draw_layout` and `update` to implement the 4-Quadrant card grid.
     - Implement delta-only dirty bounding box clearing for numerals and chunky meters.
     - Apply dynamic color transitions: Cyan `#00D2D3` → Coral `#FF6B6B`, Green `#10AC84` → Orange `#FF9F43`, Violet `#A55EEA` → Red `#EB3B5A`, Mint `#2ED573` → Gold `#FED330` → Crimson `#FF3838`.
   - In `gadget-firmware-uno`: Verify with `avr-size` that Flash remains < 28 KB and Data drops to < 60 bytes.

---

## 6. Verification Method

### 6.1 Firmware Build & Size Check
Run the following commands in `software/gadget-firmware-uno`:
```bash
cd software/gadget-firmware-uno
cargo +nightly build --release
avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
```
**Verification Criteria**:
- Build exits with code 0.
- Program (.text + .data) <= 28672 bytes (28 KB).
- Data (.data + .bss) < 100 bytes.

### 6.2 Host Daemon Build & Test Check
Run the following commands in `software/gadget-host`:
```bash
cd software/gadget-host
cargo build
cargo test
cargo run -- --dry-run
```
**Verification Criteria**:
- Build and tests exit with code 0.
- `--dry-run` prints live telemetry samples (`CPU`, `GPU`, `RAM`, `Temp`) accurately without panics.

### 6.3 Host Verification of Core Crate
Run the following commands in `software/gadget-core`:
```bash
cd software/gadget-core
cargo test
```
**Verification Criteria**:
- Compiles on host without AVR dependencies (`no_std` clean).
