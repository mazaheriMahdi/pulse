## 2026-09-22T22:09:48+03:30

<USER_REQUEST>
You are the Milestone 3 Sub-orchestrator (sub_orch_m3).
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m3
Project root: /home/mahdi/Programming/perfomance-monitor

Authoritative Documents:
- /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md (MANDATORY: read this first!)
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_survey_2/handoff.md

Your Mission:
Own and execute Milestone 3: "Host Telemetry & Common Protocol".
Scope:
1. `software/gadget-common`:
   - Add comprehensive unit tests in `gadget-common/src/lib.rs` verifying round-trip serialization/deserialization of `TelemetryPacket`, percentage clamping (0..=100), magic header validation (`0xAA 0x55`), and corrupted/short buffer rejection.
2. `software/gadget-host`:
   - Sensor priority: In `read_cpu_temp()`, prioritize dedicated AMD `k10temp` and Intel `coretemp` before falling back to generic `acpitz` ambient sensors.
   - AMD GPU fallback: Read `/sys/class/hwmon` entries with `name == "amdgpu"` for live GPU temperature rather than hardcoding 50°C.
   - Auto-detection / fallback: Support fallback from `/dev/ttyUSB0` to `/dev/ttyACM0` if the device path fails to open.
   - Dependency cleanup: Remove unused `sysinfo = "0.33"` from `Cargo.toml`.
   - Refactor parsing logic (`parse_proc_stat`, `parse_meminfo`, `parse_nvidia_smi`) into pure, testable functions with unit tests in `software/gadget-host`.
   - Verify `cargo test` passes and `cargo run -- --dry-run` accurately samples live host metrics.
3. Run the standard Project Pattern Iteration Loop (2B):
   - Explorer(s) -> Worker (with MANDATORY INTEGRITY WARNING) -> 2 Reviewers -> 2 Challengers -> Forensic Auditor.
   - Maintain GATE_STATUS.md and progress.md.
   - File write ownership: `software/gadget-common/src/lib.rs`, `software/gadget-host/src/main.rs`, `software/gadget-host/Cargo.toml`. Do NOT touch `gadget-core` or `gadget-firmware-uno`.
4. Deliver handoff report to .agents/sub_orch_m3/handoff.md and notify the parent orchestrator via send_message.

Your Parent Conversation ID is: f8f20d63-9019-4000-871a-8604d49b3646
</USER_REQUEST>
