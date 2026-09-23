## 2026-09-22T18:39:48Z

You are the E2E Testing Orchestrator (sub_orch_e2e).
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_e2e
Project root: /home/mahdi/Programming/perfomance-monitor

Authoritative Documents:
- /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md (MANDATORY: read this first!)
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md
- /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_survey_3/handoff.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_survey_1/handoff.md
- /home/mahdi/Programming/perfomance-monitor/.agents/explorer_survey_2/handoff.md

Your Mission:
You lead the E2E Testing Track (opaque-box, requirement-driven testing).
Per the Project Pattern Dual Track specifications:
1. Create /home/mahdi/Programming/perfomance-monitor/TEST_INFRA.md using the template in the system instructions.
2. Design and implement a comprehensive test suite in `tests/e2e/` testing the product opaque-box based on requirements R1–R5 and all 17 features in PROJECT.md.
3. Use the 4-tier test case design methodology:
   - Tier 1: Feature Coverage (>= 5 test cases per feature, covering all 17 features = >=85 tests)
   - Tier 2: Boundary & Corner Cases (>= 5 test cases per feature = >=85 tests)
   - Tier 3: Cross-Feature Interactions (pairwise combinations = >=17 tests)
   - Tier 4: Real-World Application Scenarios (>= 9 realistic desktop workloads / scenarios)
4. Implement the test runner script/binary that executes all tests, reports per-tier and total counts, and exits 0 on success.
5. When complete, publish /home/mahdi/Programming/perfomance-monitor/TEST_READY.md at project root with the runner command, coverage summary, and feature checklist.
6. Dispatch specialist subagents (e.g. teamwork_preview_test_writer, teamwork_preview_worker, teamwork_preview_reviewer, teamwork_preview_challenger, teamwork_preview_auditor) to build and review the test suite.
7. Deliver your soft/hard handoff report to .agents/sub_orch_e2e/handoff.md and notify the parent orchestrator via send_message.

Your Parent Conversation ID is: f8f20d63-9019-4000-871a-8604d49b3646
