# Test Infrastructure Specification: Opaque-Box E2E Testing Framework

## 1. Overview & Architectural Principles

### 1.1 Purpose & Scope
This document specifies the architecture, contracts, test harness designs, and execution mechanics for the end-to-end (E2E) testing framework of the Desktop Performance Monitor gadget. The E2E test suite validates all requirements specified in `ORIGINAL_REQUEST.md` (R1–R5) and the 17 core features cataloged in `PROJECT.md` across four software components:
1. `software/gadget-core`: Platform-agnostic `#![no_std]` UI rendering and differential redraw engine.
2. `software/gadget-firmware-uno`: Microchip ATmega328P target firmware (16MHz, 2KB SRAM, 32KB Flash).
3. `software/gadget-common`: `#![no_std]` wire protocol serialization and 8-byte packet framing.
4. `software/gadget-host`: Linux host daemon sampling `/proc/stat`, `/proc/meminfo`, `k10temp`, and `nvidia-smi`.

### 1.2 Opaque-Box Verification Principles
The testing framework operates on opaque-box principles:
- **Contract-Driven**: Verification strictly validates external inputs, outputs, observable bus transactions, and resource bounds rather than internal struct fields or private helper functions.
- **Trait-Based Decoupling**: Hardware dependencies (SPI bus, GPIO pins, UART) are decoupled via headless simulation models adhering to `embedded-hal` trait interfaces.
- **Progressive Testability**: Tests evaluate specifications deterministically without requiring a physically wired Arduino Uno or TFT LCD screen.
- **Mathematical Exactness**: Geometric card dimensions, visual angles (ISO 9241-303), color transitions, and baud rate timings are mathematically derived and explicitly asserted.

### 1.3 Target Hardware & Simulation Matrix
| Component | Physical Target | Headless Verification Vehicle | Observable Contracts |
|---|---|---|---|
| Display Driver & UI | 3.5" ILI9488 TFT (480x320, 18-bit RGB666) | `DisplayHarness` (virtual framebuffer & DCS decoder) | SPI window commands (`0x2A`, `0x2B`, `0x2C`), RGB pixel buffer, dirty bounding boxes |
| Telemetry Protocol | UART at 57,600 baud, 8-byte frames | `ProtocolHarness` (sliding window stream decoder) | `0xAA 0x55` header, 6 metric payload bytes, ACK responses, sync recovery |
| Host Daemon | Linux PC (`/proc`, `sysfs`, `nvidia-smi`) | `HostHarness` (CLI subprocess & sysfs mock runner) | CLI arguments (`--dry-run`, `--interval-ms`), regex stdout parsing, error recovery |
| Firmware Binary | ATmega328P (32KB Flash, 2KB SRAM) | `FirmwareHarness` (`avr-size`, `avr-nm` analyzer) | Flash < 28 KB, static SRAM <= 100 B, zero heap symbols |

---

## 2. Directory Layout & Module Structure

### 2.1 Directory Tree
```
tests/e2e/
├── run_tests.sh                 # Executable bash test runner script
├── test_runner.py               # Standalone Python 3 test runner (zero pip dependencies)
├── harnesses/                   # Four specialized opaque-box harnesses
│   ├── __init__.py
│   ├── host_harness.py          # Host CLI & telemetry execution harness
│   ├── protocol_harness.py      # Wire protocol & UART framing harness
│   ├── display_harness.py       # Headless MIPI DCS display driver & 480x320 framebuffer simulator
│   └── firmware_harness.py      # AVR ELF size and zero-heap symbol analyzer
├── tier1_feature_tests.py       # Tier 1: Feature Coverage (85 test cases: T1-F01-01 to T1-F17-05)
├── tier2_boundary_tests.py      # Tier 2: Boundary & Corner Cases (85 test cases: T2-F01-01 to T2-F17-05)
├── tier3_interaction_tests.py   # Tier 3: Cross-Feature Interactions (18 test cases: T3-INT-01 to T3-INT-18)
└── tier4_workload_tests.py      # Tier 4: Real-World Workload Scenarios (9 test cases: T4-APP-01 to T4-APP-09)
```

### 2.2 Ownership & Separation of Concerns
- `harnesses/`: Reusable interface abstractions wrapping subprocesses, protocol codecs, geometric calculations, and symbol inspectors.
- `tier1_feature_tests.py`: Exhaustive functional verification of happy-path behavior across all 17 features.
- `tier2_boundary_tests.py`: Stress testing of extremes, threshold crossings, noise injection, and corner cases.
- `tier3_interaction_tests.py`: Pairwise and multi-feature interaction verification under constraint coupling.
- `tier4_workload_tests.py`: Temporal lifecycle scenarios modeling authentic user desktop workloads.
- `test_runner.py`: Central test execution engine providing CLI parsing, test discovery, per-tier tracking, and ANSI tabular reporting.

---

## 3. Test Harness Architecture

### 3.1 Host Telemetry Harness (`HostHarness`)
The `HostHarness` (`tests/e2e/harnesses/host_harness.py`) manages the execution and verification of `software/gadget-host`:
- **CLI Verification**: Executes `gadget-host --help` and `gadget-host --version`, asserting exit code 0 and presence of flags (`--port`, `--baud`, `--interval-ms`, `--dry-run`).
- **Telemetry Stream Ingestion**: Executes `gadget-host --dry-run` and captures stdout, parsing telemetry metric strings via regular expressions:
  `r"\[Metrics\] CPU:\s*(\d+)%\s*\((\d+)°C\)\s*\|\s*GPU:\s*(\d+)%\s*\((\d+)°C\)\s*\|\s*RAM:\s*(\d+)%\s*\|\s*Bat:\s*(\d+)%"`
- **Procfs & Sysfs Emulation**: Tests CPU utilization computation `(delta_total - delta_idle) / delta_total * 100`, handling division-by-zero protection (`delta_total == 0`), RAM parsing from `/proc/meminfo`, driver priority (`k10temp`/`coretemp` over `acpitz`), and `nvidia-smi` CSV parsing.
- **Port Fallback**: Tests non-fatal fallback behavior when a specified serial port does not exist.

### 3.2 Wire Protocol Harness (`ProtocolHarness`)
The `ProtocolHarness` (`tests/e2e/harnesses/protocol_harness.py`) validates binary serialization and USART framing:
- **Constants**: Verifies `MAGIC_0 == 0xAA` (170), `MAGIC_1 == 0x55` (85), and `PACKET_LEN == 8`.
- **Codec Roundtrip**: Encodes `(cpu, cpu_temp, ram, gpu, gpu_temp, bat)` into 8-byte frames and decodes back with 100% field fidelity.
- **Range Clamping**: Enforces percentage clamping to `100%` for `cpu_percent`, `ram_percent`, `gpu_percent`, `battery_percent`, while leaving temperatures unclamped.
- **UART Sliding Window State Machine**: Faithfully replicates the non-blocking state machine in `gadget-firmware-uno/src/main.rs:90–130`:
  - `rx_idx == 0`: waits for `0xAA`.
  - `rx_idx == 1`: if `0x55` advances to 2; if `0xAA` remains 1; else resets to 0.
  - `rx_idx >= 2`: reads remaining 6 bytes, decodes packet upon reaching length 8, and resets index to 0.
- **Noise Immunity**: Evaluates header corruption (`0xAA 0x54`, `0xAB 0x55`), false magic embedded in payload, fragmented byte streams, and sync recovery.

### 3.3 Headless Display & Redraw Harness (`DisplayHarness`)
The `DisplayHarness` (`tests/e2e/harnesses/display_harness.py`) simulates the ILI9488 MIPI DCS display controller and 480x320 framebuffer:
- **DCS Command Interpreter**: Captures `0x2A` (CASET: $X_0 \dots X_1$), `0x2B` (PASET: $Y_0 \dots Y_1$), and `0x2C` (RAMWR), rasterizing RGB pixels into a virtual $480 \times 320$ framebuffer matrix.
- **Layout Geometry**: Validates the 4-quadrant layout:
  - Screen dimensions: $480 \times 320\text{ px}$.
  - Margins: $X = 7\text{ px}$, $Y = 10\text{ px}$. Center gutters: $X = 6\text{ px}$, $Y = 10\text{ px}$.
  - Card bounding boxes: Exactly $230 \times 145\text{ px}$ each:
    - Q1 (CPU): Origin $(7, 10)$, Extent $(236, 154)$.
    - Q2 (GPU): Origin $(243, 10)$, Extent $(472, 154)$.
    - Q3 (RAM): Origin $(7, 165)$, Extent $(236, 309)$.
    - Q4 (Thermals): Origin $(243, 165)$, Extent $(472, 309)$.
- **Typography & Ergonomics (ISO 9241-303)**:
  - Pixel pitch = $0.153\text{ mm/pixel}$ (3.5" display).
  - Asserts big numerals $\ge 28\text{ px}$ and $\le 36\text{ px}$.
  - Visual angle formula: $\theta = 2 \cdot \arctan\left(\frac{h_{\text{mm}}}{2 \cdot D_{\text{mm}}}\right) \cdot \frac{180 \cdot 60}{\pi} \ge 20\text{ arcminutes}$ at $60\dots 90\text{ cm}$.
  - Asserts zero sub-14px text on primary readings.
- **Chunky Meters**:
  - Track dimensions: Outer $202 \times 24\text{ px}$, Inner fill $200 \times 22\text{ px}$.
  - Fill ratio: Exactly $2\text{ px}$ per $1\%$ load ($\text{fill\_w} = 2 \cdot \text{clamp}(V, 0, 100)$).
- **Dynamic Palettes**:
  - CPU: $<60\%$ Electric Cyan (`#00D2D3`) $\to 60–84\%$ Coral Amber (`#FFA502`) $\to \ge 85\%$ Alert Coral (`#FF6B6B`).
  - GPU: $<65\%$ Neon Green (`#10AC84`) $\to 65–84\%$ Warning Orange (`#FF9F43`) $\to \ge 85\%$ Blaze Red (`#FF3838`).
  - RAM: $<70\%$ Vivid Violet (`#A55EEA`) $\to 70–84\%$ Magenta Rose (`#D980FA`) $\to \ge 85\%$ Danger Red (`#EA2027`).
  - Thermals: $<60^\circ\text{C}$ Cool Mint (`#1DD1A1`) $\to 60–75^\circ\text{C}$ Gold (`#FECA57`) $\to >75^\circ\text{C}$ Crimson (`#FF3838`).
- **Thermals & Peak Highlight**:
  - Simultaneous CPU and GPU temperature display in Q4.
  - $\max(\text{cpu\_temp}, \text{gpu\_temp})$ receives `[PEAK]` highlight. Non-peak rendered in `TEXT_MUTED` (`#8291AF`).
  - If peak $> 75^\circ\text{C}$, Q4 card border dynamically turns Crimson (`#FF3838`).
- **Differential Redraw & Zero-Flicker**:
  - Tracks total full screen clears: `assert display.clear_count == 0` during updates.
  - Verifies zero SPI transactions on identical consecutive frames ($\Delta == 0 \implies 0\text{ bytes}$).
  - Verifies single-metric updates are strictly confined to the dirty quadrant bounding box.
  - Verifies worst-case multi-quadrant update completes under $35,000\text{ bytes}$ ($< 45\text{ ms}$ at 8MHz SPI).

### 3.4 Firmware Resource Ceiling Harness (`FirmwareHarness`)
The `FirmwareHarness` (`tests/e2e/harnesses/firmware_harness.py`) audits the compiled AVR ELF binary (`gadget-firmware-uno.elf`) using host toolchains:
- **Flash Ceiling**: Invokes `avr-size -A` to verify Program size ($\text{.text} + \text{.data}$) $< 28,672\text{ bytes}$ ($28\text{ KB}$).
- **Static SRAM Ceiling**: Audits section sizes ($\text{.data} + \text{.bss}$), verifying static variable footprint <= 100 bytes and `.bss` <= 20 bytes.
- **Zero-Heap Audit**: Invokes `avr-nm -C` to verify complete absence of dynamic memory allocation symbols (`malloc`, `free`, `realloc`, `calloc`, `__rust_alloc`, `__rust_dealloc`).
- **`#![no_std]` Verification**: Verifies `#![no_std]` crate-level declarations in `gadget-core`, `gadget-common`, and `gadget-firmware-uno`.
- **Symbol Audit**: Asserts absence of unlinked companion modules (`pet.rs`) and verifies panic handler size minimization.

---

## 4. Test Tier Hierarchy & Catalog

```
========================================================================================
E2E TEST TIER ARCHITECTURE
========================================================================================
Tier     Category                       Count   Scope & Focus
----------------------------------------------------------------------------------------
Tier 1   Feature Coverage (F01–F17)        85   Happy-path coverage (5 tests × 17 features)
Tier 2   Boundary & Corner Cases (F01–F17) 85   Extremes, thresholds, noise (5 tests × 17 features)
Tier 3   Cross-Feature Interactions        18   Pairwise & multi-feature constraint coupling
Tier 4   Real-World Desktop Workloads       9   Temporal multi-step lifecycle scenarios
----------------------------------------------------------------------------------------
TOTAL                                     197   Comprehensive E2E Verification
========================================================================================
```

### 4.1 Feature Mapping Matrix (17 Features)
| Feature ID | Feature Name | Description | T1 Tests | T2 Tests | T3 Tests | T4 Tests | Total |
|---|---|---|---|---|---|---|---|
| F01 | 4-Quadrant Card Grid | 480x320 split into 4 230x145px cards, 2px borders | 5 | 5 | T3-INT-01, 05, 08, 13 | T4-APP-01 | 15 |
| F02 | Card Header Bar | Header label bar in accent color, 14px font | 5 | 5 | T3-INT-06, 13 | T4-APP-01 | 13 |
| F03 | Big Block Numerals | Numerals >= 28–36px tall for all primary readings | 5 | 5 | T3-INT-02, 06, 10, 14 | T4-APP-02..06 | 19 |
| F04 | Arm's-Length Legibility | Optical angle >= 20 arcmin at 60–90cm, no sub-14px | 5 | 5 | T3-INT-06 | T4-APP-02 | 12 |
| F05 | Chunky Visual Meters | Bold 20–24px high track, 200px fill, 1:2 scaling | 5 | 5 | T3-INT-05, 07, 12, 18 | T4-APP-01..06 | 19 |
| F06 | Dynamic CPU Palette | Cyan (`#00D2D3`) -> Amber -> Coral (`#FF6B6B`) | 5 | 5 | T3-INT-05, 16 | T4-APP-02, 03 | 14 |
| F07 | Dynamic GPU Palette | Green (`#10AC84`) -> Orange -> Blaze Red (`#FF3838`)| 5 | 5 | T3-INT-07, 16 | T4-APP-02, 04 | 14 |
| F08 | Dynamic RAM Palette | Violet (`#A55EEA`) -> Magenta -> Danger Red (`#EA2027`)| 5 | 5 | T3-INT-02, 12, 16 | T4-APP-02, 06 | 15 |
| F09 | Dynamic Thermal Palette | Mint (<60°C) -> Gold (60–75°C) -> Crimson (>75°C) | 5 | 5 | T3-INT-03, 08, 16 | T4-APP-02..05 | 16 |
| F10 | Dual Temp & Peak Highlight | Dual readouts with [PEAK] highlight & border alert| 5 | 5 | T3-INT-03, 08, 17 | T4-APP-03..05 | 15 |
| F11 | Differential Redraw Engine| Dirty bounding-box window updates over 8MHz SPI | 5 | 5 | T3-INT-01, 04, 07, 10..13, 15 | T4-APP-01..09 | 22 |
| F12 | Zero-Flicker Execution | Eradicate full clears during update, SPI < 50ms | 5 | 5 | T3-INT-03, 10, 13 | T4-APP-01..09 | 21 |
| F13 | Zero-Heap Architecture | `#![no_std]` execution with zero dynamic allocation| 5 | 5 | T3-INT-09, 18 | T4-APP-09 | 13 |
| F14 | Static SRAM Ceiling | Static RAM <= 100 bytes on ATmega328P | 5 | 5 | T3-INT-02, 09, 14 | T4-APP-09 | 14 |
| F15 | Flash Ceiling (<28KB) | Compiled binary size < 28 KB | 5 | 5 | T3-INT-14, 18 | T4-APP-09 | 13 |
| F16 | Serial Packet Protocol | 8-byte frame (`0xAA 0x55` + 6 bytes) with sync | 5 | 5 | T3-INT-04, 09, 11, 15 | T4-APP-07, 08 | 16 |
| F17 | Host Hardware Telemetry | Linux sysfs, procfs, k10temp, nvidia-smi collectors | 5 | 5 | T3-INT-04, 11, 17 | T4-APP-01, 07 | 15 |

---

## 5. Test Runner CLI Specification

### 5.1 CLI Arguments
```text
Usage: python3 tests/e2e/test_runner.py [OPTIONS]

Options:
  --tier <1-4>         Run specific tier or comma-separated tiers (e.g. --tier 1 or --tier 1,2,3,4)
  --feature <1-17>     Filter Tier 1 and Tier 2 tests by feature number (1..17)
  -v, --verbose        Display individual test names, execution timings, and detailed output
  -s, --summary        Display formatted execution summary table (default: enabled)
  -x, --fail-fast      Halt suite execution immediately upon first failure
  --json               Output test results as machine-readable JSON to stdout
  -h, --help           Display help message and exit
```

### 5.2 Terminal Reporting & Summary Table Design
The test runner outputs clean ANSI-formatted execution tables:
```text
========================================================================================
                      DESKTOP GADGET E2E TEST SUITE EXECUTION SUMMARY
========================================================================================
 Tier   Description                       Total    Passed    Failed   Skipped    Rate
----------------------------------------------------------------------------------------
 Tier 1 Feature Coverage (17 Features)       85        85         0         0   100.0%
 Tier 2 Boundary & Corner Cases              85        85         0         0   100.0%
 Tier 3 Cross-Feature Interactions           18        18         0         0   100.0%
 Tier 4 Real-World Workload Scenarios         9         9         0         0   100.0%
----------------------------------------------------------------------------------------
 TOTAL                                      197       197         0         0   100.0%
========================================================================================
 Status: ALL TIERS PASSED [197/197] (Elapsed: 1.84s)
```

### 5.3 Exit Codes & CI/CD Integration
- `0`: All selected tests executed and passed (100% success rate).
- `1`: One or more tests failed or encountered an unhandled exception.
- `2`: Invalid CLI invocation arguments or missing prerequisites.

---

## 6. Execution Prerequisites & Toolchain Dependencies

### 6.1 Toolchain Requirements
- Python: `python3 >= 3.10` (standard library only).
- Rust: `cargo` and `rustc` (`1.80+` stable and `nightly` for AVR).
- AVR Toolchain: `/usr/bin/avr-size`, `/usr/bin/avr-nm`, `/usr/bin/avr-gcc` (for firmware resource ceiling analysis).

### 6.2 Zero External Pip Dependencies Guarantee
The test suite and test runner depend exclusively on the Python standard library:
`sys`, `os`, `argparse`, `time`, `json`, `unittest`, `dataclasses`, `struct`, `re`, `subprocess`, `math`, `typing`.
Zero external pip packages (`pytest`, `requests`, etc.) are required, ensuring zero installation friction.

### 6.3 Standard Execution Commands
```bash
# Execute entire E2E test suite (197 tests)
python3 tests/e2e/test_runner.py --summary

# Or execute via executable bash script
./tests/e2e/run_tests.sh

# Run specific tiers
python3 tests/e2e/test_runner.py --tier 1
python3 tests/e2e/test_runner.py --tier 2
python3 tests/e2e/test_runner.py --tier 3,4 --verbose
```

---

## 7. Failure Invalidation & Forensic Diagnostic Procedures

### 7.1 Classification of Failures
1. **Layout / Geometry Violation**: Bounding boxes deviate from $230 \times 145\text{ px}$ or breach margins/gutters.
2. **Visual Ergonomics Violation**: Numeral height $< 28\text{ px}$ or optical angle $< 20\text{ arcminutes}$.
3. **Palette / Contrast Violation**: Color RGB values mismatch thresholds or WCAG AA contrast $< 4.5:1$.
4. **Zero-Flicker Violation**: `display.clear()` invoked during `Dashboard::update` or SPI payload $> 35\text{ KB}$.
5. **Resource Exhaustion**: Flash binary size $\ge 28\text{ KB}$, static SRAM $> 100\text{ bytes}$, or heap symbols detected.
6. **Protocol Synchronization Failure**: UART receiver fails to recover after packet corruption.

### 7.2 Forensic Triage Workflow
When a test failure occurs:
1. Re-run runner with `--verbose` and `--fail-fast` to isolate the exact assertion failure.
2. Inspect the failed test's component:
   - For UI / redraw failures: inspect virtual framebuffer dump and SPI command trace.
   - For wire protocol failures: inspect raw byte stream and receiver state machine transition logs.
   - For firmware resource failures: inspect `avr-size -A` and `avr-nm -S --size-sort` output.
3. Log findings and escalate implementation defects to the responsible component milestone owner.
