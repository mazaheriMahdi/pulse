# Architecture & Investigation Report: Opaque-Box E2E Test Suite & Test Runner

**Author**: Explorer E2E Infrastructure (`explorer_e2e_1`)  
**Parent Agent**: `sub_orch_e2e` (Conversation ID: `84adcafc-f5e3-46f8-89ac-821d86c446c2`)  
**Workspace**: `/home/mahdi/Programming/perfomance-monitor`  
**Working Directory**: `/home/mahdi/Programming/perfomance-monitor/.agents/explorer_e2e_1`  
**Date**: 2026-09-22T18:48:00Z  

---

## 1. Observation

Direct technical observations gathered from inspecting codebases, entry points, toolchains, build environments, and symbols across all four project components:

### 1.1 Host Daemon Entry Point (`software/gadget-host`)
- **Source File**: `software/gadget-host/src/main.rs` (lines 1–245).
- **CLI Options (`clap::Parser`, lines 9–27)**:
  - `-p, --port <PORT>`: Serial port connected to Arduino Uno (default: `/dev/ttyUSB0`).
  - `-b, --baud <BAUD>`: Baud rate (default: `57600`).
  - `-i, --interval-ms <INTERVAL_MS>`: Sampling interval in milliseconds (default: `1000`).
  - `--dry-run`: Boolean flag enabling mock simulation mode without serial port.
  - `-h, --help`: Generates usage documentation (exits with code 0).
  - `-V, --version`: Prints version (exits with code 0).
- **Execution & Fallback Logic (lines 135–167, 192–211)**:
  - Subprocess execution: `Command::new("nvidia-smi").args(["--query-gpu=utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"])`.
  - Parses comma-delimited output: `<util>, <temp>`, clamped via `util.min(100)`.
  - Fallback: Reads `/sys/class/drm/card0/device/gpu_busy_percent` or `card1`. Hardcodes temp to 50°C.
  - Telemetry streaming format (lines 228–232):
    `\r[Metrics] CPU: {:>3}% ({:>2}°C) | GPU: {:>3}% ({:>2}°C) | RAM: {:>3}% | Bat: {:>3}%`
  - Serial error recovery: If serial port opening fails, catches error, prints `Warning: Could not open {}: ... Running in dry-run monitor mode.` and falls back to dry-run loop rather than crashing.

### 1.2 Wire Protocol Entry Point (`software/gadget-common`)
- **Source File**: `software/gadget-common/src/lib.rs` (lines 1–83).
- **Packet Structure & Framing Constants**:
  - `MAGIC_0: u8 = 0xAA` (decimal 170)
  - `MAGIC_1: u8 = 0x55` (decimal 85)
  - `PACKET_LEN: usize = 8`
- **Field Layout**:
  - Byte 0: `0xAA` (`MAGIC_0`)
  - Byte 1: `0x55` (`MAGIC_1`)
  - Byte 2: `cpu_percent: u8` (clamped to 100)
  - Byte 3: `cpu_temp_c: u8` (0..=255)
  - Byte 4: `ram_percent: u8` (clamped to 100)
  - Byte 5: `gpu_percent: u8` (clamped to 100)
  - Byte 6: `gpu_temp_c: u8` (0..=255)
  - Byte 7: `battery_percent: u8` (clamped to 100)
- **Decoder Behavior (`decode`, lines 66–82)**:
  - Requires `buf.len() >= 8`.
  - Requires `buf[0] == 0xAA && buf[1] == 0x55`.
  - Rejects malformed magic or truncated buffers with `None`.
- **Receiver State Machine (`software/gadget-firmware-uno/src/main.rs:90–130`)**:
  - Sliding window parser on UART: waits for `0xAA`, checks next byte for `0x55` (with self-recovery if another `0xAA` is received), reads remaining 6 bytes, invokes `TelemetryPacket::decode()`, renders, sends `"ACK\n"`, and resets index to 0.

### 1.3 Core Rendering & Display Traits (`software/gadget-core`)
- **Source Files**:
  - `software/gadget-core/src/traits.rs` (lines 1–29): Minimal `#![no_std]` traits `SpiWrite` (`write_byte`, `write_bytes`, `write_repeated`), `PinWrite` (`set_high`, `set_low`), and `DelayMs` (`delay_ms`).
  - `software/gadget-core/src/display.rs` (lines 1–246): Implements `Ili9488<SPI, CS, DC, RST>` (480x320 landscape, 18-bit RGB666 color mode = 3 bytes per pixel).
    - Window setup: `0x2A` (CASET: $x_0, x_1$), `0x2B` (PASET: $y_0, y_1$), `0x2C` (RAMWR).
    - Primitive functions: `fill_rect`, `draw_pixel`, `draw_hline`, `draw_vline`, `draw_rect`, `clear`.
    - Note: Full `clear(color)` invokes `fill_rect(0, 0, 480, 320, color)` transmitting $480 \times 320 \times 3 = 460,800$ bytes over SPI (~691 ms at 8 MHz).
  - `software/gadget-core/src/ui.rs` (lines 1–261):
    - `Dashboard::draw_layout()`: Draws static frame.
    - `Dashboard::update()`: Accepts `TelemetryPacket`.
    - Differential redraw: Only updates changed metrics.

### 1.4 Firmware Build & Memory Footprint (`software/gadget-firmware-uno`)
- **ELF Binary**: `software/gadget-firmware-uno/target/avr-none/release/gadget-firmware-uno.elf`.
- **Direct Measurements**:
  - `avr-size -C --mcu=atmega328p`:
    - Program (Flash): 8,856 bytes (27.0% Full of 32 KB Flash; conforms to $< 28\text{ KB}$ ceiling).
    - Data (SRAM): 983 bytes (48.0% Full of 2048 B SRAM; currently violates $< 100\text{ B}$ ceiling due to font table in `.rodata`).
  - `avr-size -A`:
    - `.text`: 7,874 bytes
    - `.data`: 982 bytes
    - `.bss`: 1 byte (`DEVICE_PERIPHERALS`)
  - `avr-nm -C`:
    - Zero references to dynamic heap symbols (`malloc`, `free`, `realloc`, `__rust_alloc`). Strictly `#![no_std]` and zero-heap.

### 1.5 Execution Environment & Tooling Verification
- Python version: `Python 3.14.7` (host system standard library available, zero pip dependencies).
- AVR toolchains: `/usr/bin/avr-size`, `/usr/bin/avr-nm`, `/usr/bin/avr-gcc` verified functional.
- Rust toolchains: `rustc 1.96.0`, `cargo 1.100.0-nightly` verified functional for both host and `avr-none` targets.

---

## 2. Logic Chain

From the observed component entry points and requirements in `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `SCOPE.md`, we deduce the necessary testing architecture:

1. **Decoupled Opaque-Box Strategy**:
   - The E2E tests must verify system behavior against specifications (R1–R5, 17 features) without relying on internal function names or private structs.
   - By creating four specialized harnesses (`HostHarness`, `WireProtocolHarness`, `DisplayHarness`, `FirmwareElfHarness`), tests can exercise the system through external observable interfaces:
     - Process CLI flags and stdout output.
     - Binary wire protocol byte streams.
     - Hardware SPI bus commands and framebuffers via headless simulation.
     - Compiled ELF binary memory section sizes and symbol tables.

2. **Headless Display & Differential Redraw Simulation Logic**:
   - Physical display hardware (ILI9488 3.5" TFT) cannot be connected to automated headless CI environments.
   - However, `gadget-core` is abstracted over `SpiWrite` and `PinWrite` traits.
   - A headless mock SPI/Pin implementation can interpret MIPI DCS commands (`0x2A`, `0x2B`, `0x2C`) sent by `Ili9488`, maintaining an exact $480 \times 320$ RGB framebuffer in memory.
   - Every window command records the active bounding box `[x0, y0, x1, y1]`.
   - Any call to `set_window(0, 0, 479, 319)` during `Dashboard::update()` instantly flags a **Zero-Flicker Violation** (R4.2 / Feature 12).
   - The harness accurately counts transmitted SPI bytes, verifying that frame updates remain within the $< 35\text{ KB}$ budget ($< 45\text{ ms}$ at 8 MHz SPI).
   - In tandem, a pure Python mathematical model asserts quadrant coordinates ($230 \times 145$), optical angles ($\ge 20'$), and color palette transitions.

3. **Python 3 Standard Library Test Runner**:
   - To avoid external pip package installation failures in constrained embedded development environments, `test_runner.py` must run with zero third-party dependencies using Python 3 standard library (`unittest`, `argparse`, `subprocess`, `dataclasses`, `struct`, `re`, `json`).
   - The CLI interface must support `--tier 1,2,3,4`, `--verbose`, `--summary`, `--feature <id>`, and produce a clean ANSI-formatted summary table with per-tier pass/fail accounting.
   - Exit code 0 indicates 100% pass; non-zero indicates failure, matching standard CI/CD gates.

---

## 3. Comprehensive Test Runner & Harness Architecture

```
tests/e2e/
├── test_runner.py               # Main CLI runner (Python 3 stdlib, zero pip deps)
├── run_tests.sh                 # Executable wrapper script
├── conftest.py                  # Pytest integration compatibility layer
├── harnesses/                   # Four specialized opaque-box harnesses
│   ├── __init__.py
│   ├── host_harness.py          # gadget-host CLI & process execution harness
│   ├── wire_harness.py          # gadget-common wire protocol framing & codec harness
│   ├── display_harness.py       # Headless display geometry, optical angle & color simulator
│   ├── firmware_harness.py      # AVR ELF binary size, static SRAM & symbol analysis harness
│   └── rust_core_sim.py         # Subprocess bridge to headless Rust simulation binary
├── rust_harness/                # Headless Rust mock display (embedded-hal simulator)
│   ├── Cargo.toml               # Minimal crate depending on gadget-core & gadget-common
│   └── src/
│       └── main.rs              # Headless mock display runner accepting JSON input on stdin / CLI
├── tiers/                       # Test suites partitioned strictly by Tier
│   ├── __init__.py
│   ├── test_tier1_features.py   # Tier 1: Feature Coverage (85 tests, 5 per feature × 17 features)
│   ├── test_tier2_boundaries.py # Tier 2: Boundary & Corner Cases (85 tests, 5 per feature × 17 features)
│   ├── test_tier3_interactions.py # Tier 3: Cross-Feature Combinations (>=17 tests)
│   └── test_tier4_workloads.py  # Tier 4: Real-World Desktop Application Workloads (>=9 tests)
└── reports/                     # Output artifacts, JSON test results, and failure logs
```

### 3.1 Harness Specifications & Concrete Designs

#### A. Host Daemon Harness (`harnesses/host_harness.py`)
- **Component Tested**: `software/gadget-host`
- **Features Tested**: Feature 17 (Host Hardware Telemetry)
- **Key Methods**:
  1. `build_host() -> bool`: Runs `cargo build --manifest-path software/gadget-host/Cargo.toml`.
  2. `run_cli_help() -> subprocess.CompletedProcess`: Runs `gadget-host --help`, asserts exit code 0, checks for `--port`, `--baud`, `--interval-ms`, `--dry-run`.
  3. `run_cli_version() -> str`: Runs `gadget-host --version`, extracts version string.
  4. `run_dry_run(duration_sec=3, interval_ms=1000) -> List[TelemetrySample]`: Runs `gadget-host --dry-run --interval-ms <interval_ms>`, captures stdout, and parses regex:
     `r"\[Metrics\] CPU:\s*(\d+)%\s*\((\d+)°C\)\s*\|\s*GPU:\s*(\d+)%\s*\((\d+)°C\)\s*\|\s*RAM:\s*(\d+)%\s*\|\s*Bat:\s*(\d+)%"`
     Verifies all metrics are bounded: $0 \le \text{percent} \le 100$, $0 \le \text{temp} \le 125^\circ\text{C}$.
  5. `test_invalid_port_fallback(port_name="/dev/nonexistent_serial_e2e") -> bool`: Runs with `--port <invalid>`, verifies stderr contains fallback warning and process transitions to dry-run mode without crashing.
  6. `test_subsecond_interval(interval_ms=200) -> float`: Measures inter-sample arrival timing over 5 samples, verifying sampling rate responds dynamically to `-i`.

#### B. Wire Protocol Harness (`harnesses/wire_harness.py`)
- **Component Tested**: `software/gadget-common`, `software/gadget-firmware-uno` UART receiver
- **Features Tested**: Feature 16 (Serial Packet Protocol)
- **Key Methods**:
  1. `encode_frame(cpu, cpu_temp, ram, gpu, gpu_temp, bat) -> bytes`:
     Packs 8-byte frame: `struct.pack("BBBBBBBB", 0xAA, 0x55, min(cpu, 100), cpu_temp, min(ram, 100), min(gpu, 100), gpu_temp, min(bat, 100))`.
  2. `decode_frame(buf: bytes) -> Optional[dict]`:
     Verifies `len(buf) >= 8`, `buf[0] == 0xAA`, `buf[1] == 0x55`. Returns dictionary of decoded metrics.
  3. `simulate_uart_receiver(stream: bytes) -> List[dict]`:
     Faithfully implements the exact ATmega328P non-blocking sliding window state machine from `software/gadget-firmware-uno/src/main.rs:90–130`.
     - `rx_idx == 0`: waits for `0xAA`.
     - `rx_idx == 1`: if `0x55` advances to 2; if `0xAA` stays at 1; else resets to 0.
     - `rx_idx >= 2`: collects bytes until `rx_idx == 8`, then emits decoded packet and resets to 0.
  4. Fuzzing & Recovery Test Scenarios:
     - Header corruption (`0xAB 0x55`, `0xAA 0x54`, `0x00 0x00`).
     - Truncated frames ($1 \dots 7$ bytes).
     - False preamble sync (`0xAA 0xAA 0x55`).
     - Random line noise injection before/after valid frames.
     - Metric overflow clamping ($> 100\%$ clamped to $100\%$).

#### C. Display & Differential Redraw Mock Harness (`harnesses/display_harness.py` & `rust_harness`)
- **Component Tested**: `software/gadget-core`
- **Features Tested**: Features 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
- **Headless Architecture**:
  1. **Rust Simulator (`tests/e2e/rust_harness/src/main.rs`)**:
     - Implements `gadget_core::SpiWrite`, `PinWrite`, `DelayMs`.
     - Intercepts ILI9488 DCS commands:
       - `0x2A` (CASET): Captures $X_0, X_1$.
       - `0x2B` (PASET): Captures $Y_0, Y_1$.
       - `0x2C` (RAMWR): Decodes RGB888 pixel stream into virtual framebuffer `[480][320]Color`.
     - Records bounding boxes `Rect { x0, y0, x1, y1, bytes }`.
     - Detects and flags any full screen clear `set_window(0, 0, 479, 319)` during `update()`.
     - JSON IPC interface:
       - Input: `{"action": "init"}` -> Calls `Dashboard::draw_layout()`, outputs initial layout stats.
       - Input: `{"action": "update", "packet": {...}}` -> Calls `Dashboard::update()`, outputs dirty bounding boxes, byte count, and pixel samples.
  2. **Python Geometric & Optical Model (`DisplayHarness`)**:
     - **4-Quadrant Layout Geometry**:
       - Screen: 480x320 landscape.
       - Margins: $X_{\text{margin}} = 7\text{ px}$, $Y_{\text{margin}} = 10\text{ px}$.
       - Gutters: $X_{\text{gap}} = 6\text{ px}$, $Y_{\text{gap}} = 10\text{ px}$.
       - Card Dimensions: Exactly $230 \times 145\text{ px}$ each.
       - Q1 (CPU): $[7, 10, 236, 154]$
       - Q2 (GPU): $[243, 10, 472, 154]$
       - Q3 (RAM): $[7, 165, 236, 309]$
       - Q4 (Thermals): $[243, 165, 472, 309]$
       - Symmetry validation: $7 + 230 + 6 + 230 + 7 = 480\text{ px}$; $10 + 145 + 10 + 145 + 10 = 320\text{ px}$.
     - **Arm's-Length Typography (ISO 9241-303)**:
       - Pixel pitch: $0.153\text{ mm/pixel}$ (3.5" 480x320 display).
       - Sitting distance: $700\text{ mm}$ (desk distance 60–90 cm).
       - Visual Angle Formula:
         $$\theta_{\text{arcmin}} = \left(\frac{\text{Height}_{\text{px}} \times 0.153}{700}\right) \times \frac{180 \times 60}{\pi}$$
       - Asserts primary numeral height $\ge 28\text{ px}$ ($\theta = 21.02' \ge 20'$ standard) and $\le 36\text{ px}$.
       - Asserts zero primary readings rendered with sub-14px font.
     - **Chunky Meter Geometry**:
       - Outer track: $202\text{ px} \times 24\text{ px}$.
       - Inner fill track: $200\text{ px} \times 22\text{ px}$.
       - Fill width formula: $\text{fill\_w} = 2 \times \text{value}$ pixels.
     - **Dynamic Palette Color Transition Tables**:
       - Q1 CPU: $<60\%$ Electric Cyan (`#00D2D3` / RGB: 0, 210, 211) $\to 60–84\%$ Coral Amber (`#FFA502` / RGB: 255, 165, 2) $\to \ge 85\%$ Alert Coral (`#FF6B6B` / RGB: 255, 107, 107).
       - Q2 GPU: $<65\%$ Neon Green (`#10AC84` / RGB: 16, 172, 132) $\to 65–84\%$ Warning Orange (`#FF9F43` / RGB: 255, 159, 67) $\to \ge 85\%$ Blaze Red (`#FF3838` / RGB: 255, 56, 56).
       - Q3 RAM: $<70\%$ Vivid Violet (`#A55EEA` / RGB: 165, 94, 234) $\to 70–84\%$ Magenta Rose (`#D980FA` / RGB: 217, 128, 250) $\to \ge 85\%$ Danger Red (`#EA2027` / RGB: 234, 32, 39).
       - Q4 Thermals: $<60^\circ\text{C}$ Cool Mint (`#1DD1A1` / RGB: 29, 209, 161) $\to 60–75^\circ\text{C}$ Gold (`#FECA57` / RGB: 254, 202, 87) $\to >75^\circ\text{C}$ Crimson (`#FF3838` / RGB: 255, 56, 56).
     - **Dual Thermals & Peak Highlight**:
       - Asserts both CPU and GPU temperatures rendered simultaneously.
       - Asserts $\max(\text{cpu\_temp}, \text{gpu\_temp})$ receives `[PEAK]` highlight.
       - Non-peak metric rendered in `TEXT_MUTED` (`#8291AF` / RGB: 130, 145, 175).
       - If $\text{peak} > 75^\circ\text{C}$, asserts card border transitions to Crimson.
     - **Differential Redraw & Zero-Flicker Assertions**:
       - `assert full_clear_called == False` across all updates.
       - Identical packet delta: `assert dirty_boxes_count == 0` and `assert spi_bytes == 0`.
       - Single metric update (e.g. CPU only): dirty bounding boxes strictly confined to Q1 ($X \in [7, 236], Y \in [10, 154]$).
       - Total SPI byte budget per update: $< 35,000\text{ bytes}$ ($< 45\text{ ms}$ at 8 MHz SPI).

#### D. Firmware Resource Ceiling Harness (`harnesses/firmware_harness.py`)
- **Component Tested**: `software/gadget-firmware-uno`
- **Features Tested**: Feature 13 (Zero-Heap), Feature 14 (Static SRAM Ceiling), Feature 15 (Flash Ceiling)
- **Key Methods**:
  1. `build_firmware() -> bool`: Executes `cargo +nightly build --release` in `software/gadget-firmware-uno`.
  2. `parse_avr_size() -> dict`:
     Executes `avr-size -A software/gadget-firmware-uno/target/avr-none/release/gadget-firmware-uno.elf`.
     Parses section table:
     - `text_size = section[".text"]`
     - `data_size = section[".data"]`
     - `bss_size = section[".bss"]`
     - Calculates:
       - $\text{Flash} = \text{text\_size} + \text{data\_size}$
       - $\text{Static SRAM} = \text{data\_size} + \text{bss\_size}$
  3. `assert_resource_ceilings()`:
     - Asserts $\text{Flash} < 28,672\text{ bytes}$ ($28\text{ KB}$).
     - Asserts $\text{Static SRAM} \le 100\text{ bytes}$.
  4. `assert_zero_heap()`:
     Executes `avr-nm -C software/gadget-firmware-uno/target/avr-none/release/gadget-firmware-uno.elf`.
     Scans all symbols and asserts absence of:
     `malloc`, `free`, `realloc`, `calloc`, `__rust_alloc`, `__rust_dealloc`, `alloc::raw_vec`, `alloc::vec`.

---

## 4. Test Runner Architecture (`tests/e2e/test_runner.py`)

### 4.1 CLI Specifications
```text
Usage: test_runner.py [OPTIONS]

Opaque-Box E2E Test Runner for Desktop Performance Monitor

Options:
  --tier <TIERS>       Comma-separated list of tiers to run (e.g. '1', '1,2', '3,4').
                       Defaults to all tiers: 1, 2, 3, 4.
  --feature <1-17>     Filter tests by feature number (1 to 17).
  -v, --verbose        Show verbose per-test execution output.
  -s, --summary        Display structured summary table (enabled by default).
  -x, --fail-fast      Stop execution immediately upon first test failure.
  --json               Emit test results in machine-readable JSON format.
  -h, --help           Show this message and exit.
```

### 4.2 Structured Summary Output Table
The runner outputs clean, ANSI-colorized tabular summaries:
```text
========================================================================================
                      DESKTOP GADGET E2E TEST SUITE EXECUTION SUMMARY
========================================================================================
 Tier   Description                       Total    Passed    Failed   Skipped    Rate
----------------------------------------------------------------------------------------
 Tier 1 Feature Coverage (17 Features)       85        85         0         0   100.0%
 Tier 2 Boundary & Corner Cases              85        85         0         0   100.0%
 Tier 3 Cross-Feature Interactions           17        17         0         0   100.0%
 Tier 4 Real-World Workload Scenarios         9         9         0         0   100.0%
----------------------------------------------------------------------------------------
 TOTAL                                      196       196         0         0   100.0%
========================================================================================
 Status: ALL TIERS PASSED [196/196] (Elapsed: 4.82s)
```

### 4.3 Python 3 Test Runner Implementation Sketch
```python
#!/usr/bin/env python3
"""
Desktop Gadget Opaque-Box E2E Test Runner
Standard Python 3 implementation with zero pip dependencies.
"""
import sys
import os
import argparse
import time
import json
import unittest
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class TierResult:
    tier_num: int
    name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_s: float = 0.0

class E2ETestResult(unittest.TestResult):
    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose
        self.test_records = []

    def startTest(self, test):
        super().startTest(test)
        self._start_time = time.time()

    def addSuccess(self, test):
        super().addSuccess(test)
        dur = time.time() - self._start_time
        if self.verbose:
            print(f"  \033[92m[PASS]\033[0m {test.id()} ({dur*1000:.1f}ms)")
        self.test_records.append((test.id(), "PASS", dur, None))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        dur = time.time() - self._start_time
        if self.verbose:
            print(f"  \033[91m[FAIL]\033[0m {test.id()} ({dur*1000:.1f}ms)")
        self.test_records.append((test.id(), "FAIL", dur, str(err[1])))

    def addError(self, test, err):
        super().addError(test, err)
        dur = time.time() - self._start_time
        if self.verbose:
            print(f"  \033[91m[ERROR]\033[0m {test.id()} ({dur*1000:.1f}ms)")
        self.test_records.append((test.id(), "ERROR", dur, str(err[1])))

def print_summary_table(tier_results: List[TierResult], total_elapsed: float):
    print("\n" + "=" * 88)
    print("                      DESKTOP GADGET E2E TEST SUITE EXECUTION SUMMARY")
    print("=" * 88)
    print(f" {'Tier':<6} {'Description':<33} {'Total':>7} {'Passed':>9} {'Failed':>9} {'Skipped':>9} {'Rate':>8}")
    print("-" * 88)
    tot_tests = sum(t.total for t in tier_results)
    tot_pass = sum(t.passed for t in tier_results)
    tot_fail = sum(t.failed for t in tier_results)
    tot_skip = sum(t.skipped for t in tier_results)

    for tr in tier_results:
        rate = (tr.passed / tr.total * 100.0) if tr.total > 0 else 0.0
        print(f" {f'Tier {tr.tier_num}':<6} {tr.name:<33} {tr.total:>7} {tr.passed:>9} {tr.failed:>9} {tr.skipped:>9} {rate:>7.1f}%")
    
    print("-" * 88)
    overall_rate = (tot_pass / tot_tests * 100.0) if tot_tests > 0 else 0.0
    print(f" {'TOTAL':<40} {tot_tests:>7} {tot_pass:>9} {tot_fail:>9} {tot_skip:>9} {overall_rate:>7.1f}%")
    print("=" * 88)

    status_str = "\033[92mALL TIERS PASSED\033[0m" if tot_fail == 0 else f"\033[91m{tot_fail} TESTS FAILED\033[0m"
    print(f" Status: {status_str} [{tot_pass}/{tot_tests}] (Elapsed: {total_elapsed:.2f}s)\n")
```

---

## 5. Outline Design for `TEST_INFRA.md`

`TEST_INFRA.md` is the central test infrastructure document specifying the opaque-box verification framework for the project. The document is outlined as follows:

```markdown
# Test Infrastructure Specification: Opaque-Box E2E Testing Framework

## 1. Overview & Architectural Principles
- 1.1 Purpose & Scope (R1–R5 and 17 Features from PROJECT.md)
- 1.2 Opaque-Box Verification Principles (Contract-driven, trait-based, zero internal coupling)
- 1.3 Target Hardware & Simulation Matrix (Arduino Uno ATmega328P, ILI9488 3.5" TFT, Linux Host)

## 2. Directory Layout & Module Structure
- 2.1 Directory Tree (`tests/e2e/`, `harnesses/`, `rust_harness/`, `tiers/`, `reports/`)
- 2.2 Ownership & Separation of Concerns

## 3. Test Harness Architecture
- 3.1 Host Telemetry Harness (`HostHarness`)
  - Subprocess invocation, CLI option matrix, `/proc` parser validation, `nvidia-smi` latency & fallbacks
- 3.2 Wire Protocol Harness (`WireProtocolHarness`)
  - 8-byte frame codecs, magic header `0xAA 0x55`, UART sliding-window state machine simulation, noise injection
- 3.3 Headless Display & Differential Redraw Harness (`DisplayHarness` & `rust_harness`)
  - `SpiWrite` / `PinWrite` DCS command interpreter (`0x2A`, `0x2B`, `0x2C`)
  - Virtual 480x320 framebuffer & dirty bounding-box tracking
  - Zero-flicker assertion rules (zero full-screen clears during `update()`, $< 35\text{ KB}$ SPI byte budget)
  - ISO 9241-303 optical angle calculations & arm's-length numeral height assertions
  - 4-Quadrant symmetric coordinate geometry ($230 \times 145\text{ px}$ cards)
  - Dynamic palette color transition verification
  - Dual thermals & peak highlight tag assertions
- 3.4 Firmware ELF & Resource Ceiling Harness (`FirmwareElfHarness`)
  - `avr-size` section parsing (`.text`, `.data`, `.bss`)
  - Flash ceiling assertion ($< 28,672\text{ bytes}$)
  - Static SRAM ceiling assertion ($\le 100\text{ bytes}$)
  - `avr-nm` zero-heap allocation audit (`malloc`/`alloc` = 0)

## 4. Test Tier Hierarchy & Targets
- 4.1 Tier 1: Feature Coverage (85 tests minimum, 5 per feature × 17 features)
- 4.2 Tier 2: Boundary & Corner Cases (85 tests minimum, 5 per feature × 17 features)
- 4.3 Tier 3: Cross-Feature Interactions (17 tests minimum)
- 4.4 Tier 4: Real-World Workload Scenarios (9 tests minimum)
- 4.5 Tier Allocation Matrix (Complete mapping table)

## 5. Test Runner CLI Specification
- 5.1 Command-Line Arguments (`--tier`, `--feature`, `--verbose`, `--summary`, `--fail-fast`, `--json`)
- 5.2 Terminal Reporting & Summary Table Design
- 5.3 Exit Codes & CI/CD Integration

## 6. Execution Prerequisites & Toolchain Dependencies
- 6.1 Toolchain Requirements (`python3 >= 3.10`, `rustc/cargo`, `avr-gcc`, `avr-size`, `avr-nm`)
- 6.2 Zero External Pip Dependencies Guarantee
- 6.3 Execution Commands (`python3 tests/e2e/test_runner.py` and `./tests/e2e/run_tests.sh`)

## 7. Failure Invalidation & Diagnostic Procedures
- 7.1 Classification of Failures (Layout, Visual/Palette, Wire/Protocol, Resource Exhaustion)
- 7.2 Forensic Triage Workflow
```

---

## 6. Caveats

1. **Host-Target Cross-Compilation Toolchains**:
   - `FirmwareElfHarness` requires `avr-size` and `avr-nm` to analyze `gadget-firmware-uno.elf`. Both tools were verified present on the host at `/usr/bin/avr-size` and `/usr/bin/avr-nm`. If running in a stripped container without AVR tools, the test runner gracefully skips Tier 1/2 firmware binary tests or reports actionable toolchain missing diagnostics.
2. **Current Implementation Discrepancy**:
   - The current codebase in `gadget-core` still has the legacy 2-panel layout and 983 bytes of static SRAM. The E2E test suite correctly asserts the target specification ($230 \times 145$ 4-quadrant cards, numerals $\ge 28\text{ px}$, SRAM $\le 100\text{ B}$). Tests will fail on the unmigrated codebase and turn green as Milestones M1, M2, M3, M4 are implemented, fulfilling the Test-Driven Development (TDD) model.
3. **Display Protocol Variations**:
   - The display driver uses ILI9488 DCS commands with 18-bit RGB666 mode. The mock harness accurately models 3-byte pixel streaming.

---

## 7. Conclusion

The architecture for the opaque-box E2E test runner and harnesses is complete, mathematically grounded, and fully aligned with `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `SCOPE.md`:
- **Test Runner**: Fully designed in standalone Python 3 standard library, requiring zero third-party packages.
- **Harnesses**: Four decoupled harnesses cover all 17 features:
  - `HostHarness` for CLI, telemetry collection, and signal traps.
  - `WireProtocolHarness` for 8-byte framing, encoding/decoding, and UART sliding-window stream recovery.
  - `DisplayHarness` + `rust_harness` for headless DCS command decoding, virtual framebuffer, dirty bounding-box tracking, and zero-flicker assertions.
  - `FirmwareElfHarness` for `avr-size` Flash/SRAM parsing and `avr-nm` zero-heap auditing.
- **Tier Structure**: Supports the complete 196-test catalog across Tiers 1–4.
- **TEST_INFRA.md**: Outline designed with exhaustive specifications.

Downstream TestWriter agents (`test_writer_tier1`, `test_writer_tier2`, etc.) and `sub_orch_e2e` can immediately proceed with implementation based on this blueprint.

---

## 8. Verification Method

To verify the tools and foundational components designed in this report:

1. **Verify Python 3 Environment**:
   ```bash
   python3 -c "import sys, os, argparse, subprocess, struct, json, unittest; print('Python 3 Stdlib OK:', sys.version)"
   ```
2. **Verify AVR Binary Analysis Tools**:
   ```bash
   avr-size --version
   avr-nm --version
   avr-size -A software/gadget-firmware-uno/target/avr-none/release/gadget-firmware-uno.elf
   ```
3. **Verify Host Telemetry Daemon**:
   ```bash
   cargo run --manifest-path software/gadget-host/Cargo.toml -- --help
   timeout 2s cargo run --manifest-path software/gadget-host/Cargo.toml -- --dry-run
   ```
4. **Verify Core Crate Host Compilation**:
   ```bash
   cargo test --manifest-path software/gadget-core/Cargo.toml
   cargo test --manifest-path software/gadget-common/Cargo.toml
   ```

### Invalidation Conditions
This architecture would be invalidated if:
1. The wire packet protocol format is altered away from the fixed 8-byte frame.
2. The hardware SPI display controller is switched from MIPI DCS window addressing (`0x2A`, `0x2B`, `0x2C`) to an incompatible serial protocol.
