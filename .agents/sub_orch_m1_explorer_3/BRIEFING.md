# BRIEFING — 2026-09-22T18:50:00Z

## Mission
Design host-side unit testing and verification strategy for Milestone 1 in software/gadget-core (test MockDisplay, numeral height >= 28px, glyph bounding boxes, zero-heap allocation, 0..9/0..100/edge cases, unit symbols, AVR build & avr-size checks, interface contracts).

## 🔒 My Identity
- Archetype: explorer
- Roles: Test & Integration Architect
- Working directory: /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3
- Original parent: cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41
- Milestone: Milestone 1 (M1) Core Typography & SRAM Reduction

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Do NOT modify any source code files (only metadata/reports in our own folder)
- Ensure all test designs and commands are verifiable and self-contained
- Target AVR ATmega328P constraints: Flash < 28KB, static SRAM (.data + .bss) < 100B, zero heap

## Current Parent
- Conversation ID: cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41
- Updated: 2026-09-22T18:50:00Z

## Investigation State
- **Explored paths**:
  - `software/gadget-core/src/lib.rs`, `traits.rs`, `display.rs`, `font.rs`, `ui.rs`, `pet.rs`, `Cargo.toml`
  - `software/gadget-firmware-uno/src/main.rs`, `Cargo.toml`, `.cargo/config.toml`
  - Peer findings from Explorer 1 (`.agents/sub_orch_m1_explorer_1/handoff.md`) and Explorer 2 (`.agents/sub_orch_m1_explorer_2/handoff.md`)
- **Key findings**:
  - Current firmware static SRAM is 983 bytes (violates < 100B constraint); Flash is 8856 bytes (< 28KB ceiling satisfied).
  - SRAM leak is 731 bytes from `FONT_5X7` (475B) and `str::from_utf8` (256B) + ~250B string literals.
  - Explorer 2 designed a 7-segment 22x36px numeral engine (`DIGIT_HEIGHT = 36`, `DIGIT_WIDTH = 22`, `STROKE_THICKNESS = 4`) and unit symbols (`%`, `°`, `C`) with zero SRAM tables.
  - Test strategy requires: (1) `MockDisplay` capturing pixels & rects; (2) Assertions verifying height in [28..36]px; (3) Bounding box overflow assertions; (4) Zero-heap assertion via custom tracking allocator; (5) Values 0..=100 and edge cases 0, 100, 255; (6) Automated `avr-size` evaluation script.
- **Unexplored areas**: Implementation phase (to be completed by Worker).

## Key Decisions Made
- Architecture for `Display` trait in `traits.rs`: `Ili9488` and `MockDisplay` both implement `Display`.
- Dual mock strategy: Direct `MockDisplay` (in-memory frame buffer and rect log) + `Ili9488<MockSpi, MockPin, MockPin, MockPin>` for SPI protocol verification.
- Custom `#[global_allocator]` tracking harness in host tests to assert 0 heap allocations during numeral rendering.
- Shell verification script for CI/Gate to verify `.data + .bss < 100` and `Flash < 28672`.

## Artifact Index
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3/DISPATCH.md — Dispatch log
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3/BRIEFING.md — Situational awareness
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3/progress.md — Liveness heartbeat
- /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3/handoff.md — Final handoff report (completed)
