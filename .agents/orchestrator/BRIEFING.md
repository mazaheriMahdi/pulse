# BRIEFING — 2026-09-22T18:42:00Z

## Mission
Research, design, and implement an arm's-length readable, premium 4-Quadrant Big Block UI/UX for the 3.5-inch (480x320) desktop performance monitor gadget per ORIGINAL_REQUEST.md.

## 🔒 My Identity
- Archetype: teamwork_preview_orchestrator
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: /home/mahdi/Programming/perfomance-monitor/.agents/orchestrator
- Original parent: Sentinel
- Original parent conversation ID: cddebaba-a3e8-4372-8331-21598810d0a1

## 🔒 My Workflow
- **Pattern**: Project
- **Scope document**: /home/mahdi/Programming/perfomance-monitor/PROJECT.md
1. **Decompose**: Survey (3 Explorers/Spec Miners) -> Map features to PROJECT.md -> Decompose into 3-7 milestones with interface contracts.
2. **Dispatch & Execute**:
   - Dual-track: E2E Testing Orchestrator (parallel) + Implementation Track milestones.
   - For each milestone: Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop until gate passes.
   - Final milestone: Pass 100% E2E tests + Tier 5 adversarial coverage hardening.
3. **On failure** (in this order):
   - Retry: nudge stuck agent or re-send task
   - Replace: spawn fresh agent with partial progress
   - Skip: proceed without (only if non-critical)
   - Redistribute: split stuck agent's remaining work
   - Redesign: re-partition decomposition
   - Escalate: report to parent (sub-orchestrators only, last resort; Project Orchestrator redesigns)
4. **Succession**: At 16 spawns and all active subagents complete, write soft handoff.md, cancel crons, spawn successor, exit.
- **Work items**:
  1. Survey & Architecture Mapping [done]
  2. M1: Core Typography & SRAM Reduction [in-progress]
  3. M2: 4-Quadrant UI & Differential Redraw [pending M1]
  4. M3: Host Telemetry & Common Protocol [in-progress]
  5. M4: Firmware Integration & Resource Ceilings [pending M2, M3]
  6. M5: Final E2E Test Pass & Adversarial Hardening [pending M4, E2E]
  7. E2E: Opaque-Box E2E Testing Track [in-progress]
- **Current phase**: 2 (Parallel Implementation & E2E Track)
- **Current focus**: Monitoring M1, M3, and E2E Testing Track sub-orchestrators

## 🔒 Key Constraints
- NEVER write, modify, or create source code files directly.
- NEVER run build/test commands yourself — require workers to do so.
- NEVER investigate or explore the problem at the code level — dispatch Explorers for technical investigation.
- Use file-editing tools ONLY for metadata/state files (.md) in .agents/ folder and PROJECT.md.
- Never reuse a subagent after it has delivered its handoff — always spawn fresh.
- Binary veto on Forensic Audit failure.

## Current Parent
- Conversation ID: cddebaba-a3e8-4372-8331-21598810d0a1
- Updated: not yet

## Key Decisions Made
- Completed Survey Phase (spec_miner_survey_3, explorer_survey_1, explorer_survey_2).
- Established 17-feature inventory and 5-milestone dual-track roadmap in PROJECT.md.
- Dispatched sub_orch_e2e (E2E Track), sub_orch_m1 (Typography & SRAM), and sub_orch_m3 (Host Telemetry & Protocol).

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| explorer_survey_1 | teamwork_preview_explorer | Survey Firmware Core | completed | a1b6f4fc-7c87-41aa-98a0-62d4193fc331 |
| explorer_survey_2 | teamwork_preview_explorer | Survey Host Telemetry | completed | 3e3f34ad-9faf-47fe-b18a-21854e2f8d10 |
| spec_miner_survey_3 | teamwork_preview_spec_miner | UI UX Spec Extraction | completed | 6eed6bd9-b725-42e3-b7e0-896f049d4a82 |
| sub_orch_e2e | self | E2E Testing Track Orchestrator | in-progress | 84adcafc-f5e3-46f8-89ac-821d86c446c2 |
| sub_orch_m1 | self | Milestone 1 Sub-orchestrator | in-progress | cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41 |
| sub_orch_m3 | self | Milestone 3 Sub-orchestrator | in-progress | 0ff213ad-167d-45a5-a76d-37504c035f8a |

## Succession Status
- Succession required: no
- Spawn count: 6 / 16
- Pending subagents: 84adcafc-f5e3-46f8-89ac-821d86c446c2, cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41, 0ff213ad-167d-45a5-a76d-37504c035f8a
- Predecessor: none
- Successor: not yet spawned

## Active Timers
- Heartbeat cron: task-17 (every 10m)
- Safety timer: none
- On succession: kill all timers before spawning successor
- On context truncation: run `manage_task(Action="list")` — re-create if missing

## Artifact Index
- /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md — Authoritative User Request
- /home/mahdi/Programming/perfomance-monitor/.agents/orchestrator/DISPATCH.md — Dispatch log from Sentinel
- /home/mahdi/Programming/perfomance-monitor/.agents/orchestrator/progress.md — Liveness & status tracking
- /home/mahdi/Programming/perfomance-monitor/PROJECT.md — Global architecture, feature inventory, milestones
