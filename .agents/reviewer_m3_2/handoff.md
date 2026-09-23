# Milestone 3 Review & Adversarial Challenge Report

**Reviewer**: Reviewer 2 (`reviewer_m3_2`)  
**Working Directory**: `/home/mahdi/Programming/perfomance-monitor/.agents/reviewer_m3_2`  
**Review Target**: Milestone 3 ("Host Telemetry & Common Protocol")  
**Handoff Type**: Hard Handoff (Task Complete)  
**Timestamp**: 2026-09-22T22:26:00+03:30  

---

## Review Summary

**Verdict**: **APPROVE**  
**Overall Risk Assessment**: **LOW**  
**Integrity Violations Detected**: **NONE**

### Executive Assessment
The implementation of Milestone 3 by `worker_m3` is exemplary in architectural cleanliness, modular decomposition, and adherence to system contracts.
1. **Interface Contract**: The wire protocol remains strictly fixed at 8 bytes (`MAGIC_0 = 0xAA`, `MAGIC_1 = 0x55`, and 6 single-byte metric fields) with defense-in-depth sanitization on decode.
2. **Downstream Compatibility**: Zero regressions introduced in `software/gadget-core` (`cargo check` passed) or `software/gadget-firmware-uno` (`cargo +nightly build` passed). ATmega328P Flash is 9,882 bytes (34.5% of 28 KB ceiling) and static SRAM is 1 byte (1.0% of 100 byte ceiling).
3. **Sensor Prioritization**: `read_cpu_temp()` rigorously prioritizes dedicated silicon drivers (`k10temp` AMD, `coretemp` Intel) before generic `acpitz`, preferring `temp1_input`.
4. **GPU Telemetry Fallback**: AMD GPU hwmon fallback inspects `/sys/class/hwmon` entries with `name == "amdgpu"` (e.g. `temp1_input`) and DRM sysfs busy metrics instead of hardcoded 50°C.
5. **Serial Port Fallback**: Auto-fallback from `/dev/ttyUSB0` to `/dev/ttyACM0` on `NotFound` is implemented and verified, degrading gracefully to dry-run mode when no serial device is present.
6. **Live Runtime Sampling**: Live sampling via `timeout 3s cargo run -- --dry-run` executed flawlessly on the host system without errors or panics.
7. **Test Coverage**: 9 unit tests in `gadget-common`, 24 unit tests in `gadget-host`, and 85/85 E2E feature tests pass.

---

## 1. Observation

### 1.1 Source Code Audit
- **`software/gadget-common/src/lib.rs`**:
  - Lines 3–5: Wire constants explicitly declared:
    ```rust
    pub const MAGIC_0: u8 = 0xAA;
    pub const MAGIC_1: u8 = 0x55;
    pub const PACKET_LEN: usize = 8;
    ```
  - Lines 7–15: `TelemetryPacket` defines 6 single-byte payload fields:
    ```rust
    #[derive(Copy, Clone, Debug, PartialEq, Eq, Default)]
    pub struct TelemetryPacket {
        pub cpu_percent: u8,
        pub cpu_temp_c: u8,
        pub ram_percent: u8,
        pub gpu_percent: u8,
        pub gpu_temp_c: u8,
        pub battery_percent: u8, // 0..100
    }
    ```
  - Lines 17–34: `TelemetryPacket::new` enforces `.min(100)` on all percentage metrics (`cpu_percent`, `ram_percent`, `gpu_percent`, `battery_percent`) while preserving temperatures (0..=255°C).
  - Lines 36–45: `encode(&self, out: &mut [u8; PACKET_LEN])` maps bytes strictly according to the contract:
    - Byte 0: `MAGIC_0` (`0xAA`)
    - Byte 1: `MAGIC_1` (`0x55`)
    - Byte 2: `cpu_percent`
    - Byte 3: `cpu_temp_c`
    - Byte 4: `ram_percent`
    - Byte 5: `gpu_percent`
    - Byte 6: `gpu_temp_c`
    - Byte 7: `battery_percent`
  - Lines 47–62: `decode(buf: &[u8]) -> Option<Self>` checks `buf.len() < PACKET_LEN`, header magic equality (`buf[0] != MAGIC_0 || buf[1] != MAGIC_1`), and delegates to `Self::new(buf[2]..buf[7])` for wire sanitization.

- **`software/gadget-host/Cargo.toml`**:
  - `sysinfo = "0.33"` has been completely removed.
  - Dependencies are strictly minimal:
    ```toml
    [dependencies]
    gadget-common = { path = "../gadget-common" }
    serialport = "4.7"
    clap = { version = "4.5", features = ["derive"] }
    ```

- **`software/gadget-host/src/main.rs`**:
  - Pure testable parsers operating on string slices:
    - `parse_proc_stat_line(line: &str) -> Option<(u64, u64)>` (lines 32–46)
    - `parse_proc_stat(content: &str) -> Option<(u64, u64)>` (lines 49–54)
    - `calculate_cpu_percent(prev_idle, prev_total, curr_idle, curr_total) -> u8` (lines 57–73)
    - `parse_meminfo_kb(content: &str) -> Option<(u64, u64)>` (lines 76–95)
    - `parse_meminfo(content: &str) -> Option<u8>` (lines 98–103)
    - `parse_nvidia_smi(output: &str) -> Option<(u8, u8)>` (lines 106–122)
    - `parse_gpu_busy_percent(content: &str) -> Option<u8>` (lines 125–127)
    - `parse_hwmon_temp(content: &str) -> Option<u8>` (lines 130–137)
    - `parse_battery_capacity(content: &str) -> Option<u8>` (lines 140–142)
    - `should_fallback_port(port_name: &str, is_not_found: bool) -> bool` (lines 317–319)
  - Sensor prioritization in `read_cpu_temp()` (lines 218–249):
    - Priority 1: dedicated silicon sensors `name == "k10temp"` or `name == "coretemp"`.
    - Priority 2: generic ACPI zones `name == "acpitz"`.
    - Fallback: sensible default 50°C.
    - Inside `read_hwmon_temp(dir: &Path)` (lines 182–216): queries `dir.join("temp1_input")` first; falls back to sorted `temp*_input`.
  - AMD GPU hwmon fallback in `read_gpu_metrics()` (lines 251–265, 279–302):
    - If `nvidia-smi` is unavailable or returns non-zero status, queries `/sys/class/hwmon` entries with `name == "amdgpu"` via `read_amd_gpu_temp()`.
    - Fallback temperature is extracted from `read_hwmon_temp(&dir)` (e.g. `temp1_input`) rather than hardcoding 50°C.
    - Reads AMD GPU utilization across `/sys/class/drm/card0..card7/device/gpu_busy_percent`.
  - Serial port fallback in `open_serial_port()` (lines 321–358):
    - On `NotFound` error for `/dev/ttyUSB0`, attempts fallback to `/dev/ttyACM0` at the same baud rate.
    - On failure, logs warning and seamlessly transitions to dry-run monitor mode.

### 1.2 Verification Commands Executed Verbatim
1. **`cargo test` in `software/gadget-common`**:
   ```bash
   cd software/gadget-common && cargo test
   ```
   *Output*:
   ```text
   running 9 tests
   test tests::test_decode_defense_in_depth_clamping ... ok
   test tests::test_longer_buffer_handling ... ok
   test tests::test_edge_cases_and_temperature_extremes ... ok
   test tests::test_magic_header_validation ... ok
   test tests::test_percentage_boundary_values ... ok
   test tests::test_percentage_clamping_above_100 ... ok
   test tests::test_roundtrip_all_fields ... ok
   test tests::test_short_buffer_rejection ... ok
   test tests::test_trait_derivations ... ok

   test result: ok. 9 passed; 0 failed; 0 ignored; finished in 0.00s
   ```

2. **`cargo test` in `software/gadget-host`**:
   ```bash
   cd software/gadget-host && cargo test
   ```
   *Output*:
   ```text
   running 24 tests
   test tests::test_parse_battery_capacity ... ok
   test tests::test_calculate_cpu_percent_metrics ... ok
   test tests::test_parse_hwmon_temp ... ok
   test tests::test_open_serial_port_nonexistent ... ok
   test tests::test_parse_hwmon_temp_valid ... ok
   test tests::test_parse_meminfo_field_order_and_whitespace ... ok
   test tests::test_parse_gpu_busy_percent ... ok
   test tests::test_parse_meminfo_missing_or_corrupt ... ok
   test tests::test_parse_hwmon_temp_malformed ... ok
   test tests::test_parse_hwmon_temp_out_of_bounds ... ok
   test tests::test_parse_meminfo_high_usage ... ok
   test tests::test_parse_meminfo_standard ... ok
   test tests::test_parse_nvidia_smi_clamping ... ok
   test tests::test_parse_nvidia_smi_header_skipping ... ok
   test tests::test_parse_nvidia_smi_malformed ... ok
   test tests::test_parse_nvidia_smi_multi_gpu ... ok
   test tests::test_parse_nvidia_smi_standard ... ok
   test tests::test_parse_nvidia_smi_with_units ... ok
   test tests::test_parse_proc_stat_full_content ... ok
   test tests::test_parse_proc_stat_line_malformed ... ok
   test tests::test_parse_proc_stat_line_minimal_4_fields ... ok
   test tests::test_parse_proc_stat_line_per_core_rejected ... ok
   test tests::test_parse_proc_stat_line_standard ... ok
   test tests::test_should_fallback_port ... ok

   test result: ok. 24 passed; 0 failed; 0 ignored; finished in 0.00s
   ```

3. **`cargo clippy` on `software/gadget-common` and `software/gadget-host`**:
   ```bash
   cargo clippy --all-targets -- -D warnings
   ```
   *Output*: Clean compilation, 0 warnings.

4. **Downstream check on `software/gadget-core`**:
   ```bash
   cd software/gadget-core && cargo check
   ```
   *Output*: Finished dev profile, exited with code 0.

5. **Downstream build on `software/gadget-firmware-uno`**:
   ```bash
   cd software/gadget-firmware-uno && cargo +nightly check && cargo +nightly build
   ```
   *Output*: Clean compilation, exited with code 0.

6. **AVR Binary Size Check**:
   ```bash
   avr-size target/avr-none/debug/gadget-firmware-uno.elf
   ```
   *Output*:
   ```text
      text    data     bss     dec     hex filename
      9882       0       1    9883    269b target/avr-none/debug/gadget-firmware-uno.elf
   ```
   - **Flash (`.text + .data`)**: 9,882 bytes (< 28,672 bytes ceiling; 34.5% utilization)
   - **Static SRAM (`.data + .bss`)**: 1 byte (< 100 bytes ceiling; 1.0% utilization)

7. **Host Live Telemetry Dry-Run**:
   ```bash
   timeout 3s cargo run -- --dry-run
   ```
   *Output*:
   ```text
   Streaming live telemetry to desktop gadget (Ctrl+C to stop)...

   [Metrics] CPU:   2% (39°C) | GPU:   0% (34°C) | RAM:  56% | Bat: 100%
   [Metrics] CPU:   3% (38°C) | GPU:   0% (34°C) | RAM:  56% | Bat: 100%
   [Metrics] CPU:   3% (38°C) | GPU:   0% (34°C) | RAM:  56% | Bat: 100%
   ```
   - Real-world telemetry successfully retrieved from host kernel procfs and silicon hardware.
   - CPU package temperature was drawn from `/sys/class/hwmon/hwmon5` (`k10temp` AMD CPU: `temp1_input` = 39,000 m°C -> 39°C) instead of motherboard ambient zone (`acpitz` = 20°C / 42°C).
   - GPU metrics were retrieved via `nvidia-smi` (0%, 34°C).
   - RAM utilization was accurately computed from `/proc/meminfo` (56%).

8. **E2E Feature Test Suite**:
   ```bash
   PYTHONPATH=. python3 -m unittest tests/e2e/tier1_feature_tests.py
   ```
   *Output*:
   ```text
   Ran 85 tests in 1.406s
   OK
   ```
   (Specifically, all 5 tests for Feature 16 and all 5 tests for Feature 17 passed).

---

## 2. Logic Chain

1. **Protocol Invariance & Safety**:
   - `TelemetryPacket` maintains the exact wire definition required by PROJECT.md (8 bytes, `MAGIC_0 0xAA`, `MAGIC_1 0x55`, 6 single-byte metrics).
   - In `gadget-common/src/lib.rs`, the modification to `decode()` ensures that even if corrupt or malformed packets arrive with percentages > 100, `TelemetryPacket::new()` clamps them to 100 before passing them to the dashboard renderer. This eliminates potential coordinate overflow or out-of-bounds array indexing in the embedded firmware.
   - The compile-time array size constraint `[u8; PACKET_LEN]` in `encode()` guarantees that downstream buffers cannot be partially populated or overrun.

2. **Downstream Compatibility & Zero Regression**:
   - `gadget-core` consumes `TelemetryPacket` directly. Running `cargo check` confirmed that no type signatures or trait bounds were broken.
   - `gadget-firmware-uno` receives serial bytes non-blockingly and decodes 8-byte frames into `TelemetryPacket`. The firmware compiled cleanly with `cargo +nightly build`.
   - The compiled ELF binary consumed 9,882 bytes of Flash (well below the 28 KB ceiling) and 1 byte of static SRAM (well below the 100 byte ceiling). This validates that changes in `gadget-common` introduced zero SRAM footprint growth on the ATmega328P.

3. **Sensor Discovery & Silicon Accuracy**:
   - Generic ACPI thermal zones (`acpitz`) frequently report motherboard PCB or VRM temperatures rather than semiconductor die junction temperatures. By searching for `k10temp` and `coretemp` first, `read_cpu_temp()` reliably reports actual CPU core package temperatures.
   - Within each hwmon node, checking `temp1_input` first follows the Linux sysfs driver standard for the primary die sensor.
   - For AMD systems without NVIDIA hardware, scanning for `name == "amdgpu"` and reading `temp1_input` provides genuine hardware GPU thermals rather than an arbitrary 50°C mock.

4. **Serial Port Robustness**:
   - Arduino Uno boards using the ATmega16U2 USB-to-serial converter enumerate as `/dev/ttyACM0` on Linux, while FTDI or CH340 clones enumerate as `/dev/ttyUSB0`.
   - Detecting `NotFound` on `/dev/ttyUSB0` and falling back to `/dev/ttyACM0` ensures seamless plug-and-play operation across genuine Arduinos and clone boards without user configuration.
   - Graceful fallback to dry-run mode when no board is connected prevents crashes and provides a usable headless diagnostic interface.

5. **Integrity & Code Quality Verification**:
   - All tests run genuine algorithms against real inputs; no mock bypasses, dummy facades, or hardcoded test values were detected in production paths.
   - Unused dependencies (`sysinfo`) were removed, shrinking binary compile overhead and attack surface.

---

## 3. Caveats

- **Linux Interface Specifics**: The implementation relies on Linux sysfs (`/sys/class/hwmon`, `/sys/class/drm`, `/sys/class/power_supply`) and procfs (`/proc/stat`, `/proc/meminfo`). On non-Linux host platforms, the daemon falls back gracefully to dry-run mode with safe default values (CPU temp = 50°C, GPU = (0%, 50°C), Battery = 100%).
- **Serial Port Permissions**: In Linux environments, accessing `/dev/ttyUSB0` or `/dev/ttyACM0` requires read/write permissions (typically membership in the `uucp` or `dialout` group). When a port exists but permission is denied (`EACCES`), `open_serial_port()` correctly logs an error and enters dry-run mode rather than trying the alternative port.

---

## 4. Conclusion

The Milestone 3 deliverables satisfy all functional, architectural, and quality criteria defined in `PROJECT.md`, `ORIGINAL_REQUEST.md`, and `SCOPE.md`.
- Wire format is verified at 8 bytes.
- Downstream crates (`gadget-core`, `gadget-firmware-uno`) build and check cleanly.
- ATmega328P Flash (9,882 bytes < 28 KB) and static SRAM (1 byte < 100 bytes) are strictly within budget.
- Sensor priority (`k10temp`/`coretemp` -> `acpitz`), AMD GPU hwmon, and serial fallback operate as specified.
- The unit and E2E test suites achieve 100% pass rates.

**Final Verdict**: **APPROVE**

---

## 5. Verification Method

To independently reproduce and verify this review, execute the following commands from the repository root (`/home/mahdi/Programming/perfomance-monitor`):

1. **Verify `gadget-common` unit tests**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-common
   cargo test
   cargo clippy --all-targets -- -D warnings
   ```
2. **Verify `gadget-host` unit tests & live dry-run**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-host
   cargo test
   cargo clippy --all-targets -- -D warnings
   timeout 3s cargo run -- --dry-run
   ```
3. **Verify downstream compatibility in `gadget-core`**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-core
   cargo check
   ```
4. **Verify AVR firmware build and resource ceilings**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor/software/gadget-firmware-uno
   cargo +nightly check
   cargo +nightly build
   avr-size target/avr-none/debug/gadget-firmware-uno.elf
   ```
   *Expected condition*: `text` < 28672 bytes, `data + bss` < 100 bytes.
5. **Verify full E2E test suite**:
   ```bash
   cd /home/mahdi/Programming/perfomance-monitor
   PYTHONPATH=. python3 -m unittest tests/e2e/tier1_feature_tests.py
   ```
   *Expected condition*: 85 tests run, 0 failures.

### Invalidation Conditions
- Modification of `PACKET_LEN`, `MAGIC_0`, or `MAGIC_1` in `gadget-common`.
- Introduction of any dynamic allocation or static array bloat exceeding 100 bytes SRAM in `gadget-firmware-uno`.
- Re-introduction of unused dependencies in `software/gadget-host/Cargo.toml`.

---

## Adversarial Challenge & Stress-Test Report

### Challenge Summary
- **Overall Risk Assessment**: LOW
- **Hypotheses Tested**: 6
- **Vulnerabilities Found**: 0 critical, 0 major, 1 minor note

### Challenges & Stress Test Results
1. **Scenario: Out-of-bounds percentage over serial wire (> 100%)**
   - *Attack*: Wire buffer contains `[0xAA, 0x55, 250, 60, 200, 150, 70, 110]`.
   - *Expected*: Decoding must sanitize percentages to 100 without memory corruption or graphical clipping in firmware meters.
   - *Observed*: `TelemetryPacket::decode()` returned `cpu=100`, `ram=100`, `gpu=100`, `battery=100`, while preserving `cpu_temp=60`, `gpu_temp=70`.
   - *Result*: **PASS**.

2. **Scenario: Processor counter reset or tick rollover**
   - *Attack*: Host kernel resets CPU ticks (`curr_total < prev_total` or `curr_idle > curr_total`).
   - *Expected*: No integer underflow panic in `calculate_cpu_percent()`.
   - *Observed*: `delta_total.saturating_sub(prev_total)` evaluates to 0; function returns 0% without panic.
   - *Result*: **PASS**.

3. **Scenario: Missing or corrupt `/proc/meminfo`**
   - *Attack*: Empty file, missing `MemAvailable`, or non-numeric contents.
   - *Expected*: No divide-by-zero or unwrap panic.
   - *Observed*: Guard `tot > 0` and pattern matching safely return `None`; daemon falls back to 0% usage.
   - *Result*: **PASS**.

4. **Scenario: Missing primary serial port `/dev/ttyUSB0`**
   - *Attack*: Device plugged into Arduino Uno USB CDC ACM port (`/dev/ttyACM0`).
   - *Expected*: Transparent fallback without crashing.
   - *Observed*: `should_fallback_port` triggers second attempt on `/dev/ttyACM0`; if both absent, switches to dry run.
   - *Result*: **PASS**.

5. **Scenario: Silicon sensor priority on multi-sensor hardware**
   - *Attack*: Hardware has both ambient motherboard ACPI zone (`acpitz` = 20°C / 42°C) and CPU die sensor (`k10temp` = 39°C).
   - *Expected*: High-accuracy silicon die sensor must take precedence.
   - *Observed*: Host daemon reported 39°C CPU temperature matching `k10temp`.
   - *Result*: **PASS**.

6. **Scenario: Extreme / glitched hwmon temperature (> 125°C or <= 0°C)**
   - *Attack*: Sensor reports `0` (uninitialized) or `140000` (disconnected bus error).
   - *Expected*: Reject glitch reading and fallback to secondary sensor or sensible default.
   - *Observed*: `parse_hwmon_temp` filters out `temp <= 0 || temp >= 125`, successfully preventing bad display state.
   - *Result*: **PASS**.
