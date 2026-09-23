# Subagent Dispatch: Explorer 3

- Agent: sub_orch_m1_explorer_3
- Role: Test & Integration Architect
- Working directory: /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3
- Parent: sub_orch_m1 (cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41)
- Mission: Design host-side unit testing strategy for `gadget-core` (`font.rs` and `numeral.rs`) testing numeral heights (>= 28px), bounds checking, zero-allocation assertions, and contract preservation for `display.rs` and future `ui.rs`. Check AVR build compatibility and size verification commands.

## 2026-09-22T18:41:08Z
User Request received:
Design the unit testing and verification strategy for Milestone 1 in software/gadget-core:
1. Design host-side unit tests (`cargo test` in `software/gadget-core`):
   - Test MockDisplay capturing pixels/rectangles.
   - Assert numeral height is >= 28px (e.g. 28px..36px).
   - Assert glyph bounding boxes do not overflow bounds.
   - Assert zero heap allocations (test without `extern crate alloc`).
   - Test rendering for all digits 0..9 and all values 0..100 and edge cases (0, 100, 255).
   - Test unit symbols ('%', '°', 'C').
2. Firmware build & size verification:
   - Check build commands for `software/gadget-firmware-uno` (`cargo +nightly build --release`).
   - Verify `avr-size` evaluation commands to check `.data` + `.bss` < 100 bytes and Flash < 28KB.
3. Interface contracts:
   - Confirm compatibility with `software/gadget-core/src/traits.rs` and `src/display.rs`.

Do NOT modify any source code files.
Write your complete test architecture report to /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3/handoff.md.
When finished, notify your parent via send_message.
