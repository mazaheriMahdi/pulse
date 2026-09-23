## 2026-09-22T18:47:00Z
You are test_writer_e2e_1.
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/test_writer_e2e_1
Your parent is sub_orch_e2e (conversation ID: 84adcafc-f5e3-46f8-89ac-821d86c446c2).

MANDATORY FIRST STEP: Read /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md.

Also read:
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_e2e/SCOPE.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_e2e_1/handoff.md (Test runner architecture, harness designs, and TEST_INFRA.md blueprint)
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/handoff.md (Tier 1 & Tier 2 specifications: 170 tests across all 17 features)
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_e2e_3/handoff.md (Tier 3 & Tier 4 specifications: 27 tests)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & File Boundaries:
You have EXCLUSIVE write ownership of:
- /home/mahdi/Programming/perfomance-monitor/TEST_INFRA.md
- /home/mahdi/Programming/perfomance-monitor/TEST_READY.md
- /home/mahdi/Programming/perfomance-monitor/tests/e2e/**
DO NOT modify any implementation files in `software/` or files in `.agents/` other than your own working directory.

Your Deliverables:
1. Create `/home/mahdi/Programming/perfomance-monitor/TEST_INFRA.md` at project root using the template in the system instructions and the outline in `explorer_e2e_1/handoff.md`.
2. Implement the E2E test suite in `tests/e2e/`:
   - `tests/e2e/harnesses/`:
     - `host_harness.py`: Host CLI & telemetry execution harness.
     - `protocol_harness.py`: Wire protocol & UART framing harness.
     - `display_harness.py`: Headless MIPI DCS display driver & 480x320 framebuffer simulator.
     - `firmware_harness.py`: AVR ELF size and zero-heap symbol analyzer (`avr-size`, `avr-nm`).
   - `tests/e2e/tier1_feature_tests.py`: Exactly 85 test cases (`T1-F01-01` to `T1-F17-05`) per `spec_miner_e2e_2/handoff.md`.
   - `tests/e2e/tier2_boundary_tests.py`: Exactly 85 test cases (`T2-F01-01` to `T2-F17-05`) per `spec_miner_e2e_2/handoff.md`.
   - `tests/e2e/tier3_interaction_tests.py`: Exactly 18 test cases (`T3-INT-01` to `T3-INT-18`) per `explorer_e2e_3/handoff.md`.
   - `tests/e2e/tier4_workload_tests.py`: Exactly 9 test cases (`T4-APP-01` to `T4-APP-09`) per `explorer_e2e_3/handoff.md`.
   - `tests/e2e/test_runner.py`: Standalone Python 3 runner with CLI options (`--tier`, `--summary`, `--verbose`, `--json`), ANSI summary table, and exit code semantics.
   - `tests/e2e/run_tests.sh`: Executable bash runner script.
3. Execute the test runner:
   Run `python3 tests/e2e/test_runner.py --summary` and ensure all 197 tests pass with exit code 0.
4. Publish `/home/mahdi/Programming/perfomance-monitor/TEST_READY.md` at project root with:
   - Test Runner command
   - Coverage Summary table (Tiers 1-4 counts and total)
   - Feature Checklist (all 17 features with their test coverage)
5. Write your handoff report to `/home/mahdi/Programming/perfomance-monitor/.agents/test_writer_e2e_1/handoff.md` and notify parent via send_message.
