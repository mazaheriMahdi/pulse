# Scope: Milestone 3 - Host Telemetry & Common Protocol

## Architecture
- `software/gadget-common`: Shared `#![no_std]` telemetry data structures, serialization, and packet framing (`MAGIC_0 0xAA`, `MAGIC_1 0x55`, 6 metric payload bytes).
- `software/gadget-host`: Linux background daemon collecting telemetry from `/proc/stat`, `/proc/meminfo`, AMD `k10temp`/Intel `coretemp`, AMD GPU hwmon, and `nvidia-smi`, transmitting 8-byte frames over serial.

## Feature Inventory (Milestone 3)
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 16 | Serial Packet Protocol | 8-byte framed packet (`0xAA 0x55` + 6 metrics) with comprehensive unit tests for round-trip encode/decode, 0..=100 clamping, magic header validation, corrupt/short buffer rejection | M3 | PROJECT.md / Survey R5 |
| 17 | Host Hardware Telemetry | Linux host sampling procfs, AMD k10temp/Intel coretemp priority before acpitz, amdgpu hwmon fallback, serial port fallback (/dev/ttyUSB0 -> /dev/ttyACM0), remove unused sysinfo dep, pure testable parsing functions with unit tests | M3 | PROJECT.md / Survey R5 |

## Interface Contracts
- Fixed 8-byte frame:
  - Byte 0: `0xAA` (MAGIC_0)
  - Byte 1: `0x55` (MAGIC_1)
  - Byte 2: `cpu_percent` (0..100)
  - Byte 3: `cpu_temp_c` (0..255 °C)
  - Byte 4: `ram_percent` (0..100)
  - Byte 5: `gpu_percent` (0..100)
  - Byte 6: `gpu_temp_c` (0..255 °C)
  - Byte 7: `battery_percent` (0..100)

## Code Layout Ownership
- `software/gadget-common/src/lib.rs` (EXCLUSIVE WRITE)
- `software/gadget-host/src/main.rs` (EXCLUSIVE WRITE)
- `software/gadget-host/Cargo.toml` (EXCLUSIVE WRITE)
- STRICT READ-ONLY / DO NOT TOUCH: `software/gadget-core/*`, `software/gadget-firmware-uno/*`
