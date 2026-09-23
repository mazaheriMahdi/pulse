## 2026-09-22T18:40:58Z

You are Explorer 1 (explorer_m3_1) for Milestone 3 ("Host Telemetry & Common Protocol").
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/explorer_m3_1

MANDATORY FIRST STEP:
Read /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md before doing any work!

Additional authoritative references:
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m3/SCOPE.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_survey_2/handoff.md

Your Focus:
Investigate software/gadget-common/src/lib.rs and the wire protocol specification.
1. Inspect the existing TelemetryPacket struct, constants (MAGIC_0, MAGIC_1, PACKET_LEN), new(), encode(), and decode() implementations.
2. Formulate an exact, detailed plan and test cases to add comprehensive unit tests in gadget-common/src/lib.rs verifying:
   - Round-trip serialization/deserialization of TelemetryPacket (all fields).
   - Clamping of percentage values to 0..=100 (cpu_percent, ram_percent, gpu_percent, battery_percent) in TelemetryPacket::new().
   - Magic header validation (0xAA 0x55).
   - Short buffer rejection (< 8 bytes).
   - Corrupted header rejection (wrong magic bytes).
   - Edge cases (boundary values 0, 100, 255 for temp, etc.).
3. Check whether any changes to TelemetryPacket are needed or if the existing struct and methods already conform to all requirements. Note that wire format must remain fixed 8 bytes.

Remember:
- You are an Explorer: READ-ONLY. Do NOT modify source code or tests.
- Deliver your findings and detailed recommendation plan in /home/mahdi/Programming/perfomance-monitor/.agents/explorer_m3_1/handoff.md.
- Notify your parent orchestrator via send_message when complete.
