## 2026-09-22T18:32:01Z
Authoritative User Request: Read ORIGINAL_REQUEST.md.
Objective: Survey and investigate the existing embedded firmware codebase:
1. Explore `software/gadget-core` and `software/gadget-firmware-uno`.
2. Inspect the current display driver/controller (e.g. ST7796, SPI 8MHz), embedded-hal integration, differential redraw engine, bounding-box dirty clearing/updating logic, font rendering mechanisms, and current memory footprint.
3. Check the memory constraints: 28 KB Flash, 100 bytes static SRAM ceiling on ATmega328P (`avr-size`).
4. Check current build commands (`cargo +nightly build` in `software/gadget-firmware-uno` if nightly/avr-gcc is configured, or check Cargo.toml/configurations).
5. Document what exists, what needs to change to support R1 (4-quadrant layout), R2 (arm's-length >=28-36px numerals), R3 (color coding & chunky visual meters), R4 (differential redraw & zero-heap), and R5 (HAL portability).
