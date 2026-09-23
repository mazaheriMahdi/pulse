## 2026-09-22T18:41:27Z
You are explorer_e2e_1.
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/explorer_e2e_1
Your parent is sub_orch_e2e (conversation ID: 84adcafc-f5e3-46f8-89ac-821d86c446c2).

MANDATORY FIRST STEP: Read /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md.

Also read:
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_e2e/SCOPE.md
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_survey_3/handoff.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_survey_1/handoff.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_survey_2/handoff.md

Your Mission:
Investigate and design the architecture for the opaque-box E2E test runner and test harnesses in `tests/e2e/`.
1. Analyze the entry points of all components:
   - `gadget-host`: CLI options (`--dry-run`, `--port`, `--baud`, `--interval`), subprocess execution, output parsing.
   - `gadget-common`: Wire protocol packet framing (8 bytes, `0xAA 0x55`, metrics), encoder/decoder, corrupted packet rejection.
   - `gadget-core`: Display traits, 4-quadrant layout coordinate geometry, numeral scale and legibility calculations, meter heights/widths, color transition tables, differential bounding box tracker, zero-flicker assertions.
   - `gadget-firmware-uno`: Binary verification using `avr-size` and `avr-nm` (< 28KB Flash, < 100B static SRAM, zero-heap `#![no_std]`).
2. Design the test runner architecture:
   - Standard Python test runner (`tests/e2e/test_runner.py`) or standalone script that can run with standard Python 3.
   - Design mock harnesses for headless simulation of `gadget-core` differential redraw engine and display buffer without requiring physical display hardware.
   - Design command-line interface with tier selection (`--tier 1,2,3,4`), verbose logging, and structured summary table reporting pass/fail per tier and overall total.
3. Design the outline for `TEST_INFRA.md` following the system instruction template.
4. Output: Write your comprehensive findings, architectural blueprint, and harness designs to `/home/mahdi/Programming/perfomance-monitor/.agents/explorer_e2e_1/handoff.md`. Notify parent via send_message when done.
