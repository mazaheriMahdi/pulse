## 2026-09-22T18:45:00Z
You are Worker (worker_m3) for Milestone 3 ("Host Telemetry & Common Protocol").
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/worker_m3

MANDATORY FIRST STEP:
Read /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md before doing any work!

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Authoritative reference documents to read:
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m3/SCOPE.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_m3_1/handoff.md (Detailed gadget-common protocol test suite & specifications)
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_m3_2/handoff.md (Detailed sensor priority, AMD GPU hwmon, serial fallback specifications)
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_m3_3/handoff.md (Detailed pure parsing architecture & unit test suite specifications)

FILE WRITE OWNERSHIP:
You have exclusive write access to:
- software/gadget-common/src/lib.rs
- software/gadget-host/src/main.rs
- software/gadget-host/Cargo.toml
STRICT READ-ONLY: Do NOT modify software/gadget-core/* or software/gadget-firmware-uno/*.

YOUR CONCRETE TASKS:
1. software/gadget-common/src/lib.rs:
   - Wire format remains fixed 8 bytes (MAGIC_0 0xAA, MAGIC_1 0x55, 6 metrics).
   - In `decode()`, call `Self::new(...)` for defense-in-depth sanitization of wire values.
   - Implement the comprehensive unit test suite designed by explorer_m3_1 (covering round-trip serialization/deserialization across all fields, percentage clamping to 0..=100, boundary values, strict magic header validation, short buffer rejection, multi-byte stream handling, thermal extremes up to 255°C, trait derivations).
2. software/gadget-host/Cargo.toml:
   - Remove unused `sysinfo = "0.33"` dependency.
3. software/gadget-host/src/main.rs:
   - Implement pure, decoupled, testable parsing functions:
     - `parse_proc_stat_line(line: &str) -> Option<(u64, u64)>`
     - `parse_proc_stat(content: &str) -> Option<(u64, u64)>`
     - `calculate_cpu_percent(prev_idle: u64, prev_total: u64, curr_idle: u64, curr_total: u64) -> u8`
     - `parse_meminfo_kb(content: &str) -> Option<(u64, u64)>`
     - `parse_meminfo(content: &str) -> Option<u8>`
     - `parse_nvidia_smi(output: &str) -> Option<(u8, u8)>`
     - `parse_gpu_busy_percent(content: &str) -> Option<u8>`
     - `parse_hwmon_temp(content: &str) -> Option<u8>`
     - `parse_battery_capacity(content: &str) -> Option<u8>`
   - Refactor `CpuSampler`, `read_ram_percent`, `read_gpu_metrics`, `read_cpu_temp`, and `read_battery_percent` to use these pure functions cleanly.
   - Sensor priority: In `read_cpu_temp()`, prioritize dedicated silicon drivers AMD `k10temp` and Intel `coretemp` before generic `acpitz` ambient sensors. Check `temp1_input` first, then sorted other `temp*_input`.
   - AMD GPU fallback: In `read_gpu_metrics()`, query `nvidia-smi` first; on fallback, read `/sys/class/hwmon` entries with `name == "amdgpu"` (e.g. `temp1_input`) for live GPU temperature rather than hardcoding 50°C, and check `gpu_busy_percent` across `/sys/class/drm/card*`.
   - Serial port fallback: In `main()`, if opening default `/dev/ttyUSB0` fails with `NotFound`, try falling back to `/dev/ttyACM0` before falling back to dry-run mode.
   - Implement the complete 18+ unit test suite designed by explorer_m3_2 and explorer_m3_3.
4. Verification:
   - Run `cargo test` in `software/gadget-common` and document results.
   - Run `cargo test` in `software/gadget-host` and document results.
   - Run `cargo check` in `software/gadget-core`.
   - Run `cargo +nightly check` (or build) in `software/gadget-firmware-uno` to verify downstream compatibility.
   - Run `cargo run -- --dry-run` in `software/gadget-host` and document sampled live metrics.
5. Deliver handoff:
   - Write full report with verification outputs to /home/mahdi/Programming/perfomance-monitor/.agents/worker_m3/handoff.md.
   - Notify parent orchestrator via send_message when complete.
