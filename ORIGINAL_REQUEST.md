# Original User Request

## 2026-09-22T18:30:03Z

Research, design, and implement an arm's-length readable, premium 4-Quadrant Big Block UI/UX for the 3.5-inch (480x320) desktop performance monitor gadget.

Working directory: /home/mahdi/Programming/perfomance-monitor
Integrity mode: development

## Requirements

### R1. 4-Quadrant High-Visibility Layout (480x320)
Divide the screen into 4 distinct quadrants (approx 230x145 pixels each) with stylish border cards:
- **Top-Left (Quadrant 1)**: CPU Load (`%`)
- **Top-Right (Quadrant 2)**: GPU Load (`%`)
- **Bottom-Left (Quadrant 3)**: RAM Usage (`%`)
- **Bottom-Right (Quadrant 4)**: Thermals (CPU Temp & GPU Temp in `°C` with peak highlight)

### R2. Arm's-Length Typography & Big Numerals
Every primary reading must use bold, prominent numerals (at least 28–36 pixels tall, scale 4–5 font or bespoke 7-segment / chunky glyphs) that are effortless to read from normal desk sitting distance (60–90 cm). Tiny text is eliminated from primary data paths.

### R3. Dynamic Color Coding & Chunky Visual Meters
Each quadrant must feature a bold, glanceable visual meter (segmented bar, bold progress track, or color-shifting bar) that reflects load:
- **CPU**: Electric Cyan (`#00D2D3`) → Alert Coral
- **GPU**: Neon Green (`#10AC84` / `#05C46B`) → Warning Orange
- **RAM**: Vivid Violet (`#A55EEA`) → Danger Red
- **Thermals**: Cool Blue / Mint (`<60°C`) → Gold (`60–75°C`) → Crimson (`>75°C`)

### R4. AVR ATmega328P Zero-Heap & Zero-Flicker Efficiency
Retain the differential redraw engine in `gadget-core`: only clear and update dirty pixel bounding boxes (the numeric glyph box and active bar fill) over the 8MHz hardware SPI bus to maintain instantaneous refresh with zero screen flicker within the 2KB SRAM ceiling.

### R5. Hardware Agnosticism & Host Telemetry Alignment
Preserve the `embedded-hal` SPI and Pin trait boundaries in `gadget-core` for seamless portability to ESP32. Ensure `gadget-common` and `gadget-host` accurately feed all 4 quadrants from Linux kernel procfs, AMD k10temp, and `nvidia-smi`.

## Acceptance Criteria

### Readability & Visual Polish
- [ ] Primary numbers for all 4 quadrants are at least 28px tall and legible from arm's length (70+ cm).
- [ ] Quadrant boundaries and cards visually separate metrics cleanly.
- [ ] Thermal quadrant displays both CPU and GPU temperatures with dynamic color warning when hot.

### Embedded Performance & Build Verification
- [ ] Firmware binary size remains under 28 KB Flash and under 100 bytes static SRAM on ATmega328P (`avr-size`).
- [ ] `cargo +nightly build` succeeds in `software/gadget-firmware-uno`.
- [ ] `cargo build` succeeds in `software/gadget-host`.
- [ ] Screen updates smoothly without full-screen redraw artifacts or tearing.
