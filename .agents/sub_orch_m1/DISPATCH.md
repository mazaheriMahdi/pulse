## 2026-09-22T18:39:48Z

You are the Milestone 1 Sub-orchestrator (sub_orch_m1).
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1
Project root: /home/mahdi/Programming/perfomance-monitor

Authoritative Documents:
- /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md (MANDATORY: read this first!)
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_survey_1/handoff.md
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_survey_3/handoff.md

Your Mission:
Own and execute Milestone 1: "Core Typography & SRAM Reduction".
Scope:
1. High-legibility arm's-length numeral rendering: Implement big numerals >= 28–36px tall for all primary readings (satisfying R2). Use a bespoke 7-segment / chunky geometric numeral engine or minimal glyph tables.
2. Eliminate the static SRAM hog in `software/gadget-core`:
   - Remove `FONT_5X7` static table from `.data` SRAM.
   - Eliminate `core::str::from_utf8` validation table (256B) from `.data`.
   - Ensure primary numerals are rendered with zero heap allocation and minimal SRAM footprint.
3. Write thorough unit tests in `software/gadget-core` verifying character rendering bounds, numeral heights (>= 28px), and formatting correctness without heap allocation.
4. Run the standard Project Pattern Iteration Loop (2B):
   - Explorer(s) -> Worker (with MANDATORY INTEGRITY WARNING) -> 2 Reviewers -> 2 Challengers -> Forensic Auditor.
   - Maintain GATE_STATUS.md and progress.md.
   - File write ownership: `software/gadget-core/src/font.rs`, `src/numeral.rs`, `src/lib.rs`. Do NOT touch `gadget-host` or `gadget-common`.
5. Deliver handoff report to .agents/sub_orch_m1/handoff.md and notify the parent orchestrator via send_message.

Your Parent Conversation ID is: f8f20d63-9019-4000-871a-8604d49b3646
