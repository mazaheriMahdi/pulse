# Project: Desktop Performance Monitor 4-Quadrant Big Block UI/UX

## Architecture
The system consists of four primary software components:
1. **`software/gadget-core`**: Platform-agnostic `#![no_std]` UI rendering and differential redraw engine. Provides 4-quadrant cards, arm's-length typography (>=28–36px tall numerals), chunky visual meters, dynamic color coding, and bounding-box dirty updates over generic `embedded-hal` SPI/Pin traits.
2. **`software/gadget-firmware-uno`**: Target firmware for Arduino Uno (Microchip ATmega328P, 16MHz, 2KB SRAM). Configures 8MHz SPI, ILI9488/ST7796 display, UART receiver at 57,600 baud, non-blocking packet stream, strictly zero-heap execution, with flash ceiling < 28 KB and static SRAM ceiling < 100 bytes.
3. **`software/gadget-common`**: Shared `#![no_std]` telemetry data structures, serialization, and packet framing (`MAGIC_0 0xAA`, `MAGIC_1 0x55`, 6 metric payload bytes).
4. **`software/gadget-host`**: Linux laptop background daemon collecting telemetry from `/proc/stat`, `/proc/meminfo`, AMD `k10temp`/Intel `coretemp`, and `nvidia-smi` / AMD DRM sysfs, transmitting 8-byte frames over serial.

Data Flow:
`Linux Kernel / GPUs` -> `gadget-host` -> `Serial UART (57600 baud, 8-byte TelemetryPacket)` -> `gadget-firmware-uno` -> `gadget-core Dashboard` -> `8MHz SPI Differential Bounding Boxes` -> `3.5" 480x320 TFT Display`.

## Code Layout
- `software/gadget-common/src/lib.rs`: TelemetryPacket wire format and codecs. Owned by M3.
- `software/gadget-core/src/lib.rs`: Module exports and crate root. Owned by M1.
- `software/gadget-core/src/traits.rs`: SPI and Pin abstractions. Owned by M1.
- `software/gadget-core/src/display.rs`: Display driver, colors, and low-level window primitives. Owned by M2.
- `software/gadget-core/src/font.rs` / `src/numeral.rs`: High-legibility big numeral engine (>=28–36px) and SRAM reduction. Owned by M1.
- `software/gadget-core/src/ui.rs`: 4-Quadrant card grid, chunky meters, thermals peak badge, and differential redraw engine. Owned by M2.
- `software/gadget-firmware-uno/src/main.rs`: ATmega328P entrypoint, SPI/UART initialization, and main loop. Owned by M4.
- `software/gadget-host/src/main.rs`: Linux telemetry samplers and serial writer. Owned by M3.
- `tests/e2e/`: Requirement-driven opaque-box E2E test suite and runner. Owned by E2E Testing Track.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | 4-Quadrant Card Grid | Divide 480x320 landscape into 4 symmetric 230x145px cards with 2px borders | M2 | Survey / R1 |
| 2 | Card Header Bar | Header label in each card with quadrant metric title in accent color | M2 | Survey / R1 |
| 3 | Big Block Numerals | Prominent numerals >= 28–36px tall for all primary readings | M1 | Survey / R2 |
| 4 | Arm's-Length Legibility | Optical angle >= 20 arcminutes for 60–90cm desk viewing, eliminate sub-14px primary text | M1 | Survey / R2 |
| 5 | Chunky Visual Meters | Bold 20–24px high progress track with dynamic fill | M2 | Survey / R3 |
| 6 | Dynamic CPU Palette | Electric Cyan (`#00D2D3`) transitioning to Alert Coral (`#FF6B6B`) | M2 | Survey / R3 |
| 7 | Dynamic GPU Palette | Neon Green (`#10AC84`) transitioning to Warning Orange (`#FF9F43`) | M2 | Survey / R3 |
| 8 | Dynamic RAM Palette | Vivid Violet (`#A55EEA`) transitioning to Danger Red (`#EA2027`) | M2 | Survey / R3 |
| 9 | Dynamic Thermal Palette | Cool Mint (<60°C) -> Gold (60–75°C) -> Crimson (>75°C) | M2 | Survey / R3 |
| 10 | Dual Temp & Peak Highlight | Simultaneous CPU & GPU temp display with high-contrast `[PEAK]` highlight | M2 | Survey / R1, R3 |
| 11 | Differential Redraw Engine | Dirty bounding-box updates for numerals and meter deltas over 8MHz SPI | M2 | Survey / R4 |
| 12 | Zero-Flicker Execution | Eradicate full-screen clears during telemetry update loop | M2 | Survey / R4 |
| 13 | Zero-Heap Architecture | `#![no_std]` execution with zero dynamic allocation | M4 | Survey / R4 |
| 14 | Static SRAM Ceiling | Reduce static RAM to < 100 bytes on ATmega328P by eliminating SRAM font table | M1, M4 | Survey / R4 |
| 15 | Flash Ceiling (<28KB) | Constrain compiled AVR binary size to < 28 KB | M4 | Survey / R4 |
| 16 | Serial Packet Protocol | 8-byte framed packet (`0xAA 0x55` + 6 metrics) with validation | M3 | Survey / R5 |
| 17 | Host Hardware Telemetry | Linux host sampling procfs, AMD k10temp, and nvidia-smi with robust fallbacks | M3 | Survey / R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Typography & SRAM Reduction | Big numerals (>=28–36px), eliminate SRAM font table & UTF-8 table, arm's-length legibility | none | IN_PROGRESS |
| M2 | 4-Quadrant UI & Differential Redraw | 4 symmetric cards, chunky meters, dynamic palettes, dual thermals + peak badge, zero-flicker redraw | M1 | PLANNED |
| M3 | Host Telemetry & Common Protocol | Serialization unit tests, k10temp priority, amdgpu hwmon, port fallback, remove unused deps | none | IN_PROGRESS |
| M4 | Firmware Integration & Resource Ceilings | ATmega328P firmware integration, verify < 28KB Flash, < 100B SRAM via avr-size, zero-heap | M2, M3 | PLANNED |
| M5 | Final E2E Test Pass & Adversarial Hardening | Phase 1: 100% pass of E2E test suite (Tiers 1-4). Phase 2: Tier 5 adversarial stress testing | M4, E2E | PLANNED |

## Parallel Track: E2E Testing Track
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | Opaque-Box E2E Test Suite | Test runner, Tiers 1-4 test cases covering all 17 features, publishes TEST_READY.md | none | IN_PROGRESS |

## Interface Contracts

### `gadget-common` ↔ `gadget-host` & `gadget-firmware-uno`
- Wire format: Fixed 8-byte frame:
  - Byte 0: `0xAA` (MAGIC_0)
  - Byte 1: `0x55` (MAGIC_1)
  - Byte 2: `cpu_percent` (0..100)
  - Byte 3: `cpu_temp_c` (0..255 °C)
  - Byte 4: `ram_percent` (0..100)
  - Byte 5: `gpu_percent` (0..100)
  - Byte 6: `gpu_temp_c` (0..255 °C)
  - Byte 7: `battery_percent` (0..100)
- Endianness: Single-byte fields, no multi-byte endianness dependencies.

### `gadget-core` ↔ `gadget-firmware-uno`
- `Dashboard::new() -> Dashboard`
- `Dashboard::draw_layout<D: Display>(&mut self, display: &mut D)`: Draws static cards, borders, labels once.
- `Dashboard::update<D: Display>(&mut self, display: &mut D, packet: TelemetryPacket)`: Differential dirty redraw only. Does NOT call `display.clear()`.
- Big numeral rendering: Height >= 28–36px. Does not allocate heap.
