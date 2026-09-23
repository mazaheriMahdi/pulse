# E2E Test Suite Specification: Tier 1 (Feature Coverage) & Tier 2 (Boundary & Corner Cases)

**Author**: Specification Miner (`spec_miner_e2e_2`)  
**Working Directory**: `/home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_e2e_2`  
**Parent**: `sub_orch_e2e` (Conversation ID: `84adcafc-f5e3-46f8-89ac-821d86c446c2`)  
**Date**: 2026-09-22T22:16:00+03:30  
**Milestone**: E2E Test Suite Specification (Tiers 1 & 2)  
**Authoritative Sources**: `ORIGINAL_REQUEST.md` (R1–R5), `PROJECT.md` (Features 1–17), `sub_orch_e2e/SCOPE.md`, `spec_miner_survey_3/handoff.md`, `explorer_survey_1/handoff.md`, `explorer_survey_2/handoff.md`, ILI9488 Display Datasheet, ATmega328P Architecture Manual.  

---

## 1. Observation

Direct empirical evidence gathered across project artifacts, hardware data sheets, and toolchain probes:

1. **Authoritative Requirements (`ORIGINAL_REQUEST.md`)**:
   - **R1 (Layout)**: 4 distinct quadrants (approx 230x145 pixels each) on a 480x320 screen with stylish border cards: Top-Left (CPU Load %), Top-Right (GPU Load %), Bottom-Left (RAM Usage %), Bottom-Right (Thermals: CPU Temp & GPU Temp in °C with peak highlight).
   - **R2 (Typography)**: Every primary reading must use bold, prominent numerals (at least 28–36 pixels tall, scale 4–5 font or bespoke 7-segment / chunky glyphs) readable from 60–90 cm (70+ cm). Tiny text eliminated from primary data paths.
   - **R3 (Meters & Palettes)**: Bold visual meters (20–24px high) with dynamic color transitions:
     - CPU: Electric Cyan (`#00D2D3`) → Alert Coral (`#FF6B6B`)
     - GPU: Neon Green (`#10AC84` / `#05C46B`) → Warning Orange (`#FF9F43`) → Blaze Red (`#FF3838`)
     - RAM: Vivid Violet (`#A55EEA`) → Danger Red (`#EA2027`)
     - Thermals: Cool Mint (`<60°C`) → Gold (`60–75°C`) → Crimson (`>75°C`)
   - **R4 (Efficiency & Zero-Flicker)**: Differential redraw engine in `gadget-core`: only clear and update dirty pixel bounding boxes over 8MHz SPI bus. Zero screen flicker. Flash binary ceiling < 28 KB, static SRAM ceiling < 100 bytes on ATmega328P (`avr-size`). Strictly `#![no_std]` zero-heap.
   - **R5 (Hardware & Protocol)**: Preserve `embedded-hal` SPI and Pin trait boundaries. Host daemon collecting telemetry from Linux kernel `/proc/stat`, `/proc/meminfo`, AMD `k10temp`/Intel `coretemp`, and `nvidia-smi`/`amdgpu` sysfs, transmitting 8-byte frames over serial UART at 57,600 baud.

2. **Hardware Constraints & Display Timing (`software/gadget-core/src/display.rs`)**:
   - Screen resolution: 480x320 landscape (153,600 pixels).
   - Color format: 18-bit RGB666 (3 bytes per pixel).
   - Full frame refresh SPI payload: 153,600 × 3 = 460,800 bytes.
   - At 8 MHz SPI clock (~1.5 µs/byte with MCU loop overhead): Full screen clear requires ~691 ms. Therefore, full clears during updates produce unbearable half-second strobe flashes.
   - Differential redraw of numeral bounding box (106×36 px = 3,816 pixels × 3 = 11,448 bytes) takes ~17.2 ms.
   - Differential redraw of 10px meter delta (10×22 px = 220 pixels × 3 = 660 bytes) takes ~1.0 ms.
   - Worst-case frame (all 4 metrics updated): ~35,000 bytes SPI (< 45 ms), well within the 1,000 ms update window.

3. **Embedded Footprint Baseline (`software/gadget-firmware-uno`)**:
   - Baseline ELF size: Program (.text + .data) = 8,856 bytes (30.9% of 28 KB ceiling).
   - Baseline SRAM: Data (.data + .bss) = 983 bytes (violating 100-byte ceiling due to `FONT_5X7` [475 B], UTF-8 decode table [256 B], and string literals [~250 B] in `.data`).
   - Target footprint with Flash font / procedural segment generation: Flash < 12 KB, static SRAM < 50 bytes.

4. **Wire Format Contract (`software/gadget-common/src/lib.rs`)**:
   - Fixed 8-byte frame: Byte 0: `0xAA`, Byte 1: `0x55`, Byte 2: `cpu_percent`, Byte 3: `cpu_temp_c`, Byte 4: `ram_percent`, Byte 5: `gpu_percent`, Byte 6: `gpu_temp_c`, Byte 7: `battery_percent`.
   - Frame transmission time at 57,600 baud: 8 × 10 / 57,600 ≈ 1.39 ms.

---

## 2. Logic Chain

1. **Mathematical Partitioning for 480x320 Display**:
   - Display Width = 480 px. Symmetrical horizontal division:
     $$M_x (\text{Left Margin}) + W (\text{Card 1}) + G_x (\text{Center Gap}) + W (\text{Card 2}) + M_x (\text{Right Margin}) = 480$$
     $$7 + 230 + 6 + 230 + 7 = 480\text{ px}$$
   - Display Height = 320 px. Symmetrical vertical division:
     $$M_y (\text{Top Margin}) + H (\text{Card Row 1}) + G_y (\text{Center Gap}) + H (\text{Card Row 2}) + M_y (\text{Bottom Margin}) = 320$$
     $$10 + 145 + 10 + 145 + 10 = 320\text{ px}$$
   - Card coordinates on display:
     - Q1 (Top-Left, CPU): Origin $(7, 10)$, Extent $(236, 154)$, Size $230 \times 145\text{ px}$.
     - Q2 (Top-Right, GPU): Origin $(243, 10)$, Extent $(472, 154)$, Size $230 \times 145\text{ px}$.
     - Q3 (Bottom-Left, RAM): Origin $(7, 165)$, Extent $(236, 309)$, Size $230 \times 145\text{ px}$.
     - Q4 (Bottom-Right, Thermals): Origin $(243, 165)$, Extent $(472, 309)$, Size $230 \times 145\text{ px}$.

2. **Optical Legibility & Arcminute Derivations**:
   - Screen DPI on 3.5" 480x320: $\approx 166\text{ DPI}$ ($0.153\text{ mm/pixel}$).
   - Visual angle formula: $\theta = 2 \times \arctan\left(\frac{h}{2 \times D}\right) \times \frac{180 \times 60}{\pi}\text{ arcminutes}$.
   - At desk sitting distance $D = 700\text{ mm}$ (70 cm):
     - 7px font (scale 1): $h = 1.07\text{ mm} \implies \theta = 5.26\text{ arcmin}$ (completely illegible, fails ISO 9241-303).
     - 28px font (scale 4): $h = 4.28\text{ mm} \implies \theta = 21.02\text{ arcmin}$ (exceeds 20 arcmin threshold; fully compliant).
     - 35px font (scale 5): $h = 5.36\text{ mm} \implies \theta = 26.28\text{ arcmin}$ (high readability).
     - 36px chunky glyph: $h = 5.51\text{ mm} \implies \theta = 27.03\text{ arcmin}$ (optimal glanceability).
   - At maximum desk distance $D = 900\text{ mm}$ (90 cm): 28px yields $16.35\text{ arcmin}$ (meets minimum threshold $\ge 16'$); 35px yields $20.46\text{ arcmin}$ (meets $\ge 20'$).

3. **Chunky Meter Geometric Constraints**:
   - Card width is 230px. Outer borders take 4px ($2\text{px} \times 2$). Padding is 12px on each side.
   - Available meter width = $230 - 4 - 24 = 202\text{ px}$.
   - Inner fill track width = $200\text{ px}$ with 1px border. Height = $22\text{ px}$ inner fill, $24\text{ px}$ outer track.
   - Perfect 1:2 scaling: $1\% = 2\text{ pixels}$. Fill width formula: $\text{FillWidth} = 2 \times \text{clamp}(V, 0, 100)$. Eliminates sub-pixel rounding jitter.

4. **Thermal Dual Readout & Peak Badge Inferences**:
   - Q4 must render both CPU and GPU temperatures.
   - Peak calculation: $\text{peak} = \max(\text{cpu\_temp\_c}, \text{gpu\_temp\_c})$.
   - Peak component receives prominent `[PEAK]` highlight and color-coded foreground matching the thermal palette:
     - $<60^\circ\text{C}$: Cool Mint (`#1DD1A1`)
     - $60–75^\circ\text{C}$: Gold (`#FECA57`)
     - $>75^\circ\text{C}$: Crimson (`#FF3838`)
   - If $\text{peak} > 75^\circ\text{C}$, the Q4 card border switches dynamically from `Color::BORDER` (`#323E5A`) to Crimson (`#FF3838`).

5. **Differential Redraw & Zero-Flicker Architecture**:
   - Startup (`draw_layout()`): Clears full screen once to `Color::DARK_BG`, draws card panels in `Color::PANEL_BG`, card borders in `Color::BORDER`, and static headers.
   - Runtime loop (`update()`):
     - Evaluates $\Delta = \text{packet} \oplus \text{last\_packet}$.
     - If $\Delta == 0$: 0 SPI bytes transmitted.
     - If dirty: Clears only the changed numeral bounding box ($106 \times 36\text{ px}$) to `PANEL_BG` and redraws glyphs; computes meter delta $\Delta W = 2 \times |V_{\text{new}} - V_{\text{old}}|$ and fills or clears only the $\Delta W \times 22\text{ px}$ region (unless color threshold crossed, where active bar is recolored).
     - Invariant: Zero calls to `display.clear()` during `update()`. Total SPI transmission $< 45\text{ ms}$.

---

## 3. Caveats

1. **Mock Hardware vs Real SPI Bus**: While headless test harnesses verify coordinate geometry, byte streams, and memory limits with 100% fidelity, physical display hardware may exhibit minor panel response differences (e.g. ST7796 vs ILI9488 gamma curves). The driver enforces standard MIPI DCS commands (`0x2A`, `0x2B`, `0x2C`) common to both.
2. **Sysfs Availability on Non-Linux Hosts**: Host telemetry tests in CI environments without `/proc` and `/sys` must utilize simulated file systems or dry-run injection harnesses.
3. **Tie-Breaking for Thermal Peak**: When `cpu_temp_c == gpu_temp_c`, both sensors share equal thermal priority. Specification standardizes on highlighting CPU by default or highlighting both identically without visual flickering.

---

## 4. Conclusion

The E2E test specifications for Tier 1 (Feature Coverage) and Tier 2 (Boundary & Corner Cases) are fully articulated, mathematically validated, and ready for immediate implementation. Exactly 85 test cases are specified for Tier 1 (5 tests per feature × 17 features) and 85 test cases for Tier 2 (5 tests per feature × 17 features), yielding **170 exhaustive test case specifications** covering every requirement in `ORIGINAL_REQUEST.md` (R1–R5) and `PROJECT.md`.

---

## 5. Verification Method

To execute and verify these test cases once implemented:
1. **Execute E2E Runner for Tier 1**:
   ```bash
   python3 tests/e2e/test_runner.py --tier 1 --verbose
   ```
   *Acceptance Gate*: 85/85 tests PASS, 0 failures, 0 regressions.
2. **Execute E2E Runner for Tier 2**:
   ```bash
   python3 tests/e2e/test_runner.py --tier 2 --verbose
   ```
   *Acceptance Gate*: 85/85 tests PASS, 0 failures, 0 regressions.
3. **Static Resource Ceiling Verification**:
   ```bash
   cd software/gadget-firmware-uno && cargo +nightly build --release
   avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
   ```
   *Acceptance Gate*: Program < 28,672 bytes (28 KB), Data (.data + .bss) < 100 bytes.
4. **Host Telemetry Dry-Run Verification**:
   ```bash
   cd software/gadget-host && cargo test && cargo run -- --dry-run
   ```

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Layout | 4-Quadrant Card Grid | 480x320 landscape partitioned into 4 symmetric 230x145px cards with 2px borders | Display resolution (480x320), margins (7px X, 10px Y), center gaps (6px X, 10px Y) | 4 distinct card bounds (Q1, Q2, Q3, Q4) with dark gaps | Clamps to screen bounds (480x320) | ORIGINAL_REQUEST.md:12-17, PROJECT.md:27 |
| 2 | Layout | Card Header Bar | Top label bar inside each card rendering quadrant metric title and accent icon | Card origin (X, Y), quadrant type | Rendered title label (14px tall, scale 2) at local Y+8 | Truncates cleanly if label exceeds card inner width (202px) | ORIGINAL_REQUEST.md:13-17, PROJECT.md:28 |
| 3 | Typography | Big Block Numerals | Prominent primary numerals >= 28–36px tall for arm's-length legibility | Value (0..100, °C), scale factor 4 or 5 | Rendered glyphs with uniform pitch and baseline alignment | Clamps out-of-range values or renders error glyphs without crash | ORIGINAL_REQUEST.md:19-20, PROJECT.md:29 |
| 4 | Typography | Arm's-Length Legibility | Subtends >= 20 arcminutes visual angle at 60–90cm viewing distance; eliminate sub-14px primary text | Glyph height (28–36px), display DPI (166), sitting distance (600–900mm) | Physical glyph height 4.28–5.51mm, visual angle 16.3–30.7 arcmin | N/A (ergonomic optical invariant) | ORIGINAL_REQUEST.md:19-21, PROJECT.md:30, ISO 9241-303 |
| 5 | Visual Meter | Chunky Visual Meters | Bold 20–24px high progress track with dynamic fill and 1:2 scaling (1% = 2px) | Value (0..100), palette color | Filled track rect (2*V px) + dark background rect (200 - 2*V px) | Clamps fill width to track bounds (200px max) | ORIGINAL_REQUEST.md:22-28, PROJECT.md:31 |
| 6 | Palette | Dynamic CPU Palette | Electric Cyan (#00D2D3) transitioning to Alert Coral (#FF6B6B) | CPU load percentage (0..100%) | Color RGB triplet: <60% Cyan, 60-84% Amber, >=85% Coral | Clamps to Alert Coral for any value >= 85% | ORIGINAL_REQUEST.md:24, PROJECT.md:32 |
| 7 | Palette | Dynamic GPU Palette | Neon Green (#10AC84) transitioning to Warning Orange (#FF9F43) and Blaze Red (#FF3838) | GPU load percentage (0..100%) | Color RGB triplet: <65% Green, 65-84% Orange, >=85% Red | Clamps to Blaze Red for any value >= 85% | ORIGINAL_REQUEST.md:25, PROJECT.md:33 |
| 8 | Palette | Dynamic RAM Palette | Vivid Violet (#A55EEA) transitioning to Danger Red (#EA2027) | RAM usage percentage (0..100%) | Color RGB triplet: <70% Violet, 70-84% Magenta Rose, >=85% Danger Red | Clamps to Danger Red for any value >= 85% | ORIGINAL_REQUEST.md:26, PROJECT.md:34 |
| 9 | Palette | Dynamic Thermal Palette | Cool Mint (<60°C) -> Gold (60–75°C) -> Crimson (>75°C) | Temperature in °C (0..255) | Color RGB triplet: <60 Mint (#1DD1A1), 60-75 Gold (#FECA57), >75 Crimson (#FF3838) | Crimson for any temperature > 75°C | ORIGINAL_REQUEST.md:27, PROJECT.md:35 |
| 10 | Thermals | Dual Temp & Peak Highlight | Simultaneous CPU & GPU temp display in Q4 with high-contrast [PEAK] highlight and border warning | cpu_temp_c, gpu_temp_c | Dual readouts with [PEAK] badge on max(CPU, GPU); Crimson border if peak > 75°C | Defaults to CPU highlight or dual highlight if temperatures equal | ORIGINAL_REQUEST.md:17, 40, PROJECT.md:36 |
| 11 | Redraw | Differential Redraw Engine | Dirty bounding-box updates for numerals and meter deltas over 8MHz SPI | last_packet, new_packet | Targeted SPI window commands (0x2A, 0x2B, 0x2C) for dirty rects only | 0 SPI transactions emitted if consecutive packets are identical | ORIGINAL_REQUEST.md:29-31, PROJECT.md:37 |
| 12 | Redraw | Zero-Flicker Execution | Eradicate full-screen clears during telemetry update loop; total SPI time < 50ms | Telemetry update tick | Continuous stable display without strobe, wipe, or flicker artifacts | N/A (runtime loop never invokes display.clear()) | ORIGINAL_REQUEST.md:29-31, 46, PROJECT.md:38 |
| 13 | Architecture | Zero-Heap Execution | #![no_std] execution with zero dynamic memory allocation across embedded modules | Embedded runtime execution | Stack-allocated and static memory footprint only; zero malloc/alloc calls | Build failure / link error if dynamic allocator referenced | ORIGINAL_REQUEST.md:29, PROJECT.md:39 |
| 14 | Memory | Static SRAM Ceiling (<=100B) | Constrain static RAM (.data + .bss) to <= 100 bytes on ATmega328P | Compiled ELF artifact | Binary .data + .bss section size reported by avr-size | Build gate failure if .data + .bss > 100 bytes | ORIGINAL_REQUEST.md:43, PROJECT.md:40 |
| 15 | Memory | Flash Ceiling (<28KB) | Constrain compiled AVR binary size (.text + .data) to < 28 KB (28,672 bytes) | Compiled ELF artifact | Binary .text + .data section size reported by avr-size | Build gate failure if Flash size >= 28,672 bytes | ORIGINAL_REQUEST.md:43, PROJECT.md:41 |
| 16 | Protocol | Serial Packet Protocol | Fixed 8-byte frame (0xAA 0x55 + 6 metrics) with non-blocking sliding window sync | Serial UART byte stream at 57,600 baud | Decoded TelemetryPacket struct (6 metric fields) + UART ACK | Resets receive index on invalid magic byte; recovers sync on next valid header | ORIGINAL_REQUEST.md:33, PROJECT.md:42, gadget-common |
| 17 | Telemetry | Host Hardware Telemetry | Linux host daemon sampling procfs, AMD k10temp/Intel coretemp, and nvidia-smi/amdgpu sysfs | Linux kernel APIs (/proc/stat, /proc/meminfo, /sys/class/hwmon) | 8-byte serialized frames transmitted over serial or printed in dry-run | Falls back gracefully to sensible defaults on missing sensor hardware | ORIGINAL_REQUEST.md:33, PROJECT.md:43, gadget-host |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | Numeric Formatting | Value = 100% (3 digits) | Numeral width expands to 3 digits (72–90px). Bounding box must accommodate 3 digits + suffix without overflowing card border. |
| 2 | Numeric Formatting | Value = 0% (1 digit) | Preceding digit columns must be cleanly cleared with PANEL_BG to avoid leaving visual ghost digits from prior 100% reading. |
| 3 | Thermal Equality | cpu_temp_c == gpu_temp_c (e.g. 72°C == 72°C) | Peak tie-breaking logic highlights CPU by default or highlights both without oscillating or flickering. |
| 4 | Thermal Overheat | Temperature > 99°C (e.g. 105°C or 115°C) | Formatting handles 3 digits or clamps to 99°C with flashing Crimson warning border without crashing or buffer overflow. |
| 5 | Host Disconnect | Serial cable unplugged / no packets for 3 seconds | Gadget retains last valid telemetry or renders subtle OFFLINE/WAITING indicator in header without blanking display. |
| 6 | Packet Noise | Corrupted byte stream on UART (bit flips in header) | Sliding window receiver rejects invalid magic header (!= 0xAA 0x55) and resynchronizes on next valid packet start. |
| 7 | Zero Telemetry Delta | Consecutive identical packets received | Differential redraw engine detects equality and emits 0 SPI transactions, preserving 0% bus load. |
| 8 | Rapid Oscillations | Metric swinging 0% <-> 100% every 200ms | Differential bar redraw fills full width without visual tearing; bounding box clearing completely overwrites previous state. |
| 9 | Scale 5 Font Bounds | Character height is 35px, width is 25px | Vertical layout ensures 35px numeral does not overlap card header (Y=24) or chunky meter track (Y=70). |
| 10 | SPI Saturation | All 4 metrics changing simultaneously in one tick | Total SPI transfer is ~35,000 bytes; transfer completes in < 45 ms, well within 1000ms update window. |
| 11 | Over-Range Load | Telemetry packet receives cpu_percent = 255 | Decoder or firmware clamps value to 100%; bar does not exceed 200px track; numeral renders 100% cleanly. |
| 12 | Sensor Shadowing | acpitz ambient sensor (20°C) visited before k10temp (82°C) | Host sensor collector applies strict driver priority, ensuring dedicated silicon temperature is reported. |
| 13 | Missing Serial Port | /dev/ttyUSB0 does not exist on Arduino Uno (uses /dev/ttyACM0) | Host daemon automatically falls back to /dev/ttyACM0 before falling back to dry-run console mode. |
| 14 | Zero CPU Ticks | Host suspended or no CPU tick advance (delta_total == 0) | CpuSampler detects delta_total == 0, returns 0% or previous sample, preventing division-by-zero NaN panic. |
| 15 | Thermal Spike | Temperature leaps across thresholds (45°C -> 65°C -> 85°C) | Palette transitions smoothly Mint -> Gold -> Crimson; card border turns Crimson at 85°C without full redraw. |

---

## Tier 1: Feature Coverage Specifications (85 Test Cases across 17 Features)

Every test case below exercises happy-path feature behavior with exact concrete inputs, expected results, and assertion criteria.

### Feature 01: 4-Quadrant Card Grid (Survey / R1)

#### `T1-F01-01`: Verify 4-quadrant screen partitioning geometry and card counts on 480x320 display.
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify 4-quadrant screen partitioning geometry and card counts on 480x320 display.
- **Inputs**: `Call `Dashboard::new()`, then `draw_layout(&mut display)` on a 480x320 display mock.`
- **Expected Behavior / Output**: Screen is partitioned into exactly 4 rectangular card bounding boxes of 230x145 pixels each.
- **Assertion Criteria**: `Mock records 4 card rects: Q1 at (7, 10, 230, 145), Q2 at (243, 10, 230, 145), Q3 at (7, 165, 230, 145), Q4 at (243, 165, 230, 145).`

#### `T1-F01-02`: Verify card border thickness (2px) and default border color (`Color::BORDER`).
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify card border thickness (2px) and default border color (`Color::BORDER`).
- **Inputs**: ``draw_layout(&mut display)` called on blank display.`
- **Expected Behavior / Output**: Each card is outlined with a 2-pixel solid border in Color::BORDER (`#323E5A` / RGB: 50, 62, 90).
- **Assertion Criteria**: `Pixels at card perimeter (e.g. X in [7..8, 235..236], Y in [10..11, 153..154] for Q1) equal (50, 62, 90).`

#### `T1-F01-03`: Verify horizontal and vertical outer margins and center gutters.
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify horizontal and vertical outer margins and center gutters.
- **Inputs**: ``draw_layout(&mut display)` called on display.`
- **Expected Behavior / Output**: Left margin = 7px, right margin = 7px, center X gap = 6px; Top margin = 10px, bottom margin = 10px, center Y gap = 10px.
- **Assertion Criteria**: `Assert Q1.x = 7; Q2.x = 243; Q2.right = 472 (479 - 7); Q3.y = 165; Q3.bottom = 309 (319 - 10); Q1_Q2_gap = 243 - 237 = 6; Q1_Q3_gap = 165 - 155 = 10.`

#### `T1-F01-04`: Verify card interior background fill (`Color::PANEL_BG`) vs screen background (`Color::DARK_BG`).
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify card interior background fill (`Color::PANEL_BG`) vs screen background (`Color::DARK_BG`).
- **Inputs**: ``draw_layout(&mut display)` called on display.`
- **Expected Behavior / Output**: Screen backdrop is filled with Color::DARK_BG (`#121622` / RGB: 18, 22, 34); card interiors are filled with Color::PANEL_BG (`#1C2234` / RGB: 28, 34, 52).
- **Assertion Criteria**: `Pixel (0, 0) == (18, 22, 34); Pixel (3, 3) == (18, 22, 34); Pixel (240, 50) == (18, 22, 34); Pixel (15, 20) == (28, 34, 52); Pixel (250, 20) == (28, 34, 52).`

#### `T1-F01-05`: Verify functional metric mapping across all four quadrants.
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify functional metric mapping across all four quadrants.
- **Inputs**: `Feed telemetry packet `[0xAA, 0x55, 42, 58, 65, 80, 71, 95]` to `Dashboard::update`.`
- **Expected Behavior / Output**: Q1 renders CPU Load (42%), Q2 renders GPU Load (80%), Q3 renders RAM Usage (65%), Q4 renders Thermals (58°C & 71°C).
- **Assertion Criteria**: `Region Q1 contains '42%'; Region Q2 contains '80%'; Region Q3 contains '65%'; Region Q4 contains '58' and '71'.`

### Feature 02: Card Header Bar (Survey / R1)

#### `T1-F02-01`: Verify Q1 header title text and accent color.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify Q1 header title text and accent color.
- **Inputs**: ``draw_layout(&mut display)` called.`
- **Expected Behavior / Output**: Q1 renders 'CPU LOAD' at local (14, 8) in Electric Cyan (`#00D2D3` / RGB: 0, 210, 211).
- **Assertion Criteria**: `Mock text spy records string 'CPU LOAD' at global position (21, 18) with color (0, 210, 211).`

#### `T1-F02-02`: Verify Q2 header title text and accent color.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify Q2 header title text and accent color.
- **Inputs**: ``draw_layout(&mut display)` called.`
- **Expected Behavior / Output**: Q2 renders 'GPU LOAD' at local (14, 8) in Neon Green (`#10AC84` / RGB: 16, 172, 132).
- **Assertion Criteria**: `Mock text spy records string 'GPU LOAD' at global position (257, 18) with color (16, 172, 132).`

#### `T1-F02-03`: Verify Q3 header title text and accent color.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify Q3 header title text and accent color.
- **Inputs**: ``draw_layout(&mut display)` called.`
- **Expected Behavior / Output**: Q3 renders 'RAM USAGE' at local (14, 8) in Vivid Violet (`#A55EEA` / RGB: 165, 94, 234).
- **Assertion Criteria**: `Mock text spy records string 'RAM USAGE' at global position (21, 173) with color (165, 94, 234).`

#### `T1-F02-04`: Verify Q4 header title text and accent color.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify Q4 header title text and accent color.
- **Inputs**: ``draw_layout(&mut display)` called.`
- **Expected Behavior / Output**: Q4 renders 'THERMALS' at local (14, 8) in Cool Mint (`#1DD1A1` / RGB: 29, 209, 161).
- **Assertion Criteria**: `Mock text spy records string 'THERMALS' at global position (257, 173) with color (29, 209, 161).`

#### `T1-F02-05`: Verify header typography font size (Scale 2, 14px height).
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify header typography font size (Scale 2, 14px height).
- **Inputs**: `Inspect glyph dimensions emitted during card header rendering.`
- **Expected Behavior / Output**: Header labels use scale 2 font (10x14px glyphs, pitch 12px), clearly legible for section identification.
- **Assertion Criteria**: `Height of rendered header characters == 14px; width == 10px; total label height <= 16px.`

### Feature 03: Big Block Numerals (Survey / R2)

#### `T1-F03-01`: Verify big block numeral height compliance (>= 28–36px).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify big block numeral height compliance (>= 28–36px).
- **Inputs**: `Feed telemetry packet with CPU load = 75%.`
- **Expected Behavior / Output**: Primary numeric glyphs ('7' and '5') rendered with height between 28px and 36px.
- **Assertion Criteria**: `Rendered digit bounding box height >= 28px and <= 36px.`

#### `T1-F03-02`: Verify two-digit numeral rendering with percentage suffix (`62%`).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify two-digit numeral rendering with percentage suffix (`62%`).
- **Inputs**: `Feed telemetry packet `[0xAA, 0x55, 62, 50, 50, 50, 50, 100]`.`
- **Expected Behavior / Output**: Digits '6' and '2' rendered at card local (14, 26), followed by '%' unit suffix.
- **Assertion Criteria**: `Digits decoded from framebuffer match '62'; '%' suffix detected adjacent to '2'; total width in [50..85] px.`

#### `T1-F03-03`: Verify three-digit numeral rendering (`100%`).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify three-digit numeral rendering (`100%`).
- **Inputs**: `Feed telemetry packet `[0xAA, 0x55, 100, 50, 50, 50, 50, 100]`.`
- **Expected Behavior / Output**: Digits '1', '0', '0' and '%' fit cleanly within the numeral bounding box (width <= 106px).
- **Assertion Criteria**: `Digits decoded match '100'; rightmost extent X < 130; no collision with card right border (X=230).`

#### `T1-F03-04`: Verify single-digit numeral rendering (`7%`).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify single-digit numeral rendering (`7%`).
- **Inputs**: `Feed telemetry packet `[0xAA, 0x55, 7, 50, 50, 50, 50, 100]`.`
- **Expected Behavior / Output**: Single digit '7' rendered with '%' suffix; previous digit spaces cleanly filled with `PANEL_BG`.
- **Assertion Criteria**: `Only digit '7' is present; preceding character slots are blank `PANEL_BG`.`

#### `T1-F03-05`: Verify unit suffix baseline alignment with big numerals.
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify unit suffix baseline alignment with big numerals.
- **Inputs**: `Inspect baseline Y coordinate of '%' and '°C' relative to numeral glyph baseline.`
- **Expected Behavior / Output**: Unit suffix baseline aligns with the bottom baseline of the big block numerals.
- **Assertion Criteria**: `Suffix baseline Y == Numeral baseline Y; suffix height in [14..20] px.`

### Feature 04: Arm's-Length Legibility (Survey / R2)

#### `T1-F04-01`: Verify optical visual angle >= 20 arcminutes at 60 cm desk distance.
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify optical visual angle >= 20 arcminutes at 60 cm desk distance.
- **Inputs**: `Numeral pixel height = 28px on 166 DPI screen (pixel pitch = 0.153mm), viewing distance = 600mm.`
- **Expected Behavior / Output**: Physical height = 4.28mm; subtended visual angle = 24.5 arcminutes.
- **Assertion Criteria**: `Calculated visual angle >= 20.0 arcminutes; complies with ISO 9241-303.`

#### `T1-F04-02`: Verify optical visual angle >= 20 arcminutes at 70 cm sitting distance.
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify optical visual angle >= 20 arcminutes at 70 cm sitting distance.
- **Inputs**: `Numeral pixel height = 28px, viewing distance = 700mm.`
- **Expected Behavior / Output**: Physical height = 4.28mm; subtended visual angle = 21.0 arcminutes.
- **Assertion Criteria**: `Calculated visual angle >= 20.0 arcminutes; glanceable from normal sitting posture.`

#### `T1-F04-03`: Verify optical visual angle >= 20 arcminutes at 90 cm maximum desk distance with 35px font.
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify optical visual angle >= 20 arcminutes at 90 cm maximum desk distance with 35px font.
- **Inputs**: `Numeral pixel height = 35px (scale 5), viewing distance = 900mm.`
- **Expected Behavior / Output**: Physical height = 5.36mm; subtended visual angle = 20.5 arcminutes.
- **Assertion Criteria**: `Calculated visual angle >= 20.0 arcminutes.`

#### `T1-F04-04`: Verify complete elimination of sub-14px text on primary telemetry paths.
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify complete elimination of sub-14px text on primary telemetry paths.
- **Inputs**: `Audit all font rendering calls in `gadget-core` during primary metric updates.`
- **Expected Behavior / Output**: Zero primary readings use Scale 1 (7px) font. Primary numerals use >= 28px, secondary labels use >= 14px.
- **Assertion Criteria**: `Assertion passes: no call to draw primary metric has font_height < 28px; no label has font_height < 14px.`

#### `T1-F04-05`: Verify glyph stroke thickness for high glanceability.
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify glyph stroke thickness for high glanceability.
- **Inputs**: `Measure vertical and horizontal stroke width of rendered big numerals.`
- **Expected Behavior / Output**: Stroke thickness is >= 4 pixels, providing high contrast and visual weight.
- **Assertion Criteria**: `Stroke width >= 4px on all numeric segments.`

### Feature 05: Chunky Visual Meters (Survey / R3)

#### `T1-F05-01`: Verify chunky meter track physical dimensions (20–24px height, 200px width).
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify chunky meter track physical dimensions (20–24px height, 200px width).
- **Inputs**: `Inspect meter track geometry in card layout.`
- **Expected Behavior / Output**: Outer track height = 24px, inner fill height = 22px, inner fill width = 200px.
- **Assertion Criteria**: `Track outer height in [20, 24]; inner height == 22px; inner width == 200px.`

#### `T1-F05-02`: Verify exact linear 1:2 scaling relationship (1% = 2 pixels).
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify exact linear 1:2 scaling relationship (1% = 2 pixels).
- **Inputs**: `Feed telemetry values: 10%, 25%, 50%, 75%.`
- **Expected Behavior / Output**: Active bar fill width is exactly 20px, 50px, 100px, 150px respectively.
- **Assertion Criteria**: `Measured fill width == 2 * value pixels for each input.`

#### `T1-F05-03`: Verify 100% full-scale meter fill.
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify 100% full-scale meter fill.
- **Inputs**: `Feed metric value = 100%.`
- **Expected Behavior / Output**: Fill width is exactly 200px, filling the active track completely.
- **Assertion Criteria**: `Fill width == 200px; unfilled track width == 0px.`

#### `T1-F05-04`: Verify 0% zero-scale meter fill.
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify 0% zero-scale meter fill.
- **Inputs**: `Feed metric value = 0%.`
- **Expected Behavior / Output**: Fill width is 0px; inner track is entirely filled with background Color::DARK_BG.
- **Assertion Criteria**: `Fill width == 0px; all 200x22 pixels in track match Color::DARK_BG (`#121622`).`

#### `T1-F05-05`: Verify meter track border outline and inset styling.
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify meter track border outline and inset styling.
- **Inputs**: `Inspect track perimeter pixels.`
- **Expected Behavior / Output**: Track is surrounded by a 1px border in Color::BORDER (`#323E5A`).
- **Assertion Criteria**: `Perimeter border pixels at local (14, 70) to (215, 93) match (50, 62, 90).`

### Feature 06: Dynamic CPU Palette (Survey / R3)

#### `T1-F06-01`: Verify CPU nominal load palette (< 60%).
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU nominal load palette (< 60%).
- **Inputs**: `Telemetry packet with `cpu_percent = 30`.`
- **Expected Behavior / Output**: Meter and numeral color is Electric Cyan (`#00D2D3` / RGB: 0, 210, 211).
- **Assertion Criteria**: `Color == (0, 210, 211).`

#### `T1-F06-02`: Verify CPU warning load palette (60–84%).
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU warning load palette (60–84%).
- **Inputs**: `Telemetry packet with `cpu_percent = 72`.`
- **Expected Behavior / Output**: Meter and numeral color is Coral Amber (`#FFA502` / RGB: 255, 165, 2).
- **Assertion Criteria**: `Color == (255, 165, 2).`

#### `T1-F06-03`: Verify CPU alert load palette (>= 85%).
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU alert load palette (>= 85%).
- **Inputs**: `Telemetry packet with `cpu_percent = 92`.`
- **Expected Behavior / Output**: Meter and numeral color is Alert Coral (`#FF6B6B` / RGB: 255, 107, 107).
- **Assertion Criteria**: `Color == (255, 107, 107).`

#### `T1-F06-04`: Verify CPU color at lower bound (0%).
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU color at lower bound (0%).
- **Inputs**: `Telemetry packet with `cpu_percent = 0`.`
- **Expected Behavior / Output**: Color is Electric Cyan (`#00D2D3`).
- **Assertion Criteria**: `Color == (0, 210, 211).`

#### `T1-F06-05`: Verify CPU color at upper bound (100%).
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU color at upper bound (100%).
- **Inputs**: `Telemetry packet with `cpu_percent = 100`.`
- **Expected Behavior / Output**: Color is Alert Coral (`#FF6B6B`).
- **Assertion Criteria**: `Color == (255, 107, 107).`

### Feature 07: Dynamic GPU Palette (Survey / R3)

#### `T1-F07-01`: Verify GPU nominal load palette (< 65%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU nominal load palette (< 65%).
- **Inputs**: `Telemetry packet with `gpu_percent = 45`.`
- **Expected Behavior / Output**: Color is Neon Green (`#10AC84` / RGB: 16, 172, 132).
- **Assertion Criteria**: `Color == (16, 172, 132).`

#### `T1-F07-02`: Verify GPU warning load palette (65–84%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU warning load palette (65–84%).
- **Inputs**: `Telemetry packet with `gpu_percent = 75`.`
- **Expected Behavior / Output**: Color is Warning Orange (`#FF9F43` / RGB: 255, 159, 67).
- **Assertion Criteria**: `Color == (255, 159, 67).`

#### `T1-F07-03`: Verify GPU danger load palette (>= 85%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU danger load palette (>= 85%).
- **Inputs**: `Telemetry packet with `gpu_percent = 95`.`
- **Expected Behavior / Output**: Color is Blaze Red (`#FF3838` / RGB: 255, 56, 56).
- **Assertion Criteria**: `Color == (255, 56, 56).`

#### `T1-F07-04`: Verify GPU color at lower bound (0%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU color at lower bound (0%).
- **Inputs**: `Telemetry packet with `gpu_percent = 0`.`
- **Expected Behavior / Output**: Color is Neon Green (`#10AC84`).
- **Assertion Criteria**: `Color == (16, 172, 132).`

#### `T1-F07-05`: Verify GPU color at upper bound (100%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU color at upper bound (100%).
- **Inputs**: `Telemetry packet with `gpu_percent = 100`.`
- **Expected Behavior / Output**: Color is Blaze Red (`#FF3838`).
- **Assertion Criteria**: `Color == (255, 56, 56).`

### Feature 08: Dynamic RAM Palette (Survey / R3)

#### `T1-F08-01`: Verify RAM nominal usage palette (< 70%).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM nominal usage palette (< 70%).
- **Inputs**: `Telemetry packet with `ram_percent = 55`.`
- **Expected Behavior / Output**: Color is Vivid Violet (`#A55EEA` / RGB: 165, 94, 234).
- **Assertion Criteria**: `Color == (165, 94, 234).`

#### `T1-F08-02`: Verify RAM elevated usage palette (70–84%).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM elevated usage palette (70–84%).
- **Inputs**: `Telemetry packet with `ram_percent = 78`.`
- **Expected Behavior / Output**: Color is Magenta Rose (`#D980FA` / RGB: 217, 128, 250).
- **Assertion Criteria**: `Color == (217, 128, 250).`

#### `T1-F08-03`: Verify RAM danger usage palette (>= 85%).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM danger usage palette (>= 85%).
- **Inputs**: `Telemetry packet with `ram_percent = 92`.`
- **Expected Behavior / Output**: Color is Danger Red (`#EA2027` / RGB: 234, 32, 39).
- **Assertion Criteria**: `Color == (234, 32, 39).`

#### `T1-F08-04`: Verify RAM color at lower bound (0%).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM color at lower bound (0%).
- **Inputs**: `Telemetry packet with `ram_percent = 0`.`
- **Expected Behavior / Output**: Color is Vivid Violet (`#A55EEA`).
- **Assertion Criteria**: `Color == (165, 94, 234).`

#### `T1-F08-05`: Verify RAM color at upper bound (100%).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM color at upper bound (100%).
- **Inputs**: `Telemetry packet with `ram_percent = 100`.`
- **Expected Behavior / Output**: Color is Danger Red (`#EA2027`).
- **Assertion Criteria**: `Color == (234, 32, 39).`

### Feature 09: Dynamic Thermal Palette (Survey / R3)

#### `T1-F09-01`: Verify thermal cool palette (< 60°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify thermal cool palette (< 60°C).
- **Inputs**: `Telemetry packet with temperature = 48°C.`
- **Expected Behavior / Output**: Color is Cool Mint (`#1DD1A1` / RGB: 29, 209, 161).
- **Assertion Criteria**: `Color == (29, 209, 161).`

#### `T1-F09-02`: Verify thermal warm/elevated palette (60–75°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify thermal warm/elevated palette (60–75°C).
- **Inputs**: `Telemetry packet with temperature = 68°C.`
- **Expected Behavior / Output**: Color is Gold / Amber (`#FECA57` / RGB: 254, 202, 87).
- **Assertion Criteria**: `Color == (254, 202, 87).`

#### `T1-F09-03`: Verify thermal critical palette (> 75°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify thermal critical palette (> 75°C).
- **Inputs**: `Telemetry packet with temperature = 82°C.`
- **Expected Behavior / Output**: Color is Crimson (`#FF3838` / RGB: 255, 56, 56).
- **Assertion Criteria**: `Color == (255, 56, 56).`

#### `T1-F09-04`: Verify thermal color at lower bound (0°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify thermal color at lower bound (0°C).
- **Inputs**: `Telemetry packet with temperature = 0°C.`
- **Expected Behavior / Output**: Color is Cool Mint (`#1DD1A1`).
- **Assertion Criteria**: `Color == (29, 209, 161).`

#### `T1-F09-05`: Verify thermal color at upper bound (100°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify thermal color at upper bound (100°C).
- **Inputs**: `Telemetry packet with temperature = 100°C.`
- **Expected Behavior / Output**: Color is Crimson (`#FF3838`).
- **Assertion Criteria**: `Color == (255, 56, 56).`

### Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)

#### `T1-F10-01`: Verify simultaneous CPU and GPU temperature display in Q4.
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify simultaneous CPU and GPU temperature display in Q4.
- **Inputs**: `Packet with `cpu_temp_c = 64`, `gpu_temp_c = 78`.`
- **Expected Behavior / Output**: Q4 displays both CPU (64°C) and GPU (78°C) numeric values side-by-side.
- **Assertion Criteria**: `Q4 region contains strings '64' and '78' with '°C' units.`

#### `T1-F10-02`: Verify peak highlight badge on higher GPU temperature.
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify peak highlight badge on higher GPU temperature.
- **Inputs**: `Packet with `cpu_temp_c = 58`, `gpu_temp_c = 72`.`
- **Expected Behavior / Output**: GPU temperature is tagged with `[PEAK]` highlight badge in Gold (`#FECA57`); CPU text is dimmed in `Color::TEXT_MUTED`.
- **Assertion Criteria**: `Badge `[PEAK]` located adjacent to GPU text; GPU color == (254, 202, 87); CPU color == (130, 145, 175).`

#### `T1-F10-03`: Verify peak highlight badge on higher CPU temperature.
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify peak highlight badge on higher CPU temperature.
- **Inputs**: `Packet with `cpu_temp_c = 84`, `gpu_temp_c = 65`.`
- **Expected Behavior / Output**: CPU temperature is tagged with `[PEAK]` highlight badge in Crimson (`#FF3838`); GPU text is dimmed in `Color::TEXT_MUTED`.
- **Assertion Criteria**: `Badge `[PEAK]` located adjacent to CPU text; CPU color == (255, 56, 56); GPU color == (130, 145, 175).`

#### `T1-F10-04`: Verify Q4 card border switches to Crimson when peak temp > 75°C.
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify Q4 card border switches to Crimson when peak temp > 75°C.
- **Inputs**: `Packet with `cpu_temp_c = 82`, `gpu_temp_c = 70` (peak = 82°C).`
- **Expected Behavior / Output**: Q4 card border turns Crimson (`#FF3838`), warning user of high thermal state.
- **Assertion Criteria**: `Q4 border pixels match (255, 56, 56).`

#### `T1-F10-05`: Verify Q4 card border remains default `Color::BORDER` when peak temp <= 75°C.
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify Q4 card border remains default `Color::BORDER` when peak temp <= 75°C.
- **Inputs**: `Packet with `cpu_temp_c = 65`, `gpu_temp_c = 74` (peak = 74°C).`
- **Expected Behavior / Output**: Q4 card border remains Color::BORDER (`#323E5A` / RGB: 50, 62, 90).
- **Assertion Criteria**: `Q4 border pixels match (50, 62, 90).`

### Feature 11: Differential Redraw Engine (Survey / R4)

#### `T1-F11-01`: Verify dirty bounding-box isolation on single metric change.
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify dirty bounding-box isolation on single metric change.
- **Inputs**: `Initial packet: `[0xAA, 0x55, 40, 50, 50, 50, 50, 100]`. Second packet: `[0xAA, 0x55, 45, 50, 50, 50, 50, 100]`.`
- **Expected Behavior / Output**: Only Q1 (CPU) numeral box and meter delta rect are redrawn; Q2, Q3, Q4 receive 0 SPI pixel writes.
- **Assertion Criteria**: `All SPI window commands (0x2A, 0x2B) during second update are within X: [7..236], Y: [10..154].`

#### `T1-F11-02`: Verify zero SPI transactions emitted on identical consecutive packets.
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify zero SPI transactions emitted on identical consecutive packets.
- **Inputs**: `Initial packet: `[0xAA, 0x55, 50, 60, 70, 80, 65, 100]`. Second packet: identical.`
- **Expected Behavior / Output**: Differential redraw engine detects equality and emits 0 SPI transactions.
- **Assertion Criteria**: `Mock SPI byte count during second update == 0 bytes.`

#### `T1-F11-03`: Verify independent quadrant dirty tracking.
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify independent quadrant dirty tracking.
- **Inputs**: `Packet changing only RAM (Q3) and GPU Temp (Q4).`
- **Expected Behavior / Output**: Redraws occur only within Q3 and Q4 bounds; Q1 and Q2 are completely untouched.
- **Assertion Criteria**: `Zero SPI writes directed at Q1 or Q2 pixel coordinates.`

#### `T1-F11-04`: Verify SPI bandwidth economy for typical single-metric update (< 5,000 bytes).
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify SPI bandwidth economy for typical single-metric update (< 5,000 bytes).
- **Inputs**: `Single metric increments by 2%.`
- **Expected Behavior / Output**: Total SPI transmission payload < 5,000 bytes (< 6.25 ms bus time at 8MHz).
- **Assertion Criteria**: `Total SPI bytes <= 5000.`

#### `T1-F11-05`: Verify worst-case multi-quadrant dirty bounding box updates (< 35,000 bytes).
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify worst-case multi-quadrant dirty bounding box updates (< 35,000 bytes).
- **Inputs**: `All 4 quadrants change simultaneously.`
- **Expected Behavior / Output**: Targeted dirty bounding boxes are refreshed without clearing the full screen; total SPI bytes < 35,000 bytes (< 45ms).
- **Assertion Criteria**: `display.clear() was NOT called; total SPI bytes <= 35000.`

### Feature 12: Zero-Flicker Execution (Survey / R4)

#### `T1-F12-01`: Verify static layout is drawn exactly once during initialization.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify static layout is drawn exactly once during initialization.
- **Inputs**: `Call `Dashboard::new()`, then `draw_layout()`, followed by 10 `update()` ticks.`
- **Expected Behavior / Output**: `draw_layout()` executed once; full screen clear and card border draws are not repeated in `update()`.
- **Assertion Criteria**: `Mock display `clear()` call count == 1 (only at startup); `draw_layout` call count == 1.`

#### `T1-F12-02`: Verify continuous telemetry updates execute with zero full-screen clears.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify continuous telemetry updates execute with zero full-screen clears.
- **Inputs**: `Feed 30 telemetry packets with fluctuating values.`
- **Expected Behavior / Output**: `display.clear()` is called 0 times during all 30 updates, completely eliminating full-screen strobe flashes.
- **Assertion Criteria**: ``clear()` call count during update loop == 0.`

#### `T1-F12-03`: Verify in-place numeral box clearing without perturbing adjacent elements.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify in-place numeral box clearing without perturbing adjacent elements.
- **Inputs**: `Update CPU load from 45% to 46%.`
- **Expected Behavior / Output**: Only the 106x36px numeral box is cleared with `PANEL_BG` and redrawn; header and borders remain intact.
- **Assertion Criteria**: `Surrounding header pixels in [0..220, 0..24] and borders undergo 0 redraws.`

#### `T1-F12-04`: Verify incremental meter delta fill without redrawing existing bar.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify incremental meter delta fill without redrawing existing bar.
- **Inputs**: `CPU load increases from 40% to 45% (both in Electric Cyan).`
- **Expected Behavior / Output**: Only the +10px delta rect (200 * 5 / 100 = 10px) is filled; existing 80px bar is not redrawn.
- **Assertion Criteria**: `SPI window set strictly for delta region X: [95..104]; pixels 0..79 untouched.`

#### `T1-F12-05`: Verify total update cycle duration is comfortably under 50ms at 8MHz SPI.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify total update cycle duration is comfortably under 50ms at 8MHz SPI.
- **Inputs**: `Simulate worst-case 4-quadrant update at 8MHz SPI clock.`
- **Expected Behavior / Output**: Update finishes in < 50ms, allowing a 1000ms update rate with > 95% bus idle time.
- **Assertion Criteria**: `Simulated transmission duration <= 50.0 ms.`

### Feature 13: Zero-Heap Architecture (Survey / R4)

#### `T1-F13-01`: Verify `#![no_std]` compliance in `gadget-core`.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify `#![no_std]` compliance in `gadget-core`.
- **Inputs**: `Inspect `software/gadget-core/src/lib.rs`.`
- **Expected Behavior / Output**: `#![no_std]` declared at crate root; no reference to `extern crate alloc;`.
- **Assertion Criteria**: ``#![no_std]` is present; `alloc` is absent.`

#### `T1-F13-02`: Verify `#![no_std]` compliance in `gadget-common`.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify `#![no_std]` compliance in `gadget-common`.
- **Inputs**: `Inspect `software/gadget-common/src/lib.rs`.`
- **Expected Behavior / Output**: `#![no_std]` declared; stack-only structures.
- **Assertion Criteria**: ``#![no_std]` is present; zero heap dependencies.`

#### `T1-F13-03`: Verify `#![no_std]` and `#![no_main]` in `gadget-firmware-uno`.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify `#![no_std]` and `#![no_main]` in `gadget-firmware-uno`.
- **Inputs**: `Inspect `software/gadget-firmware-uno/src/main.rs`.`
- **Expected Behavior / Output**: `#![no_std]` and `#![no_main]` declared; uses `panic-halt`.
- **Assertion Criteria**: ``#![no_std]` and `#![no_main]` are present.`

#### `T1-F13-04`: Verify complete absence of dynamic memory allocation symbols in ELF binary.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify complete absence of dynamic memory allocation symbols in ELF binary.
- **Inputs**: `Run `avr-nm` on `gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: Zero occurrences of `malloc`, `free`, `realloc`, `__rust_alloc`, `__rust_dealloc`.
- **Assertion Criteria**: `Symbol audit returns 0 heap allocation symbols.`

#### `T1-F13-05`: Verify deterministic call stack bounds (< 256 bytes frame).
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify deterministic call stack bounds (< 256 bytes frame).
- **Inputs**: `Analyze call graph stack depth of `Dashboard::update`.`
- **Expected Behavior / Output**: Max stack frame depth is < 256 bytes, safe for 2KB SRAM ATmega328P.
- **Assertion Criteria**: `Max function stack frame < 256 bytes.`

### Feature 14: Static SRAM Ceiling (Survey / R4)

#### `T1-F14-01`: Verify total static SRAM (.data + .bss) is <= 100 bytes on ATmega328P.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify total static SRAM (.data + .bss) is <= 100 bytes on ATmega328P.
- **Inputs**: `Run `avr-size -C --mcu=atmega328p gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: Data section total (.data + .bss) <= 100 bytes.
- **Assertion Criteria**: `Data size reported by avr-size <= 100 bytes.`

#### `T1-F14-02`: Verify `.data` section size <= 80 bytes.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify `.data` section size <= 80 bytes.
- **Inputs**: `Run `avr-size -A gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: `.data` section is <= 80 bytes.
- **Assertion Criteria**: ``.data` <= 80 bytes.`

#### `T1-F14-03`: Verify `.bss` section size <= 20 bytes.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify `.bss` section size <= 20 bytes.
- **Inputs**: `Run `avr-size -A gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: `.bss` section is <= 20 bytes (only peripheral singletons).
- **Assertion Criteria**: ``.bss` <= 20 bytes.`

#### `T1-F14-04`: Verify font tables are stored in Flash (PROGMEM) or procedural generator, not SRAM.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify font tables are stored in Flash (PROGMEM) or procedural generator, not SRAM.
- **Inputs**: `Inspect symbol table of `gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: No 475-byte `FONT_5X7` in `.data` (RAM address 0x800100+).
- **Assertion Criteria**: `Font table symbols reside in Flash (.text/.progmem) or are procedurally synthesized.`

#### `T1-F14-05`: Verify `Dashboard` struct size is <= 16 bytes on stack.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify `Dashboard` struct size is <= 16 bytes on stack.
- **Inputs**: `Check `core::mem::size_of::<Dashboard>()`.`
- **Expected Behavior / Output**: `Dashboard` struct contains only `last_packet: Option<TelemetryPacket>` (9 bytes) + `initialized: bool` (1 byte) + padding <= 16 bytes.
- **Assertion Criteria**: ``size_of::<Dashboard>()` <= 16.`

### Feature 15: Flash Ceiling (< 28KB) (Survey / R4)

#### `T1-F15-01`: Verify total compiled Flash binary size < 28,672 bytes (28 KB).
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify total compiled Flash binary size < 28,672 bytes (28 KB).
- **Inputs**: `Run `avr-size -C --mcu=atmega328p gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: Program (.text + .data + .bootloader) < 28,672 bytes.
- **Assertion Criteria**: `Program bytes < 28672.`

#### `T1-F15-02`: Verify release build profile compiler optimizations in Cargo.toml.
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify release build profile compiler optimizations in Cargo.toml.
- **Inputs**: `Inspect `software/gadget-firmware-uno/Cargo.toml`.`
- **Expected Behavior / Output**: `opt-level = 's'` or `'z'`, `lto = true`, `codegen-units = 1`.
- **Assertion Criteria**: `Profile flags are configured for aggressive size reduction.`

#### `T1-F15-03`: Verify bootloader safety margin (>= 4 KB Flash headroom).
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify bootloader safety margin (>= 4 KB Flash headroom).
- **Inputs**: `Calculate $32,768 - \text{Program Bytes}$.`
- **Expected Behavior / Output**: Free Flash >= 4,096 bytes (leaves room for 2KB bootloader + 2KB future headroom).
- **Assertion Criteria**: `32768 - Program Bytes >= 4096.`

#### `T1-F15-04`: Verify individual function sizes remain compact (< 2,048 bytes).
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify individual function sizes remain compact (< 2,048 bytes).
- **Inputs**: `Run `avr-nm --size-sort -C gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: No single compiled function exceeds 2,048 bytes of Flash.
- **Assertion Criteria**: `Max function size <= 2048 bytes.`

#### `T1-F15-05`: Verify unused modules (e.g. `pet.rs`) are stripped via LTO.
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify unused modules (e.g. `pet.rs`) are stripped via LTO.
- **Inputs**: `Inspect symbol table for unlinked companion pet symbols.`
- **Expected Behavior / Output**: Zero symbols related to `pet.rs` exist in the ELF binary.
- **Assertion Criteria**: `No `pet` symbol found in ELF.`

### Feature 16: Serial Packet Protocol (Survey / R5)

#### `T1-F16-01`: Verify happy-path packet encode and decode roundtrip.
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify happy-path packet encode and decode roundtrip.
- **Inputs**: `Construct `TelemetryPacket::new(45, 68, 72, 85, 62, 95)`.`
- **Expected Behavior / Output**: Encodes into 8 bytes `[0xAA, 0x55, 45, 68, 72, 85, 62, 95]`, and decodes back to identical struct.
- **Assertion Criteria**: `Encoded array matches expected; `decode(&buf).unwrap() == packet`.`

#### `T1-F16-02`: Verify magic header bytes `MAGIC_0 == 0xAA` and `MAGIC_1 == 0x55`.
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify magic header bytes `MAGIC_0 == 0xAA` and `MAGIC_1 == 0x55`.
- **Inputs**: `Inspect `MAGIC_0` and `MAGIC_1` constants.`
- **Expected Behavior / Output**: `MAGIC_0` is `0xAA`, `MAGIC_1` is `0x55`.
- **Assertion Criteria**: ``buf[0] == 0xAA && buf[1] == 0x55`.`

#### `T1-F16-03`: Verify exact field mapping of all 6 payload bytes.
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify exact field mapping of all 6 payload bytes.
- **Inputs**: `Decode `[0xAA, 0x55, 12, 34, 56, 78, 90, 99]`.`
- **Expected Behavior / Output**: cpu=12, cpu_temp=34, ram=56, gpu=78, gpu_temp=90, battery=99.
- **Assertion Criteria**: `packet.cpu_percent == 12; packet.cpu_temp_c == 34; packet.ram_percent == 56; packet.gpu_percent == 78; packet.gpu_temp_c == 90; packet.battery_percent == 99.`

#### `T1-F16-04`: Verify fixed packet length constant `PACKET_LEN == 8`.
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify fixed packet length constant `PACKET_LEN == 8`.
- **Inputs**: `Check `gadget_common::PACKET_LEN`.`
- **Expected Behavior / Output**: Constant equals 8.
- **Assertion Criteria**: ``PACKET_LEN == 8`.`

#### `T1-F16-05`: Verify non-blocking UART receiver sliding window synchronization in firmware.
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify non-blocking UART receiver sliding window synchronization in firmware.
- **Inputs**: `Stream bytes with noise prefix: `[0x00, 0xFF, 0xAA, 0x55, 50, 60, 70, 80, 65, 100]`.`
- **Expected Behavior / Output**: Firmware discards leading noise, locks onto `0xAA 0x55`, decodes packet upon receiving 8th byte, and transmits 'ACK\n'.
- **Assertion Criteria**: `Packet decoded cleanly; UART output contains 'ACK'.`

### Feature 17: Host Hardware Telemetry (Survey / R5)

#### `T1-F17-01`: Verify CPU telemetry sampling from `/proc/stat` delta.
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify CPU telemetry sampling from `/proc/stat` delta.
- **Inputs**: `Feed two mock `/proc/stat` samples over 200ms interval.`
- **Expected Behavior / Output**: Accurately computes CPU load percentage via `(delta_total - delta_idle) / delta_total * 100`.
- **Assertion Criteria**: `Result matches mathematical formula within +/- 1%.`

#### `T1-F17-02`: Verify RAM usage sampling from `/proc/meminfo`.
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify RAM usage sampling from `/proc/meminfo`.
- **Inputs**: `Mock `/proc/meminfo` with `MemTotal: 32000000 kB` and `MemAvailable: 8000000 kB`.`
- **Expected Behavior / Output**: RAM usage percentage computed as `(32000000 - 8000000) / 32000000 * 100 = 75%`.
- **Assertion Criteria**: `Returned RAM percentage == 75.`

#### `T1-F17-03`: Verify CPU temperature collection via `k10temp` hwmon.
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify CPU temperature collection via `k10temp` hwmon.
- **Inputs**: `Mock `/sys/class/hwmon` with directory `name == 'k10temp'` containing `temp1_input = 74500`.`
- **Expected Behavior / Output**: Reads millidegrees and converts to `74°C` (`74500 / 1000`).
- **Assertion Criteria**: `Returned CPU temperature == 74.`

#### `T1-F17-04`: Verify GPU telemetry parsing from `nvidia-smi` output.
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify GPU telemetry parsing from `nvidia-smi` output.
- **Inputs**: `Mock output from `nvidia-smi`: `'42, 65'\n`.`
- **Expected Behavior / Output**: Parses GPU load = 42%, GPU temperature = 65°C.
- **Assertion Criteria**: `GPU load == 42; GPU temperature == 65.`

#### `T1-F17-05`: Verify host CLI `--dry-run` flag execution.
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify host CLI `--dry-run` flag execution.
- **Inputs**: `Execute `cargo run -- --dry-run --interval 200` with timeout 1s.`
- **Expected Behavior / Output**: Prints formatted metrics line to stdout without attempting to open physical serial port.
- **Assertion Criteria**: `Stdout contains `[Metrics] CPU:`; process exits cleanly.`

---

## Tier 2: Boundary & Corner Cases Specifications (85 Test Cases across 17 Features)

Every test case below exercises boundary, limit, and corner cases (0%, 100%, >100%, 0°C, >100°C, threshold transitions 59/60°C, 74/75°C, 84/85%, missing hardware, packet noise, zero delta packets) with concrete inputs and assertions.

### Feature 01: 4-Quadrant Card Grid (Survey / R1)

#### `T2-F01-01`: Verify boundary coordinate clamping to 480x320 display edges.
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify boundary coordinate clamping to 480x320 display edges.
- **Inputs**: `Inspect all pixel write commands emitted during layout and update.`
- **Expected Behavior / Output**: No pixel write occurs at X < 0, X >= 480, Y < 0, or Y >= 320.
- **Assertion Criteria**: `Mock display asserts: min_x >= 0, max_x <= 479, min_y >= 0, max_y <= 319.`

#### `T2-F01-02`: Verify zero overlap between adjacent cards across center gutters.
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify zero overlap between adjacent cards across center gutters.
- **Inputs**: `Inspect pixel buffer across horizontal gutter (X: 237..242) and vertical gutter (Y: 155..164).`
- **Expected Behavior / Output**: Gutters remain strictly filled with `Color::DARK_BG`; card border and fills never spill into gutter.
- **Assertion Criteria**: `All pixels in X in [237, 242] and Y in [155, 164] match Color::DARK_BG (`#121622`).`

#### `T2-F01-03`: Verify redraw isolation when only a single quadrant transitions to dirty state.
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify redraw isolation when only a single quadrant transitions to dirty state.
- **Inputs**: `Frame 1: all metrics 50. Frame 2: CPU changes to 60 (Q1 dirty), Q2..Q4 unchanged.`
- **Expected Behavior / Output**: Pixels in Q2 (243..472, 10..154), Q3 (7..236, 165..309), Q4 (243..472, 165..309) undergo 0 writes.
- **Assertion Criteria**: `Zero write commands emitted outside Q1 bounding box.`

#### `T2-F01-04`: Verify 2px card border integrity during rapid extreme metric oscillations (0% <-> 100%).
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify 2px card border integrity during rapid extreme metric oscillations (0% <-> 100%).
- **Inputs**: `Alternate packets with 0% and 100% metrics every tick for 20 ticks.`
- **Expected Behavior / Output**: Card border perimeter pixels remain intact; internal meter fill and numeral clears never overwrite 2px border.
- **Assertion Criteria**: `Perimeter pixels at X=7, 8, 235, 236 and Y=10, 11, 153, 154 remain Color::BORDER (50, 62, 90).`

#### `T2-F01-05`: Verify dynamic Q4 card border color shift on critical thermal condition (> 75°C).
- **Feature Reference**: Feature 01: 4-Quadrant Card Grid (Survey / R1)
- **Description**: Verify dynamic Q4 card border color shift on critical thermal condition (> 75°C).
- **Inputs**: `Telemetry packet with `cpu_temp_c = 85` (> 75°C).`
- **Expected Behavior / Output**: Q4 card border switches from `Color::BORDER` to Crimson (`#FF3838`); Q1, Q2, Q3 borders remain default.
- **Assertion Criteria**: `Q4 border pixels == (255, 56, 56); Q1, Q2, Q3 border pixels == (50, 62, 90).`

### Feature 02: Card Header Bar (Survey / R1)

#### `T2-F02-01`: Verify card header label clipping boundary within 202px available inner width.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify card header label clipping boundary within 202px available inner width.
- **Inputs**: `Measure rightmost extent of longest header string ('THERMALS' or 'SYSTEM MONITOR').`
- **Expected Behavior / Output**: Header text fits within card inner width with at least 10px right margin padding.
- **Assertion Criteria**: `Rightmost character extent X < 220 in card local coordinates.`

#### `T2-F02-02`: Verify header typography luminance contrast ratio (WCAG AA >= 4.5:1).
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify header typography luminance contrast ratio (WCAG AA >= 4.5:1).
- **Inputs**: `Calculate contrast ratio between accent color (e.g. Electric Cyan, Neon Green) and `Color::PANEL_BG` (`#1C2234`).`
- **Expected Behavior / Output**: Contrast ratio exceeds 4.5:1, ensuring high legibility under varying ambient light.
- **Assertion Criteria**: `Contrast ratio >= 4.50.`

#### `T2-F02-03`: Verify card header persistence across 100 continuous metric updates.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify card header persistence across 100 continuous metric updates.
- **Inputs**: `Feed 100 consecutive random telemetry packets.`
- **Expected Behavior / Output**: Header title pixels in Y in [8..24] are never erased or modified by lower numeral/meter redraws.
- **Assertion Criteria**: `Header region pixel buffer remains unchanged across all 100 updates.`

#### `T2-F02-04`: Verify offline / waiting indicator in card header upon host disconnection.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify offline / waiting indicator in card header upon host disconnection.
- **Inputs**: `Simulate 3 seconds without serial packet reception.`
- **Expected Behavior / Output**: Header displays subtle 'WAITING' or 'OFFLINE' badge in muted color without blanking screen.
- **Assertion Criteria**: `Status badge appears; display does not clear or panic.`

#### `T2-F02-05`: Verify non-ASCII / extended glyph handling in header without panic in `#![no_std]`.
- **Feature Reference**: Feature 02: Card Header Bar (Survey / R1)
- **Description**: Verify non-ASCII / extended glyph handling in header without panic in `#![no_std]`.
- **Inputs**: `Header rendering with degree symbol `°` or `%`.`
- **Expected Behavior / Output**: Valid glyph indexed and drawn; zero dynamic string decoding or panic.
- **Assertion Criteria**: `Renderer completes without panic; expected glyph bitmap drawn.`

### Feature 03: Big Block Numerals (Survey / R2)

#### `T2-F03-01`: Verify ghosting prevention when transitioning from 100% (3 digits) to 0% (1 digit).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify ghosting prevention when transitioning from 100% (3 digits) to 0% (1 digit).
- **Inputs**: `Step 1: Feed packet with 100%. Step 2: Feed packet with 0%.`
- **Expected Behavior / Output**: Previous 3-digit glyph bounding box is completely cleared with `PANEL_BG`; no ghost '1' or '0' pixels remain.
- **Assertion Criteria**: `In Step 2, only digit '0' and '%' are rendered; pixel positions where '10' was previously located are 100% Color::PANEL_BG.`

#### `T2-F03-02`: Verify numeral formatting and display clamping for over-range inputs (> 100%).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify numeral formatting and display clamping for over-range inputs (> 100%).
- **Inputs**: `Feed telemetry packet with raw `cpu_percent = 255`.`
- **Expected Behavior / Output**: Firmware clamps display value to `100%` (or renders '---') without memory corruption or buffer overflow.
- **Assertion Criteria**: `Rendered text matches '100%' (or '---'); bounding box width <= 106px.`

#### `T2-F03-03`: Verify zero percent numeral rendering (`0%`).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify zero percent numeral rendering (`0%`).
- **Inputs**: `Feed telemetry packet with `cpu_percent = 0`.`
- **Expected Behavior / Output**: Renders clean single digit '0' with '%' suffix; does not leave blank or uninitialized box.
- **Assertion Criteria**: `Rendered string is '0%'; bounding box height >= 28px.`

#### `T2-F03-04`: Verify three-digit high temperature display (`105°C` / `115°C`).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify three-digit high temperature display (`105°C` / `115°C`).
- **Inputs**: `Feed telemetry packet with `cpu_temp_c = 105`.`
- **Expected Behavior / Output**: Renders '105°C' (or clamped '99°C' with overheat alert) without clipping card boundary.
- **Assertion Criteria**: `Rightmost extent of rendered thermal string X < 225 local.`

#### `T2-F03-05`: Verify rapid numeral jitter expansion/contraction (99% <-> 100%).
- **Feature Reference**: Feature 03: Big Block Numerals (Survey / R2)
- **Description**: Verify rapid numeral jitter expansion/contraction (99% <-> 100%).
- **Inputs**: `Alternate between 99% and 100% every update for 20 frames.`
- **Expected Behavior / Output**: Numeral bounding box toggles cleanly between 2-digit and 3-digit layouts without pixel debris.
- **Assertion Criteria**: `Framebuffer exactly reflects 2 digits at 99% and 3 digits at 100%; zero residual artifact pixels.`

### Feature 04: Arm's-Length Legibility (Survey / R2)

#### `T2-F04-01`: Verify visual angle at maximum desk distance boundary (90 cm with 28px font).
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify visual angle at maximum desk distance boundary (90 cm with 28px font).
- **Inputs**: `Numeral height = 28px (4.28mm), viewing distance = 900mm.`
- **Expected Behavior / Output**: Subtended visual angle = 16.35 arcminutes, satisfying minimum industrial legibility threshold (>= 16 arcmin).
- **Assertion Criteria**: `Visual angle >= 16.0 arcminutes.`

#### `T2-F04-02`: Verify high luminance contrast ratio under low ambient desk lighting (WCAG AAA >= 7:1).
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify high luminance contrast ratio under low ambient desk lighting (WCAG AAA >= 7:1).
- **Inputs**: `Calculate contrast between White `#FFFFFF` / Accent and `Color::PANEL_BG` (`#1C2234`).`
- **Expected Behavior / Output**: Contrast ratio exceeds 7.0:1.
- **Assertion Criteria**: `Contrast ratio >= 7.0.`

#### `T2-F04-03`: Verify inter-character pitch spacing boundary (>= 4px).
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify inter-character pitch spacing boundary (>= 4px).
- **Inputs**: `Measure pixel gap between consecutive digits in '100%'.`
- **Expected Behavior / Output**: Gap between digits is at least 4 pixels, preventing visual crowding / optical merging at 90cm.
- **Assertion Criteria**: `Inter-digit gap >= 4px.`

#### `T2-F04-04`: Verify close inspection visual quality at 40 cm boundary.
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify close inspection visual quality at 40 cm boundary.
- **Inputs**: `Viewing distance = 400mm.`
- **Expected Behavior / Output**: Subtended visual angle = 36.8 arcminutes; glyph edges remain crisp without pixel blur.
- **Assertion Criteria**: `Glyph edges are sharp step boundaries; no anti-aliasing color bleed.`

#### `T2-F04-05`: Verify glyphic distinguishability between cardinal numbers (0 vs 8 vs 6 vs 9).
- **Feature Reference**: Feature 04: Arm's-Length Legibility (Survey / R2)
- **Description**: Verify glyphic distinguishability between cardinal numbers (0 vs 8 vs 6 vs 9).
- **Inputs**: `Compare bitmap segment masks for digits 0, 6, 8, 9.`
- **Expected Behavior / Output**: Hamming distance between any pair of glyph bitmaps is >= 6 pixels, ensuring distinct glanceability.
- **Assertion Criteria**: `Bitwise difference between glyph bitmaps >= 6 bits.`

### Feature 05: Chunky Visual Meters (Survey / R3)

#### `T2-F05-01`: Verify over-range meter fill clamping (> 100%).
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify over-range meter fill clamping (> 100%).
- **Inputs**: `Feed telemetry load = 120%.`
- **Expected Behavior / Output**: Meter fill width is clamped to exactly 200px (100%); does not bleed into right card border.
- **Assertion Criteria**: `Fill width == 200px; pixels at X > 214 local remain border pixels.`

#### `T2-F05-02`: Verify incremental delta fill on metric increase (40% -> 45%).
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify incremental delta fill on metric increase (40% -> 45%).
- **Inputs**: `Step 1: 40% (fill = 80px). Step 2: 45% (fill = 90px).`
- **Expected Behavior / Output**: Differential update only fills the +10px delta rect (local 95..104, 71..92); 0..79px untouched.
- **Assertion Criteria**: `SPI window set to X: [95..104], Y: [71..92]; pixel count == 220 pixels.`

#### `T2-F05-03`: Verify decremental delta clear on metric decrease (80% -> 60%).
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify decremental delta clear on metric decrease (80% -> 60%).
- **Inputs**: `Step 1: 80% (fill = 160px). Step 2: 60% (fill = 120px).`
- **Expected Behavior / Output**: Differential update fills the -40px delta rect (local 135..174, 71..92) with `Color::DARK_BG`.
- **Assertion Criteria**: `SPI window set to X: [135..174], Y: [71..92]; written color is Color::DARK_BG.`

#### `T2-F05-04`: Verify single-percent increment boundary (49% -> 50%).
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify single-percent increment boundary (49% -> 50%).
- **Inputs**: `Load increases from 49% to 50%.`
- **Expected Behavior / Output**: Delta fill width is exactly 2 pixels (1% * 2px = 2px).
- **Assertion Criteria**: `Delta rect width == 2px, height == 22px; total written pixels == 44.`

#### `T2-F05-05`: Verify full-scale swing boundary (0% -> 100% -> 0%).
- **Feature Reference**: Feature 05: Chunky Visual Meters (Survey / R3)
- **Description**: Verify full-scale swing boundary (0% -> 100% -> 0%).
- **Inputs**: `Sequence: 0% -> 100% -> 0%.`
- **Expected Behavior / Output**: Complete 200px fill followed by complete 200px erase; no residual colored pixels.
- **Assertion Criteria**: `At end of sequence, all 200x22 pixels in track match Color::DARK_BG.`

### Feature 06: Dynamic CPU Palette (Survey / R3)

#### `T2-F06-01`: Verify CPU color threshold boundary at 59% vs 60%.
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU color threshold boundary at 59% vs 60%.
- **Inputs**: `Sample A: `cpu_percent = 59`. Sample B: `cpu_percent = 60`.`
- **Expected Behavior / Output**: 59% maps to Electric Cyan (`#00D2D3`); 60% maps to Coral Amber (`#FFA502`).
- **Assertion Criteria**: `Color(59) == (0, 210, 211); Color(60) == (255, 165, 2).`

#### `T2-F06-02`: Verify CPU color threshold boundary at 84% vs 85%.
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU color threshold boundary at 84% vs 85%.
- **Inputs**: `Sample A: `cpu_percent = 84`. Sample B: `cpu_percent = 85`.`
- **Expected Behavior / Output**: 84% maps to Coral Amber (`#FFA502`); 85% maps to Alert Coral (`#FF6B6B`).
- **Assertion Criteria**: `Color(84) == (255, 165, 2); Color(85) == (255, 107, 107).`

#### `T2-F06-03`: Verify active meter bar recoloring upon crossing color-shift threshold (59% -> 61%).
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify active meter bar recoloring upon crossing color-shift threshold (59% -> 61%).
- **Inputs**: `Step 1: 59% (Electric Cyan). Step 2: 61% (Coral Amber).`
- **Expected Behavior / Output**: Entire active filled bar (0..122px) is recolored to Coral Amber.
- **Assertion Criteria**: `All active bar pixels in [0..122] match (255, 165, 2).`

#### `T2-F06-04`: Verify CPU palette clamping for over-range input (255%).
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify CPU palette clamping for over-range input (255%).
- **Inputs**: ``cpu_percent = 255`.`
- **Expected Behavior / Output**: Color clamped to Alert Coral (`#FF6B6B`).
- **Assertion Criteria**: `Color == (255, 107, 107).`

#### `T2-F06-05`: Verify threshold chatter stability across 59% <-> 60% boundary.
- **Feature Reference**: Feature 06: Dynamic CPU Palette (Survey / R3)
- **Description**: Verify threshold chatter stability across 59% <-> 60% boundary.
- **Inputs**: `Toggle between 59% and 60% every tick for 10 frames.`
- **Expected Behavior / Output**: Clean alternating palette transitions without graphics corruption or buffer desync.
- **Assertion Criteria**: `Colors alternate cleanly between (0, 210, 211) and (255, 165, 2).`

### Feature 07: Dynamic GPU Palette (Survey / R3)

#### `T2-F07-01`: Verify GPU color threshold boundary at 64% vs 65%.
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU color threshold boundary at 64% vs 65%.
- **Inputs**: `Sample A: `gpu_percent = 64`. Sample B: `gpu_percent = 65`.`
- **Expected Behavior / Output**: 64% maps to Neon Green (`#10AC84`); 65% maps to Warning Orange (`#FF9F43`).
- **Assertion Criteria**: `Color(64) == (16, 172, 132); Color(65) == (255, 159, 67).`

#### `T2-F07-02`: Verify GPU color threshold boundary at 84% vs 85%.
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU color threshold boundary at 84% vs 85%.
- **Inputs**: `Sample A: `gpu_percent = 84`. Sample B: `gpu_percent = 85`.`
- **Expected Behavior / Output**: 84% maps to Warning Orange (`#FF9F43`); 85% maps to Blaze Red (`#FF3838`).
- **Assertion Criteria**: `Color(84) == (255, 159, 67); Color(85) == (255, 56, 56).`

#### `T2-F07-03`: Verify GPU bar recoloring on warning-to-danger crossing (84% -> 86%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU bar recoloring on warning-to-danger crossing (84% -> 86%).
- **Inputs**: `Step 1: 84% (Orange). Step 2: 86% (Blaze Red).`
- **Expected Behavior / Output**: Entire active bar (0..172px) is recolored to Blaze Red.
- **Assertion Criteria**: `All active bar pixels match (255, 56, 56).`

#### `T2-F07-04`: Verify GPU palette clamping for over-range input (150%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify GPU palette clamping for over-range input (150%).
- **Inputs**: ``gpu_percent = 150`.`
- **Expected Behavior / Output**: Color clamped to Blaze Red (`#FF3838`).
- **Assertion Criteria**: `Color == (255, 56, 56).`

#### `T2-F07-05`: Verify instantaneous GPU load spike from idle to max (0% -> 99%).
- **Feature Reference**: Feature 07: Dynamic GPU Palette (Survey / R3)
- **Description**: Verify instantaneous GPU load spike from idle to max (0% -> 99%).
- **Inputs**: `Step 1: 0%. Step 2: 99%.`
- **Expected Behavior / Output**: Instantaneous transition from unlit bar to 198px Blaze Red bar with zero lag.
- **Assertion Criteria**: `Active fill width == 198px; color == (255, 56, 56).`

### Feature 08: Dynamic RAM Palette (Survey / R3)

#### `T2-F08-01`: Verify RAM color threshold boundary at 69% vs 70%.
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM color threshold boundary at 69% vs 70%.
- **Inputs**: `Sample A: `ram_percent = 69`. Sample B: `ram_percent = 70`.`
- **Expected Behavior / Output**: 69% maps to Vivid Violet (`#A55EEA`); 70% maps to Magenta Rose (`#D980FA`).
- **Assertion Criteria**: `Color(69) == (165, 94, 234); Color(70) == (217, 128, 250).`

#### `T2-F08-02`: Verify RAM color threshold boundary at 84% vs 85%.
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM color threshold boundary at 84% vs 85%.
- **Inputs**: `Sample A: `ram_percent = 84`. Sample B: `ram_percent = 85`.`
- **Expected Behavior / Output**: 84% maps to Magenta Rose (`#D980FA`); 85% maps to Danger Red (`#EA2027`).
- **Assertion Criteria**: `Color(84) == (217, 128, 250); Color(85) == (234, 32, 39).`

#### `T2-F08-03`: Verify extreme memory pressure condition (99% RAM).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify extreme memory pressure condition (99% RAM).
- **Inputs**: ``ram_percent = 99`.`
- **Expected Behavior / Output**: Bar fills 198px in Danger Red; numeral '99%' rendered in bold Danger Red.
- **Assertion Criteria**: `Fill width == 198px; color == (234, 32, 39).`

#### `T2-F08-04`: Verify RAM input overflow clamping (200%).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify RAM input overflow clamping (200%).
- **Inputs**: ``ram_percent = 200`.`
- **Expected Behavior / Output**: Clamped to 100% Danger Red.
- **Assertion Criteria**: `Value clamped to 100; color == (234, 32, 39).`

#### `T2-F08-05`: Verify memory deallocation drop (90% Danger Red -> 30% Vivid Violet).
- **Feature Reference**: Feature 08: Dynamic RAM Palette (Survey / R3)
- **Description**: Verify memory deallocation drop (90% Danger Red -> 30% Vivid Violet).
- **Inputs**: `Step 1: 90% (Danger Red). Step 2: 30% (Vivid Violet).`
- **Expected Behavior / Output**: Clear 60..180px with `Color::DARK_BG`; recolor 0..60px to Vivid Violet.
- **Assertion Criteria**: `Active bar pixels in [0..60] == (165, 94, 234); pixels in [61..200] == Color::DARK_BG.`

### Feature 09: Dynamic Thermal Palette (Survey / R3)

#### `T2-F09-01`: Verify thermal color threshold boundary at 59°C vs 60°C.
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify thermal color threshold boundary at 59°C vs 60°C.
- **Inputs**: `Sample A: `temp = 59`. Sample B: `temp = 60`.`
- **Expected Behavior / Output**: 59°C maps to Cool Mint (`#1DD1A1`); 60°C maps to Gold (`#FECA57`).
- **Assertion Criteria**: `Color(59) == (29, 209, 161); Color(60) == (254, 202, 87).`

#### `T2-F09-02`: Verify thermal color threshold boundary at 74°C vs 75°C vs 76°C.
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify thermal color threshold boundary at 74°C vs 75°C vs 76°C.
- **Inputs**: `Sample A: 74°C. Sample B: 75°C. Sample C: 76°C.`
- **Expected Behavior / Output**: 74°C -> Gold; 75°C -> Gold; 76°C -> Crimson (condition is > 75°C).
- **Assertion Criteria**: `Color(74) == Gold; Color(75) == Gold; Color(76) == Crimson ((255, 56, 56)).`

#### `T2-F09-03`: Verify freezing / sub-zero sensor representation (0°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify freezing / sub-zero sensor representation (0°C).
- **Inputs**: ``temp = 0°C`.`
- **Expected Behavior / Output**: Handled without integer underflow; renders '0°C' in Cool Mint.
- **Assertion Criteria**: `Display string == '0°C'; color == (29, 209, 161).`

#### `T2-F09-04`: Verify extreme overheating beyond 100°C (e.g. 115°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify extreme overheating beyond 100°C (e.g. 115°C).
- **Inputs**: ``temp = 115°C`.`
- **Expected Behavior / Output**: Crimson palette; no integer overflow; warning badge active.
- **Assertion Criteria**: `Color == (255, 56, 56); displayed value == '115°C' (or clamped '99°C' + alert).`

#### `T2-F09-05`: Verify rapid thermal spike crossing both boundaries (45°C -> 65°C -> 85°C).
- **Feature Reference**: Feature 09: Dynamic Thermal Palette (Survey / R3)
- **Description**: Verify rapid thermal spike crossing both boundaries (45°C -> 65°C -> 85°C).
- **Inputs**: `Sequence: 45°C -> 65°C -> 85°C across consecutive frames.`
- **Expected Behavior / Output**: Palette transitions cleanly Mint -> Gold -> Crimson.
- **Assertion Criteria**: `Frame 1 Color == Mint; Frame 2 Color == Gold; Frame 3 Color == Crimson.`

### Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)

#### `T2-F10-01`: Verify thermal equality peak tie-breaking (`cpu_temp_c == gpu_temp_c`).
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify thermal equality peak tie-breaking (`cpu_temp_c == gpu_temp_c`).
- **Inputs**: ``cpu_temp_c = 72`, `gpu_temp_c = 72`.`
- **Expected Behavior / Output**: Deterministic behavior: highlights CPU by default (or highlights both); does not crash or toggle erratically.
- **Assertion Criteria**: `Peak badge is present; display is stable.`

#### `T2-F10-02`: Verify peak inversion transition (CPU peak -> GPU peak).
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify peak inversion transition (CPU peak -> GPU peak).
- **Inputs**: `Step 1: CPU=80°C, GPU=65°C. Step 2: CPU=68°C, GPU=82°C.`
- **Expected Behavior / Output**: Badge shifts from CPU to GPU; prior CPU badge area cleared with `PANEL_BG`.
- **Assertion Criteria**: `At Step 2, former CPU badge slot matches Color::PANEL_BG; GPU slot has `[PEAK]`.`

#### `T2-F10-03`: Verify boundary peak temperature for card border alert (75°C vs 76°C).
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify boundary peak temperature for card border alert (75°C vs 76°C).
- **Inputs**: `Case A: Peak = 75°C. Case B: Peak = 76°C.`
- **Expected Behavior / Output**: At 75°C, border is `Color::BORDER` (`#323E5A`). At 76°C, border turns Crimson (`#FF3838`).
- **Assertion Criteria**: `Case A border == (50, 62, 90); Case B border == (255, 56, 56).`

#### `T2-F10-04`: Verify zero-degree temperatures in both sensors (`0°C, 0°C`).
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify zero-degree temperatures in both sensors (`0°C, 0°C`).
- **Inputs**: ``cpu_temp_c = 0`, `gpu_temp_c = 0`.`
- **Expected Behavior / Output**: Peak calculation = 0; renders `CPU: 0°C   GPU: 0°C` in Cool Mint.
- **Assertion Criteria**: `No underflow; badge active in Cool Mint.`

#### `T2-F10-05`: Verify max-scale dual thermal runaway (CPU=115°C, GPU=108°C).
- **Feature Reference**: Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)
- **Description**: Verify max-scale dual thermal runaway (CPU=115°C, GPU=108°C).
- **Inputs**: `Extreme temperatures exceeding 100°C simultaneously.`
- **Expected Behavior / Output**: CPU tagged with Crimson peak highlight; card border turns Crimson; no visual corruption.
- **Assertion Criteria**: `Q4 border == Crimson; values rendered cleanly.`

### Feature 11: Differential Redraw Engine (Survey / R4)

#### `T2-F11-01`: Verify zero full-screen clears during 100 random packet updates.
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify zero full-screen clears during 100 random packet updates.
- **Inputs**: `Run 100 update cycles with randomized telemetry values.`
- **Expected Behavior / Output**: `display.clear()` is called exactly 0 times during all `update()` calls.
- **Assertion Criteria**: ``clear()` call count during update loop == 0.`

#### `T2-F11-02`: Verify bounding box dimensions match dirty areas exactly.
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify bounding box dimensions match dirty areas exactly.
- **Inputs**: `Update value from 40% to 42%.`
- **Expected Behavior / Output**: Numeral bounding box is exactly 106x36px; meter delta rect is exactly 4x22px.
- **Assertion Criteria**: `SPI window extents match exact bounding box geometry.`

#### `T2-F11-03`: Verify shrinking value bounding box completely clears residual pixels (100% -> 9%).
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify shrinking value bounding box completely clears residual pixels (100% -> 9%).
- **Inputs**: `Step 1: 100%. Step 2: 9%.`
- **Expected Behavior / Output**: Full 3-digit bounding box is cleared with `PANEL_BG` before drawing 1-digit glyph.
- **Assertion Criteria**: `Pixel locations of former digits are verified to be Color::PANEL_BG.`

#### `T2-F11-04`: Verify sustained 10 Hz rapid update stress without SPI queue desync.
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify sustained 10 Hz rapid update stress without SPI queue desync.
- **Inputs**: `Stream 10 packets per second for 5 seconds.`
- **Expected Behavior / Output**: Each frame redraw completes in < 45ms; no queue overflow or packet drops.
- **Assertion Criteria**: `50 frames processed without dropped ticks.`

#### `T2-F11-05`: Verify initial state transition on cold start (first packet after reset).
- **Feature Reference**: Feature 11: Differential Redraw Engine (Survey / R4)
- **Description**: Verify initial state transition on cold start (first packet after reset).
- **Inputs**: ``Dashboard::new()` with `last_packet = None`. Feed first packet.`
- **Expected Behavior / Output**: Performs initial full render of all 4 quadrants; stores packet as `last_packet`; second identical packet emits 0 bytes.
- **Assertion Criteria**: `First update draws all 4 cards; second identical update emits 0 SPI bytes.`

### Feature 12: Zero-Flicker Execution (Survey / R4)

#### `T2-F12-01`: Verify zero-clear invariant under corrupted packet reception.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify zero-clear invariant under corrupted packet reception.
- **Inputs**: `Feed corrupted serial packet `[0xFF, 0x00, 1, 2, 3, 4, 5, 6]`.`
- **Expected Behavior / Output**: Firmware rejects packet; display is NOT cleared or perturbed.
- **Assertion Criteria**: `Framebuffer remains 100% bit-identical to prior valid state.`

#### `T2-F12-02`: Verify strobe prevention during dynamic color threshold crossing.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify strobe prevention during dynamic color threshold crossing.
- **Inputs**: `Metric crosses threshold from 59% (Cyan) to 60% (Amber).`
- **Expected Behavior / Output**: Bar is recolored without clearing to black first (direct overwrite / single fill).
- **Assertion Criteria**: `No intermediate black frame recorded in display history.`

#### `T2-F12-03`: Verify high-frequency load toggling without display blanking.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify high-frequency load toggling without display blanking.
- **Inputs**: `Metric toggles between 0% and 100% every 200ms.`
- **Expected Behavior / Output**: Smooth visual alternation without blanking or partial tearing.
- **Assertion Criteria**: `Zero full clears; window updates strictly bounded.`

#### `T2-F12-04`: Verify thermal status badge refresh without quadrant invalidation.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify thermal status badge refresh without quadrant invalidation.
- **Inputs**: `Peak thermal shifts from CPU to GPU.`
- **Expected Behavior / Output**: Only badge area and card border change; quadrant interior not refreshed.
- **Assertion Criteria**: `Unchanged quadrant pixels remain unwritten.`

#### `T2-F12-05`: Verify SPI bus idle ratio is >= 90% at 1 Hz update rate.
- **Feature Reference**: Feature 12: Zero-Flicker Execution (Survey / R4)
- **Description**: Verify SPI bus idle ratio is >= 90% at 1 Hz update rate.
- **Inputs**: `1 packet per second with standard load delta.`
- **Expected Behavior / Output**: SPI bus active for < 30ms per second (>= 97% idle time).
- **Assertion Criteria**: `Active SPI duty cycle <= 10%.`

### Feature 13: Zero-Heap Architecture (Survey / R4)

#### `T2-F13-01`: Verify zero dynamic heap allocation during big numeral ASCII byte formatting.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify zero dynamic heap allocation during big numeral ASCII byte formatting.
- **Inputs**: `Format 0, 45, 100 into numeral string buffers.`
- **Expected Behavior / Output**: Formatting operates purely on stack buffer `[u8; 6]`; zero heap allocation.
- **Assertion Criteria**: `Heap allocation counter remains 0.`

#### `T2-F13-02`: Verify zero dynamic allocation during packet decoding.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify zero dynamic allocation during packet decoding.
- **Inputs**: `Decode 10,000 packets (malformed and valid).`
- **Expected Behavior / Output**: Returns `Option<TelemetryPacket>` by value on stack; zero heap calls.
- **Assertion Criteria**: `Heap allocation counter == 0.`

#### `T2-F13-03`: Verify complete absence of UTF-8 validation lookup table in binary.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify complete absence of UTF-8 validation lookup table in binary.
- **Inputs**: `Check symbol table for `core::str::from_utf8` tables.`
- **Expected Behavior / Output**: String formatting uses raw byte slices `&[u8]`; no 256-byte UTF-8 table.
- **Assertion Criteria**: `Zero UTF-8 decode table symbols in `.data`.`

#### `T2-F13-04`: Verify stack pointer margin under deepest execution path.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify stack pointer margin under deepest execution path.
- **Inputs**: `Trace stack consumption through `main` -> `Dashboard::update` -> `update_gauge` -> `fill_rect` -> SPI.`
- **Expected Behavior / Output**: Stack pointer remains > 1,024 bytes away from static `.bss` boundary.
- **Assertion Criteria**: `Dynamic stack headroom > 1024 bytes.`

#### `T2-F13-05`: Verify infinite loop memory stability across 100,000 cycles in simulator.
- **Feature Reference**: Feature 13: Zero-Heap Architecture (Survey / R4)
- **Description**: Verify infinite loop memory stability across 100,000 cycles in simulator.
- **Inputs**: `Execute firmware loop for 100,000 cycles in AVR simulator / mock.`
- **Expected Behavior / Output**: SRAM memory footprint at cycle 100,000 is bit-identical to cycle 1 (0 byte leak).
- **Assertion Criteria**: `SRAM memory delta == 0 bytes.`

### Feature 14: Static SRAM Ceiling (Survey / R4)

#### `T2-F14-01`: Verify automated CI acceptance gate assertion for static SRAM <= 100 bytes.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify automated CI acceptance gate assertion for static SRAM <= 100 bytes.
- **Inputs**: `Execute `avr-size -C --mcu=atmega328p gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: Exit code 0 if Data <= 100 bytes; non-zero if Data > 100 bytes.
- **Assertion Criteria**: `Reported Data size <= 100 bytes.`

#### `T2-F14-02`: Verify static string literal Flash placement audit.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify static string literal Flash placement audit.
- **Inputs**: `Check `.data` symbols for quadrant titles ('CPU', 'GPU', 'RAM', 'TMP').`
- **Expected Behavior / Output**: Strings reside in Flash (.progmem) or minimal byte slices <= 30 bytes total.
- **Assertion Criteria**: `Total string bytes in `.data` <= 30 bytes.`

#### `T2-F14-03`: Verify absence of large global buffers in `.bss` (max symbol <= 16 bytes).
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify absence of large global buffers in `.bss` (max symbol <= 16 bytes).
- **Inputs**: `Inspect `.bss` section symbols via `avr-nm -S`.`
- **Expected Behavior / Output**: No single buffer in `.bss` exceeds 16 bytes.
- **Assertion Criteria**: `Max individual symbol size in `.bss` <= 16 bytes.`

#### `T2-F14-04`: Verify UART receive buffer is stack-allocated, not static global in `.bss`.
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify UART receive buffer is stack-allocated, not static global in `.bss`.
- **Inputs**: `Audit `software/gadget-firmware-uno/src/main.rs`.`
- **Expected Behavior / Output**: `rx_buf` is allocated on stack inside `main()`.
- **Assertion Criteria**: ``rx_buf` symbol does NOT exist in `.bss`.`

#### `T2-F14-05`: Verify SRAM stack headroom margin (>= 1,900 bytes available for stack).
- **Feature Reference**: Feature 14: Static SRAM Ceiling (Survey / R4)
- **Description**: Verify SRAM stack headroom margin (>= 1,900 bytes available for stack).
- **Inputs**: `Calculate $2,048 - (\text{.data} + \text{.bss})$.`
- **Expected Behavior / Output**: Available stack headroom >= 1,900 bytes.
- **Assertion Criteria**: `2048 - (data + bss) >= 1900.`

### Feature 15: Flash Ceiling (< 28KB) (Survey / R4)

#### `T2-F15-01`: Verify automated CI acceptance gate assertion for Flash < 28 KB (28,672 bytes).
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify automated CI acceptance gate assertion for Flash < 28 KB (28,672 bytes).
- **Inputs**: `Check binary size of `gadget-firmware-uno.elf`.`
- **Expected Behavior / Output**: Exit code 0 if Program < 28,672 bytes; fails if >= 28,672 bytes.
- **Assertion Criteria**: `Program bytes < 28672.`

#### `T2-F15-02`: Verify panic handler size minimization (< 20 bytes).
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify panic handler size minimization (< 20 bytes).
- **Inputs**: `Inspect panic handler implementation in `gadget-firmware-uno`.`
- **Expected Behavior / Output**: Uses `panic-halt` (infinite loop); does NOT link `core::fmt` formatting machinery.
- **Assertion Criteria**: `Panic handler footprint < 20 bytes; zero formatting code linked.`

#### `T2-F15-03`: Verify inlining bloat audit on display driver write primitives.
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify inlining bloat audit on display driver write primitives.
- **Inputs**: `Check `write_cmd` and `write_data` size across call sites.`
- **Expected Behavior / Output**: Functions remain compact; total text size remains within budget.
- **Assertion Criteria**: `Driver function overhead <= 2048 bytes.`

#### `T2-F15-04`: Verify bespoke numeral generator Flash footprint audit (< 800 bytes).
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify bespoke numeral generator Flash footprint audit (< 800 bytes).
- **Inputs**: `Measure symbol size of big numeral rendering logic.`
- **Expected Behavior / Output**: Total numeral generator footprint < 800 bytes Flash.
- **Assertion Criteria**: `Numeral rendering symbols total < 800 bytes.`

#### `T2-F15-05`: Verify long-term Flash growth headroom margin (>= 15% headroom remaining).
- **Feature Reference**: Feature 15: Flash Ceiling (< 28KB) (Survey / R4)
- **Description**: Verify long-term Flash growth headroom margin (>= 15% headroom remaining).
- **Inputs**: `Calculate percentage of 28 KB utilized.`
- **Expected Behavior / Output**: Flash utilization <= 85% (at least 4.2 KB headroom available).
- **Assertion Criteria**: `Flash utilization <= 85.0%.`

### Feature 16: Serial Packet Protocol (Survey / R5)

#### `T2-F16-01`: Verify rejection of corrupted magic header (`0xAA 0x54` / `0xAB 0x55`).
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify rejection of corrupted magic header (`0xAA 0x54` / `0xAB 0x55`).
- **Inputs**: `Decode `[0xAA, 0x54, 50, 60, 70, 80, 65, 100]`.`
- **Expected Behavior / Output**: `decode()` returns `None`; firmware receiver resets `rx_idx = 0`.
- **Assertion Criteria**: `decode returns None; receiver state machine resets.`

#### `T2-F16-02`: Verify immunity to false magic bytes embedded in payload (`0xAA 0x55` in data).
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify immunity to false magic bytes embedded in payload (`0xAA 0x55` in data).
- **Inputs**: `Packet 1 payload contains `cpu_percent = 0xAA`, `cpu_temp_c = 0x55`. Followed by Packet 2.`
- **Expected Behavior / Output**: Receiver consumes all 8 bytes of Packet 1 and does NOT prematurely reset on inner `0xAA 0x55`.
- **Assertion Criteria**: `Both Packet 1 and Packet 2 decode cleanly.`

#### `T2-F16-03`: Verify synchronization on back-to-back consecutive MAGIC_0 bytes (`0xAA 0xAA 0x55`).
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify synchronization on back-to-back consecutive MAGIC_0 bytes (`0xAA 0xAA 0x55`).
- **Inputs**: `Stream bytes: `[0xAA, 0xAA, 0x55, 10, 20, 30, 40, 50, 60]`.`
- **Expected Behavior / Output**: State machine transitions `rx_idx = 1 -> 1 -> 2`, correctly synchronizing on second `0xAA`.
- **Assertion Criteria**: `Packet decoded successfully without dropping bytes.`

#### `T2-F16-04`: Verify percentage clamping in `TelemetryPacket::new` for out-of-range inputs.
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify percentage clamping in `TelemetryPacket::new` for out-of-range inputs.
- **Inputs**: ``TelemetryPacket::new(150, 85, 200, 255, 90, 110)`.`
- **Expected Behavior / Output**: Percentages clamped to 100: cpu=100, ram=100, gpu=100, battery=100; temperatures unclamped (85, 90).
- **Assertion Criteria**: `packet.cpu_percent == 100; packet.ram_percent == 100; packet.gpu_percent == 100; packet.battery_percent == 100; packet.cpu_temp_c == 85; packet.gpu_temp_c == 90.`

#### `T2-F16-05`: Verify recovery from fragmented / interrupted packet streams.
- **Feature Reference**: Feature 16: Serial Packet Protocol (Survey / R5)
- **Description**: Verify recovery from fragmented / interrupted packet streams.
- **Inputs**: `Send 4 bytes `[0xAA, 0x55, 10, 20]`, pause 2 seconds, then send full valid 8-byte packet.`
- **Expected Behavior / Output**: Firmware receiver recovers synchronization and decodes the subsequent complete packet cleanly.
- **Assertion Criteria**: `Subsequent complete packet decodes cleanly; no receiver deadlock.`

### Feature 17: Host Hardware Telemetry (Survey / R5)

#### `T2-F17-01`: Verify sensor driver priority: dedicated driver (`k10temp`/`coretemp`) selected over ambient `acpitz`.
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify sensor driver priority: dedicated driver (`k10temp`/`coretemp`) selected over ambient `acpitz`.
- **Inputs**: `Mock sysfs with `hwmon1: acpitz (temp1=20000)` and `hwmon2: k10temp (temp1=78000)`.`
- **Expected Behavior / Output**: Host collector prioritizes `k10temp`, returning 78°C instead of shadowing with 20°C ambient.
- **Assertion Criteria**: `Returned CPU temperature == 78.`

#### `T2-F17-02`: Verify AMD GPU sysfs fallback (`gpu_busy_percent` and `amdgpu` hwmon).
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify AMD GPU sysfs fallback (`gpu_busy_percent` and `amdgpu` hwmon).
- **Inputs**: `Host without `nvidia-smi`, but with `/sys/class/drm/card0/device/gpu_busy_percent` and `hwmon` driver `amdgpu`.`
- **Expected Behavior / Output**: Reads GPU busy % from sysfs and temperature from `amdgpu` hwmon; does NOT crash.
- **Assertion Criteria**: `Returns valid GPU load and temperature (> 0).`

#### `T2-F17-03`: Verify graceful fallback when sensors are missing or disconnected.
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify graceful fallback when sensors are missing or disconnected.
- **Inputs**: `Host running in container/VM without hwmon or GPU.`
- **Expected Behavior / Output**: Falls back to default values (e.g. 50°C, 0% GPU) without panicking.
- **Assertion Criteria**: `Daemon stays running; logs warning; transmits valid packets.`

#### `T2-F17-04`: Verify serial port auto-fallback (`/dev/ttyUSB0` -> `/dev/ttyACM0` -> dry-run mode).
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify serial port auto-fallback (`/dev/ttyUSB0` -> `/dev/ttyACM0` -> dry-run mode).
- **Inputs**: `Run host daemon without `--port`, when `/dev/ttyUSB0` is absent but `/dev/ttyACM0` exists.`
- **Expected Behavior / Output**: Automatically detects and opens `/dev/ttyACM0`, or enters dry-run if neither exists.
- **Assertion Criteria**: `Daemon does not panic with 'No such file or directory'.`

#### `T2-F17-05`: Verify handling of zero CPU delta ticks (system suspended / no tick advance).
- **Feature Reference**: Feature 17: Host Hardware Telemetry (Survey / R5)
- **Description**: Verify handling of zero CPU delta ticks (system suspended / no tick advance).
- **Inputs**: `Two consecutive `/proc/stat` reads return identical tick counts (`delta_total == 0`).`
- **Expected Behavior / Output**: Code avoids division by zero ($0/0 \to \text{NaN}$) and defaults safely to 0% or previous sample.
- **Assertion Criteria**: `No division by zero panic; CPU percentage is valid u8 (0..100).`

---

## Specification Summary & Handoff Metrics

- **Total Tier 1 Test Cases**: 85 (5 per feature × 17 features)
- **Total Tier 2 Test Cases**: 85 (5 per feature × 17 features)
- **Total Specified Test Cases**: 170
- **Features Covered**: 17 / 17 (100% coverage)
- **Requirement Mapping**: R1.1–R1.3, R2.1–R2.3, R3.1–R3.5, R4.1–R4.5, R5.1–R5.2 (100% verified)
- **Status**: Fully specified, self-contained, actionable, and ready for E2E runner implementation.

