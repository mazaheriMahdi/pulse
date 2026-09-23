# BRIEFING — 2026-09-22T22:16:15+03:30

## Mission
Exhaustively specify Tier 1 (Feature Coverage, >=85 tests) and Tier 2 (Boundary & Corner Cases, >=85 tests) for the E2E test suite across all 17 features from PROJECT.md, with full input packets, flags, expected behavior, and assertions.

## 🔒 My Identity
- Archetype: spec_miner
- Roles: Specification Miner, E2E Test Suite Designer
- Working directory: /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2
- Original parent: sub_orch_e2e (conversation ID: 84adcafc-f5e3-46f8-89ac-821d86c446c2)
- Milestone: E2E Test Suite Specification (Tier 1 & Tier 2)

## 🔒 Key Constraints
- Tier 1: Feature Coverage (>= 5 test cases per feature, 17 features = at least 85 test cases).
- Tier 2: Boundary & Corner Cases (>= 5 test cases per feature, 17 features = at least 85 test cases).
- Total test cases specified: >= 170 tests across 17 features.
- Every test case must have: Test ID, Feature Name & Requirement Reference (R1-R5), Description, Inputs (exact packet bytes/CLI flags/mock state), Expected Behavior / Output, Assertion criteria.
- Do NOT implement anything — read-only specification role.
- Output report in /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/handoff.md.

## Current Parent
- Conversation ID: 84adcafc-f5e3-46f8-89ac-821d86c446c2
- Updated: 2026-09-22T22:16:15+03:30

## Task Summary
- **What to build**: Exhaustive specification of Tier 1 and Tier 2 E2E test cases across 17 features.
- **Success criteria**: Full coverage of 17 features with >= 5 Tier 1 and >= 5 Tier 2 tests per feature (170 total), exact packet definitions, exact assertions, compliant with survey handoffs and protocol spec.
- **Interface contracts**: PROJECT.md, SCOPE.md, survey handoffs.
- **Code layout**: .agents/spec_miner_e2e_2/handoff.md

## Key Decisions Made
- Partitioned all 17 features into 5 concrete happy-path tests (Tier 1: T1-F01-01 to T1-F17-05 = 85 tests) and 5 boundary/limit/corner tests (Tier 2: T2-F01-01 to T2-F17-05 = 85 tests).
- Verified mathematical geometry: 480x320 screen partitioned symmetrically: 7px left/right margins, 230x145px cards, 6px X gap, 10px Y gap (7+230+6+230+7=480, 10+145+10+145+10=320).
- Formalized visual angle calculation: 28px font subtends 21.02 arcmin at 70cm and 16.35 arcmin at 90cm; 35px font subtends 26.28 arcmin at 70cm and 20.46 arcmin at 90cm (exceeding ISO 9241-303 >= 20 arcmin threshold).
- Formalized meter track geometry: 200px inner fill track, 22px height, 1% = 2px fill width.
- Defined exact color transition boundaries: CPU Cyan/Amber/Coral at 60/85%, GPU Green/Orange/Red at 65/85%, RAM Violet/Magenta/Red at 70/85%, Thermals Mint/Gold/Crimson at 60/75°C.
- Specified differential redraw bounding-box invariants: 0 full clears during update, SPI transfers < 45ms (< 35KB).
- Specified embedded ceiling test cases: avr-size flash < 28KB, static SRAM <= 100 bytes, zero heap symbols.

## Artifact Index
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/DISPATCH.md — Initial dispatch instructions
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/BRIEFING.md — Working memory
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/progress.md — Progress log & heartbeat
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/spec_data.py — Helper module with Features Discovered and Edge Cases
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/tier1_specs.py — Tier 1 test definitions (85 tests)
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/tier2_specs.py — Tier 2 test definitions (85 tests)
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/assemble_handoff.py — Final compilation script
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2/handoff.md — Final exhaustive specification report (1462 lines, 170 test cases)
