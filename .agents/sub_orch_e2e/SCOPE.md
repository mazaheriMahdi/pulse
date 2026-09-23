# Scope: E2E Testing Track (Opaque-Box Requirement-Driven Test Suite)

## Architecture
The E2E Test Suite evaluates the desktop performance monitor system end-to-end across its four primary components (`gadget-core`, `gadget-firmware-uno`, `gadget-common`, `gadget-host`).
Testing is opaque-box and requirement-driven, deriving directly from `ORIGINAL_REQUEST.md` (R1–R5) and the 17 features specified in `PROJECT.md`.

Data flow & verification harnesses:
1. **Host Daemon Harness**: Invokes `gadget-host` CLI in dry-run mode and mock environments, validating procfs/sysfs/hwmon telemetry ingestion, sampling accuracy, interval timing, and error recovery.
2. **Wire Protocol Harness**: Injects valid, corrupted, fragmented, and boundary serial frames (8-byte `[0xAA, 0x55, ...]`), validating framing, decoding, clamping, and synchronization.
3. **Display & Differential Redraw Mock Harness**: Feeds telemetry packets into `Dashboard`, validating 4-quadrant layout dimensions (230x145px cards), numeral heights (>=28–36px), visual meter geometry (20–24px), dynamic color transitions, dual thermals + peak badge, and strict dirty bounding-box updates with zero full-screen clears.
4. **Embedded Resource Ceiling Harness**: Analyzes compiled AVR ATmega328P ELF artifacts using `avr-size` and `avr-nm`, strictly enforcing Flash < 28KB, static SRAM < 100 bytes, and zero heap allocation.

## Feature Inventory
| # | Feature | Description | E2E Tier Allocation | Source |
|---|---------|-------------|---------------------|--------|
| 1 | 4-Quadrant Card Grid | 480x320 partitioned into 4 symmetric 230x145px cards with 2px borders | T1 (5), T2 (5), T3, T4 | Survey / R1 |
| 2 | Card Header Bar | Header label in each card with quadrant metric title in accent color | T1 (5), T2 (5), T3, T4 | Survey / R1 |
| 3 | Big Block Numerals | Prominent numerals >= 28–36px tall for all primary readings | T1 (5), T2 (5), T3, T4 | Survey / R2 |
| 4 | Arm's-Length Legibility | Optical angle >= 20 arcminutes for 60–90cm viewing, no sub-14px primary text | T1 (5), T2 (5), T3, T4 | Survey / R2 |
| 5 | Chunky Visual Meters | Bold 20–24px high progress track with dynamic fill | T1 (5), T2 (5), T3, T4 | Survey / R3 |
| 6 | Dynamic CPU Palette | Electric Cyan (`#00D2D3`) -> Alert Coral (`#FF6B6B`) | T1 (5), T2 (5), T3, T4 | Survey / R3 |
| 7 | Dynamic GPU Palette | Neon Green (`#10AC84`) -> Warning Orange (`#FF9F43`) | T1 (5), T2 (5), T3, T4 | Survey / R3 |
| 8 | Dynamic RAM Palette | Vivid Violet (`#A55EEA`) -> Danger Red (`#EA2027`) | T1 (5), T2 (5), T3, T4 | Survey / R3 |
| 9 | Dynamic Thermal Palette | Cool Mint (<60°C) -> Gold (60–75°C) -> Crimson (>75°C) | T1 (5), T2 (5), T3, T4 | Survey / R3 |
| 10 | Dual Temp & Peak Highlight | Simultaneous CPU & GPU temp with high-contrast `[PEAK]` highlight | T1 (5), T2 (5), T3, T4 | Survey / R1, R3 |
| 11 | Differential Redraw Engine | Dirty bounding-box updates for numerals and meter deltas over 8MHz SPI | T1 (5), T2 (5), T3, T4 | Survey / R4 |
| 12 | Zero-Flicker Execution | Eradicate full-screen clears during telemetry update loop | T1 (5), T2 (5), T3, T4 | Survey / R4 |
| 13 | Zero-Heap Architecture | `#![no_std]` execution with zero dynamic allocation | T1 (5), T2 (5), T3, T4 | Survey / R4 |
| 14 | Static SRAM Ceiling | Reduce static RAM to < 100 bytes on ATmega328P | T1 (5), T2 (5), T3, T4 | Survey / R4 |
| 15 | Flash Ceiling (<28KB) | Constrain compiled AVR binary size to < 28 KB | T1 (5), T2 (5), T3, T4 | Survey / R4 |
| 16 | Serial Packet Protocol | 8-byte framed packet (`0xAA 0x55` + 6 metrics) with validation | T1 (5), T2 (5), T3, T4 | Survey / R5 |
| 17 | Host Hardware Telemetry | Linux host sampling procfs, AMD k10temp, and nvidia-smi with fallbacks | T1 (5), T2 (5), T3, T4 | Survey / R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Test Infrastructure & Runner | Test runner script, mock harnesses, directory layout, TEST_INFRA.md | none | IN_PROGRESS |
| M2 | Tier 1 Feature Coverage Tests | >= 5 test cases per feature (17 features = 85 tests minimum) | M1 | PLANNED |
| M3 | Tier 2 Boundary & Corner Tests | >= 5 test cases per feature (17 features = 85 tests minimum) | M1 | PLANNED |
| M4 | Tier 3 Cross-Feature Combinations | Pairwise feature interaction tests (>= 17 tests minimum) | M1 | PLANNED |
| M5 | Tier 4 Real-World Workloads | Realistic desktop workload scenarios (>= 9 tests minimum) | M1 | PLANNED |
| M6 | Review, Challenge, Audit & TEST_READY | Multi-agent verification, coverage audit, publish TEST_READY.md | M2, M3, M4, M5 | PLANNED |

## Test Case Count Targets
- Tier 1 (Feature Coverage): 85 tests (5 × 17 features)
- Tier 2 (Boundary & Corner Cases): 85 tests (5 × 17 features)
- Tier 3 (Cross-Feature Combinations): 17 tests
- Tier 4 (Real-World Workloads): 9 tests
- **Total Minimum Target**: 196 tests

## Interface Contracts
### Test Runner Interface
- Entry Point: `python3 tests/e2e/test_runner.py` or `./tests/e2e/run_tests.sh`
- CLI Arguments: `--tier <1-4>`, `--verbose`, `--summary`
- Output: Structured console output reporting tests passed/failed per tier, overall total, and clean exit code (0 for pass, non-zero for fail).
