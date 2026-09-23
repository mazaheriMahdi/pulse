# Scope: Milestone 1 — Core Typography & SRAM Reduction

## Architecture
Milestone 1 focuses on `software/gadget-core` typography and static memory efficiency:
- High-legibility arm's-length numeral rendering: Implement big numerals >= 28–36px tall for all primary readings (satisfying R2). Use a bespoke 7-segment / chunky geometric numeral engine or minimal glyph tables.
- Eliminate static SRAM hog in `software/gadget-core`:
  - Remove `FONT_5X7: [[u8; 5]; 95]` static table from `.data` SRAM.
  - Eliminate `core::str::from_utf8` validation table (256B) from `.data`.
  - Ensure primary numerals are rendered with zero heap allocation and minimal SRAM footprint.
- Unit testing:
  - Host-side tests in `software/gadget-core` verifying character rendering bounds, numeral heights (>= 28px), and formatting correctness without heap allocation.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 3 | Big Block Numerals | Prominent numerals >= 28–36px tall for all primary readings | M1 | Survey / R2 |
| 4 | Arm's-Length Legibility | Optical angle >= 20 arcminutes for 60–90cm desk viewing, eliminate sub-14px primary text | M1 | Survey / R2 |
| 14 | Static SRAM Ceiling | Reduce static RAM by eliminating FONT_5X7 SRAM table and str::from_utf8 table | M1 | Survey / R4 |

## Subtask Breakdown (Iteration Loop 2B)
1. **Exploration**: 3 Explorers:
   - Explorer 1: Inspect `software/gadget-core/src/font.rs` and `software/gadget-core/src/ui.rs`, detail the current font rendering implementation, exact SRAM leak sources, and design of the big numeral engine (7-segment vs chunky glyph table).
   - Explorer 2: Technical design for zero-heap, zero-SRAM numeral formatting (formatting integers 0..999 to digits/bytes without `core::str::from_utf8` or heap allocation) and geometric segment/stroke rendering.
   - Explorer 3: Interface contract with `display.rs` / `ui.rs`, backwards-compatibility for labels (headers/units) without 475B SRAM cost, and comprehensive unit test strategy for `gadget-core`.
2. **Implementation**: Worker implements `numeral.rs`, refactors `font.rs` and `lib.rs`, adds unit tests, verifies host tests and firmware builds.
3. **Verification**: 2 Reviewers, 2 Challengers, 1 Forensic Auditor, Gate evaluation.

## Interface Contracts
### `numeral` / `font` Module Interface
- `draw_big_numeral<D: Display>(display: &mut D, x: u16, y: u16, value: u8, color: Color, bg_color: Color) -> u16`:
  - Renders a 1, 2, or 3-digit number (0..255).
  - Glyph height: at least 28–36px.
  - Returns bounding box width or renders within tight bounding box.
  - Zero heap allocations (`alloc` is forbidden).
  - No references to `core::str::from_utf8`.
- `draw_big_digit<D: Display>(display: &mut D, x: u16, y: u16, digit: u8, color: Color, bg_color: Color)`:
  - Renders single digit 0..9 with height >= 28px.
- ASCII / Label support:
  - Small text or quadrant header text should use either minimal PROGMEM-safe / algorithmic font or reduced static table that does not leak into `.data` SRAM.
