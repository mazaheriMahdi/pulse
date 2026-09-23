## 2026-09-22T22:17:55Z

You are sub_orch_m1_worker_1 (Role: Typography & SRAM Reduction Worker).
Your working directory is /home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_worker_1.
Your parent orchestrator conversation ID is cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT
hardcode test results, create dummy/facade implementations, or
circumvent the intended task. A teamwork_preview_auditor will independently
verify your work. Integrity violations WILL be detected and your
work WILL be rejected.

MANDATORY FIRST STEP: Read the original user request at:
/home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md
Also read:
/home/mahdi/Programming/perfomance-monitor/PROJECT.md
/home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1/SCOPE.md
/home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_1/handoff.md
/home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_2/handoff.md
/home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_explorer_3/handoff.md

Your Mission:
Implement Milestone 1: "Core Typography & SRAM Reduction".

Write Ownership Boundaries:
- `software/gadget-core/src/font.rs`
- `software/gadget-core/src/numeral.rs` (new module)
- `software/gadget-core/src/lib.rs`
- `software/gadget-core/src/traits.rs` (if adding Display trait)
- `software/gadget-core/src/ui.rs` (ONLY surgical 2-line fix to replace core::str::from_utf8(&buf[..len]) with font::draw_ascii, do not redesign UI yet)
- `software/gadget-core/tests/` (comprehensive unit tests)
Do NOT touch `gadget-host` or `gadget-common`.

Key Implementation Tasks:
1. `software/gadget-core/src/numeral.rs`:
   - Implement bespoke 7-segment / chunky geometric numeral engine for big numerals >= 28–36px tall (e.g. 32px or 36px tall, 18–22px wide, 4px stroke thickness).
   - Implement segment bitmask table via `const fn match` in Flash (0 bytes static SRAM).
   - Implement unit symbols: '%' and '°C' (or degree symbol + 'C') using clean geometric shapes.
   - Implement zero-heap, zero-UTF8 integer formatting: format `u8` (0..255) into stack-allocated digits `[u8; 3]` with leading blanks. NO heap allocations, NO UTF-8 validation table.
   - Implement `draw_big_digit` and `draw_big_numeral` taking `&mut D` where `D: Display` (or implemented for `Ili9488`).
2. `software/gadget-core/src/font.rs`:
   - Completely remove the static array `pub static FONT_5X7: [[u8; 5]; 95]` to eliminate 475 bytes of `.data` SRAM.
   - Replace with zero-SRAM `get_glyph_5x7(c: u8) -> [u8; 5]` via a Flash `match` statement supporting ASCII characters.
   - Implement `draw_ascii` for `&[u8]` byte slices, and update `draw_text` to use `text.as_bytes()`.
3. `software/gadget-core/src/lib.rs`:
   - Export `pub mod numeral;`.
4. `software/gadget-core/src/ui.rs`:
   - Replace `core::str::from_utf8(&buf[..len])` in `format_num_unit` call site with `draw_ascii` to eliminate `core::str::from_utf8` (freeing 256 bytes from `.data` SRAM).
5. Comprehensive unit tests in `software/gadget-core/tests/numeral_tests.rs`:
   - Implement `MockDisplay` capturing pixels and draw calls.
   - Test numeral heights (assert height >= 28px and <= 36px for all digits 0..9).
   - Test that all digits 0..9 are visually distinct.
   - Test value sweep for 0..=100 and edge cases (0, 1, 9, 10, 99, 100, 105, 255).
   - Test unit symbols ('%', '°', 'C').
   - Test differential overwrite without residual ghost pixels.
   - Test zero-heap allocation assertion.
6. Verification commands:
   - Run `cargo test` in `software/gadget-core` and verify 100% tests pass.
   - Run `cargo +nightly build --release` in `software/gadget-firmware-uno`.
   - Run `avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf` and check:
     - Program (.text + .data) < 28,672 bytes (28 KB).
     - Data (.data + .bss) < 100 bytes (should be ~26–50 bytes!).
     - Check `avr-nm -C target/avr-none/release/gadget-firmware-uno.elf` to verify `FONT_5X7` and `anon.*.211` (`from_utf8`) are absent from `.data`.

Deliver your complete handoff report to:
/home/mahdi/Programming/perfomance-monitor/.agents/sub_orch_m1_worker_1/handoff.md
Include commands run, test results, `avr-size` outputs, and git diff.
When finished, notify your parent via send_message(Recipient="cf3aad96-f70d-4c4d-afc6-6ab1d1ea6d41", Message="...").
