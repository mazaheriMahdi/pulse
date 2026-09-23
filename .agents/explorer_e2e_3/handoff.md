# E2E Test Suite Specification: Tier 3 (Cross-Feature Interactions) & Tier 4 (Real-World Scenarios)

**Author**: Explorer E2E 3 (`explorer_e2e_3`)  
**Workspace**: `/home/mahdi/Programming/perfomance-monitor`  
**Timestamp**: 2026-09-22T18:45:00Z  
**Parent**: Sub-Orchestrator E2E (`sub_orch_e2e` / `84adcafc-f5e3-46f8-89ac-821d86c446c2`)  
**Target Specifications**: `ORIGINAL_REQUEST.md` (R1–R5), `PROJECT.md` (Features 1–17), `sub_orch_e2e/SCOPE.md` (Tiers 3 & 4)

---

## 1. Observation

Direct observations from authoritative project requirements and codebase architecture:

1. **Authoritative Mandates (`ORIGINAL_REQUEST.md` & `PROJECT.md`)**:
   - **R1 (4-Quadrant Layout)**: 480x320 landscape partitioned into 4 symmetric cards (approx 230x145px each):
     - Q1 (Top-Left): CPU Load (`%`)
     - Q2 (Top-Right): GPU Load (`%`)
     - Q3 (Bottom-Left): RAM Usage (`%`)
     - Q4 (Bottom-Right): Thermals (CPU Temp & GPU Temp in `°C` with peak highlight)
   - **R2 (Arm's-Length Typography)**: Bold, prominent numerals $\ge 28–36\text{ px}$ tall (Scale 4–5 font or bespoke 7-segment / chunky glyphs). Zero tiny sub-14px text on primary readings.
   - **R3 (Dynamic Color Coding & Chunky Visual Meters)**: Bold 20–24px high progress track. Distinct dynamic palettes:
     - CPU: Electric Cyan (`#00D2D3`) $\to$ Alert Coral (`#FF6B6B`)
     - GPU: Neon Green (`#10AC84` / `#05C46B`) $\to$ Warning Orange (`#FF9F43`) $\to$ Blaze Red (`#FF3838`)
     - RAM: Vivid Violet (`#A55EEA`) $\to$ Danger Red (`#EA2027`)
     - Thermals: Cool Mint (`<60°C`) $\to$ Gold (`60–75°C`) $\to$ Crimson (`>75°C`)
   - **R4 (AVR ATmega328P Zero-Heap & Zero-Flicker Redraw)**:
     - Differential redraw engine updating only dirty bounding boxes over 8MHz SPI. Zero full-screen clears during telemetry loop.
     - Binary constraints: Flash binary size $< 28\text{ KB}$ ($28,672\text{ bytes}$) and static SRAM $< 100\text{ bytes}$ (`.data` + `.bss`).
     - `#![no_std]` strictly zero dynamic heap allocations.
   - **R5 (Hardware Agnosticism & Host Telemetry Alignment)**:
     - `embedded-hal` SPI/Pin trait boundaries preserved for ESP32 portability.
     - 8-byte framed serial packet (`0xAA 0x55` + 6 telemetry bytes).
     - Linux host telemetry collector querying procfs, sysfs, and `nvidia-smi`.

2. **Feature Inventory (17 Features)**:
   - F01: 4-Quadrant Card Grid (230x145px cards, 2px borders)
   - F02: Card Header Bar (14px tall header with accent label)
   - F03: Big Block Numerals ($\ge 28–36\text{ px}$ tall)
   - F04: Arm's-Length Legibility ($\ge 20$ arcminutes at 60–90cm)
   - F05: Chunky Visual Meters (20–24px high progress track, 200px inner fill)
   - F06: Dynamic CPU Palette (Electric Cyan $\to$ Alert Coral)
   - F07: Dynamic GPU Palette (Neon Green $\to$ Warning Orange $\to$ Blaze Red)
   - F08: Dynamic RAM Palette (Vivid Violet $\to$ Danger Red)
   - F09: Dynamic Thermal Palette (Cool Mint $\to$ Gold $\to$ Crimson)
   - F10: Dual Temp & Peak Highlight (CPU/GPU temps + high-contrast `[PEAK]` badge)
   - F11: Differential Redraw Engine (Dirty bounding-box SPI window updates)
   - F12: Zero-Flicker Execution (Eliminate full-screen clears during update)
   - F13: Zero-Heap Architecture (`#![no_std]` zero allocation)
   - F14: Static SRAM Ceiling ($< 100\text{ bytes}$ static RAM on ATmega328P)
   - F15: Flash Ceiling ($< 28\text{ KB}$ compiled AVR binary size)
   - F16: Serial Packet Protocol (8-byte binary frame: `[0xAA, 0x55, cpu, cpu_t, ram, gpu, gpu_t, bat]`)
   - F17: Host Hardware Telemetry (Linux `/proc/stat`, `/proc/meminfo`, `/sys/class/hwmon`, `nvidia-smi`)

3. **Geometry & Timing Constants**:
   - Screen Dimensions: $480 \times 320\text{ px}$
   - Horizontal Partition: Left margin $7\text{ px}$, Card 1 width $230\text{ px}$, Center gap $6\text{ px}$, Card 2 width $230\text{ px}$, Right margin $7\text{ px}$. Total = $480\text{ px}$.
   - Vertical Partition: Top margin $10\text{ px}$, Card Row 1 height $145\text{ px}$, Center gap $10\text{ px}$, Card Row 2 height $145\text{ px}$, Bottom margin $10\text{ px}$. Total = $320\text{ px}$.
   - Card Origins $(X, Y)$: Q1: $(7, 10)$, Q2: $(243, 10)$, Q3: $(7, 165)$, Q4: $(243, 165)$.
   - Meter Track Dimensions: Outer $202 \times 24\text{ px}$, Inner fill $200 \times 22\text{ px}$. Ratio = $2\text{ px}$ per $1\%$.
   - Big Numeral Bounding Box: $X_{\text{local}} = 14 \dots 120$, $Y_{\text{local}} = 26 \dots 62$ ($106 \times 36\text{ px}$).
   - 8MHz SPI Byte Rate: $1.0\,\mu\text{s}$ per byte; full clear ($460.8\text{ KB}$) takes $\approx 691\text{ ms}$; dirty update ($< 12\text{ KB}$) takes $< 18\text{ ms}$.

---

## 2. Logic Chain

1. **Why Cross-Feature Interaction Testing (Tier 3) is Critical**:
   - Individual features may pass isolated unit tests but fail catastrophically when combined under embedded resource constraints.
   - *Example 1*: F01 (Grid boundaries) + F11 (Differential Redraw): If a numeral or progress bar bounding box is calculated using global coordinates without quadrant offset, or if dirty rect bounds are computed with off-by-one errors, redraw operations will overwrite adjacent card borders (6px center gap) or bleed into neighboring quadrants.
   - *Example 2*: F03 (Big Numerals) + F08 (RAM Palette) + F14 (Static SRAM Ceiling): Generating dynamic colored 28–36px numerals must not allocate glyph lookup tables or string buffers in SRAM. The numeral generator must either stream procedurally from PROGMEM or calculate 7-segment vectors on the stack without exceeding the 100-byte static SRAM ceiling.
   - *Example 3*: F09 (Thermal Palette) + F10 (Dual Temp & Peak) + F12 (Zero-Flicker): When the peak temperature switches dynamically between CPU and GPU, the `[PEAK]` badge must transfer cleanly without full-card clears that cause noticeable 100ms+ optical flashes.
   - *Example 4*: F16 (Serial Protocol) + F17 (Host Telemetry) + F11 (Differential Redraw): When the host streams back-to-back identical packets (0 delta), the differential redraw engine must detect zero change and emit exactly 0 SPI bytes, maintaining 0% bus load.

2. **Why Real-World Scenario Testing (Tier 4) is Critical**:
   - Synthetic benchmarks test discrete static states. Desktop monitoring gadgets operate in continuous, noisy, dynamic environments characterized by bursty CPU builds, sustained GPU gaming heat, out-of-memory kernel spikes, USB disconnects, and 24/7 continuous operation.
   - Testing multi-step temporal workflows validates state machine transitions, edge condition recovery, accumulator drift, memory leak absence, and optical ergonomics under authentic user conditions.

---

## 3. Caveats

1. **Test Environment Headless Execution**:
   - E2E tests run on Linux host runners without requiring physical ATmega328P or ILI9488 hardware.
   - The test harnesses intercept display SPI commands via a virtual framebuffer (`MockDisplayBuffer` / `MockSpiDevice`), capturing exact window parameters (`CASET 0x2A`, `PASET 0x2B`, `RAMWR 0x2C`), pixel colors, full clear counters, and total SPI bytes transferred.
2. **Timing Assertions**:
   - SPI transmission times ($< 35\text{ ms}$) and serial transmission times ($1.39\text{ ms}$) are derived from mathematical byte count calculations on 8MHz SPI and 57600 baud UART. Host-side execution timers verify relative algorithm speed.
3. **Auxiliary Battery Metric**:
   - `battery_percent` is carried at Byte 7 of `TelemetryPacket`. In accordance with `ORIGINAL_REQUEST.md` R1, primary real estate is dedicated to the 4 big blocks. Tests verify that Byte 7 is safely parsed without disturbing the 4 quadrants.

---

## 4. Conclusion: Exhaustive Tier 3 & Tier 4 Specifications

---

### Part A: Tier 3 — Cross-Feature Interactions (18 Test Cases)

```
========================================================================================================================
TIER 3 CROSS-FEATURE INTERACTION MATRIX
========================================================================================================================
Test ID     Feature Combination               Primary Interaction Under Test
------------------------------------------------------------------------------------------------------------------------
T3-INT-01   F01 (Grid) + F11 (Diff Redraw)    Card bounding clipping; zero bleed into 6px/10px gutters or adjacent cards
T3-INT-02   F03 (Big Num) + F08 + F14 (SRAM)  3-digit 100% RAM numeral rendering in Flash/Stack with SRAM < 100 bytes
T3-INT-03   F09 (Thermals) + F10 + F12 (Zero) Dynamic CPU/GPU PEAK swapping with zero card-level clears or optical strobe
T3-INT-04   F16 (Serial) + F17 + F11 (Redraw) 0-delta packet streaming results in exactly 0 dirty rects and 0 SPI bytes
T3-INT-05   F01 (Grid) + F05 + F06 (CPU Pal)  Chunky meter expansion across Cyan -> Amber -> Coral within Q1 card bounds
T3-INT-06   F02 (Header) + F03 + F04 (Legib)  Vertical clearance harmony: 14px header, 36px numeral, 24px chunky meter
T3-INT-07   F07 (GPU Pal) + F05 + F11 (Redraw)Rapid load swing contraction/expansion; clearing abandoned track without ghosts
T3-INT-08   F01 (Grid) + F09 + F10 (Peak)     Thermals >75°C triggers dynamic Crimson card border on Q4 without affecting Q1-Q3
T3-INT-09   F13 (Zero-Heap) + F14 + F16 (Wire)USART RX sliding window state machine processes packets with 0B heap, <100B SRAM
T3-INT-10   F03 (Big Num) + F11 + F12 (Zero)  Digit width transition (9% -> 100% -> 0%); clean erasure of 3rd column ghost digits
T3-INT-11   F16 (Serial) + F17 + Range Clamp  Host telemetry clamping (105% CPU, 120°C temp); firmware graceful handling
T3-INT-12   F05 (Meter) + F08 (RAM) + F11     Subtle 1% creeping delta vs threshold-crossing full-bar recolor (Violet -> Red)
T3-INT-13   F01 + F02 + F11 + F12 (Simult)    Full-system multi-quadrant load spike: all 4 cards update in <45ms without flicker
T3-INT-14   F03 (Big Num) + F14 + F15 (Flash) Firmware build verification: complete numeral engine with Flash < 28KB, SRAM < 100B
T3-INT-15   F11 (Redraw) + F16 (Packet Noise) Mid-stream line noise and bad magic recovery without UI distortion or spurious redraws
T3-INT-16   F06 + F07 + F08 + F09 (Palettes)  4-Quadrant simultaneous palette distinctness and visual hierarchy under stress
T3-INT-17   F10 (Peak) + F17 (Host Collectors)Dual GPU/CPU sensor discovery (k10temp priority, nvidia-smi vs amdgpu hwmon)
T3-INT-18   F05 (Chunky) + F13 + F15 (Math)   Zero-float integer gauge math (fill_w = val * 2) preventing soft-float bloat
========================================================================================================================
```

---

#### Detailed Specifications: T3-INT-01 through T3-INT-18

##### `T3-INT-01`: F01 (4-Quadrant Grid) + F11 (Differential Redraw Engine)
- **Features Under Test**: F01 (4-Quadrant Card Grid), F11 (Differential Redraw Engine).
- **Scenario**: Validate that differential dirty bounding boxes for all 4 quadrants are strictly clamped to their respective card interiors ($230 \times 145\text{ px}$) and never overwrite the $2\text{ px}$ card borders, the $6\text{ px}$ center vertical gap ($X = 237 \dots 242$), the $10\text{ px}$ horizontal gap ($Y = 155 \dots 164$), or the outer screen margins.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Baseline Layout)*: Call `Dashboard::draw_layout(&mut display)`. Verify 4 cards drawn at $(7, 10)$, $(243, 10)$, $(7, 165)$, and $(243, 165)$ with $2\text{ px}$ solid border in `Color::BORDER` (`#323E5A`).
  2. *Step 2 (Max Dimension Trigger)*: Feed `TelemetryPacket` with `cpu_percent = 100`, `gpu_percent = 100`, `ram_percent = 100`, `cpu_temp_c = 100`.
  3. *Step 3 (Dirty Window Audit)*: Intercept all `set_window(x0, y0, x1, y1)` SPI calls.
- **Concrete Assertions**:
  - For all Q1 window calls: $7 \le x0 \le x1 \le 236$ and $10 \le y0 \le y1 \le 154$.
  - For all Q2 window calls: $243 \le x0 \le x1 \le 472$ and $10 \le y0 \le y1 \le 154$.
  - For all Q3 window calls: $7 \le x0 \le x1 \le 236$ and $165 \le y0 \le y1 \le 309$.
  - For all Q4 window calls: $243 \le x0 \le x1 \le 472$ and $165 \le y0 \le y1 \le 309$.
  - Pixels in center gap ($X \in [237, 242]$, $Y \in [0, 319]$) retain background `#121622` with $0$ writes.
  - Card border pixels (e.g. $X = 7, Y \in [10, 154]$) retain border `#323E5A` with $0$ overwrites.

##### `T3-INT-02`: F03 (Big Block Numerals) + F08 (Dynamic RAM Palette) + F14 (Static SRAM Ceiling)
- **Features Under Test**: F03 (Big Block Numerals), F08 (Dynamic RAM Palette), F14 (Static SRAM Ceiling).
- **Scenario**: Render maximum 3-digit RAM load (`100%`) with dynamic danger coloring (Danger Red `#EA2027`) while verifying zero RAM font table consumption and total static SRAM $< 100\text{ bytes}$.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Static Analysis)*: Inspect compiled firmware ELF using `avr-size -C` and `avr-nm -S`.
  2. *Step 2 (State Transition)*: Send `TelemetryPacket { ram_percent: 100, .. }` to `Dashboard::update`.
  3. *Step 3 (Render Inspection)*: Intercept glyph rendering pipeline.
- **Concrete Assertions**:
  - `avr-size`: Data (`.data` + `.bss`) $\le 100\text{ bytes}$ (expected $\le 55\text{ bytes}$).
  - `avr-nm`: Symbol `FONT_5X7` does NOT exist in `.data`.
  - Rendered numeral glyph height $\ge 28\text{ px}$ (Scale 4 = $28\text{ px}$, bespoke = $36\text{ px}$).
  - Numeral pixel color matches `Color::new(234, 32, 39)` (Danger Red `#EA2027`).
  - Stack allocation during `update` $\le 64\text{ bytes}$.

##### `T3-INT-03`: F09 (Dynamic Thermal Palette) + F10 (Dual Temp & Peak Highlight) + F12 (Zero-Flicker)
- **Features Under Test**: F09 (Dynamic Thermal Palette), F10 (Dual Temp & Peak Highlight), F12 (Zero-Flicker Execution).
- **Scenario**: Swap the thermal peak role between CPU and GPU across consecutive frames while verifying targeted differential updates with zero full-card or full-screen clears.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (CPU is Peak)*: Feed `packet_1 = [0xAA, 0x55, 50, 78, 50, 50, 62, 100]`. (CPU 78°C [PEAK], GPU 62°C).
  2. *Step 2 (Verify CPU Peak)*: Assert CPU readout renders in Crimson (`#FF3838`) with `[PEAK]` badge at CPU coordinates ($X_{\text{local}} = 78, Y_{\text{local}} = 30$). GPU renders in Gold (`#FECA57`).
  3. *Step 3 (GPU Becomes Peak)*: Feed `packet_2 = [0xAA, 0x55, 50, 65, 50, 50, 82, 100]`. (CPU 65°C, GPU 82°C [PEAK]).
  4. *Step 4 (Verify GPU Peak & Diff Clear)*: Assert `[PEAK]` badge erased from CPU region and rendered at GPU coordinates ($X_{\text{local}} = 188, Y_{\text{local}} = 30$). GPU readout in Crimson (`#FF3838`), CPU in Gold (`#FECA57`).
- **Concrete Assertions**:
  - `display.clear_count == 0` across all steps.
  - Number of dirty window updates $\le 3$ (CPU numeral box, GPU numeral box, peak badge box).
  - Total SPI bytes transferred during swap $\le 14,500\text{ bytes}$ ($\approx 18\text{ ms}$ at 8MHz SPI).

##### `T3-INT-04`: F16 (Serial Packet Protocol) + F17 (Host Telemetry) + F11 (Differential Redraw)
- **Features Under Test**: F16 (Serial Packet Protocol), F17 (Host Hardware Telemetry), F11 (Differential Redraw Engine).
- **Scenario**: Host daemon continuously samples Linux sysfs and streams valid 8-byte frames. When system state is static (0 delta), the differential redraw engine must transmit zero SPI transactions.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (First Sample)*: Host produces `packet_1 = [0xAA, 0x55, 35, 52, 60, 20, 48, 95]`. Firmware decodes and renders.
  2. *Step 2 (Identical Sample)*: Host samples identical load: `packet_2 = [0xAA, 0x55, 35, 52, 60, 20, 48, 95]`. Encoded and transmitted.
  3. *Step 3 (Firmware Reception)*: Firmware receives 8 bytes, decodes `TelemetryPacket`, invokes `dashboard.update(&mut display, packet_2)`.
- **Concrete Assertions**:
  - Host serialization output: `len == 8`, `buf[0] == 0xAA`, `buf[1] == 0x55`.
  - Firmware `decode(&rx_buf)` returns `Some(packet_2)`.
  - In Step 3, SPI calls to `set_window` == 0 and SPI bytes transmitted == 0.
  - Display controller CS pin remains inactive (high).

##### `T3-INT-05`: F01 (4-Quadrant Grid) + F05 (Chunky Visual Meters) + F06 (Dynamic CPU Palette)
- **Features Under Test**: F01 (4-Quadrant Card Grid), F05 (Chunky Visual Meters), F06 (Dynamic CPU Palette).
- **Scenario**: CPU meter fills horizontally across three color thresholds within Q1, verifying exact geometric fill scaling ($1\% = 2\text{ px}$) and color palette transitions.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Nominal Load)*: `cpu_percent = 40`.
  2. *Step 2 (Warning Amber)*: `cpu_percent = 70`.
  3. *Step 3 (Alert Coral)*: `cpu_percent = 92`.
- **Concrete Assertions**:
  - *Step 1*: Gauge fill width = $40 \times 2 = 80\text{ px}$. Track fill rect: $X = 22 \dots 101$, $Y = 81 \dots 102$ ($80 \times 22\text{ px}$). Fill color = `Color::new(0, 210, 211)` (Electric Cyan `#00D2D3`).
  - *Step 2*: Gauge fill width = $70 \times 2 = 140\text{ px}$. Track fill rect: $X = 22 \dots 161$. Fill color = `Color::new(255, 165, 2)` (Coral Amber `#FFA502`).
  - *Step 3*: Gauge fill width = $92 \times 2 = 184\text{ px}$. Track fill rect: $X = 22 \dots 205$. Fill color = `Color::new(255, 107, 107)` (Alert Coral `#FF6B6B`).
  - Outer meter track bounds: $X \in [21, 222]$, $Y \in [80, 103]$ strictly inside Q1 ($X \in [7, 236]$, $Y \in [10, 154]$).

##### `T3-INT-06`: F02 (Card Header Bar) + F03 (Big Block Numerals) + F04 (Arm's-Length Legibility)
- **Features Under Test**: F02 (Card Header Bar), F03 (Big Block Numerals), F04 (Arm's-Length Legibility).
- **Scenario**: Validate vertical ergonomic hierarchy and optical clearance within a $230 \times 145\text{ px}$ card: header label (14px), big numeral (36px), chunky meter (24px), secondary telemetry (14px).
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Render Full Card)*: Render Q1 with title `"CPU LOAD"`, reading `"88 %"`, meter at $88\%$, and secondary subtitle `"4.8 GHz"`.
  2. *Step 2 (Spatial Intersect Audit)*: Calculate bounding boxes of all 4 visual components and verify zero vertical or horizontal overlap.
- **Concrete Assertions**:
  - Header label: $Y_{\text{local}} \in [8, 22]$ (Height = $14\text{ px}$).
  - Big numeral: $Y_{\text{local}} \in [26, 62]$ (Height = $36\text{ px}$). Vertical gap below header = $4\text{ px}$.
  - Chunky meter: $Y_{\text{local}} \in [70, 93]$ (Height = $24\text{ px}$). Vertical gap below numeral = $8\text{ px}$.
  - Secondary subtitle: $Y_{\text{local}} \in [104, 118]$ (Height = $14\text{ px}$). Vertical gap below meter = $11\text{ px}$.
  - Card bottom margin: $145 - 118 = 27\text{ px}$ cushion.
  - Optical subtended angle of numeral at 70cm: $\ge 21.0\text{ arcminutes}$ (meets ISO 9241-303).

##### `T3-INT-07`: F07 (Dynamic GPU Palette) + F05 (Chunky Visual Meters) + F11 (Differential Redraw)
- **Features Under Test**: F07 (Dynamic GPU Palette), F05 (Chunky Visual Meters), F11 (Differential Redraw Engine).
- **Scenario**: Rapid contraction of GPU meter from 95% down to 25%. Ensure that abandoned track pixels ($X = 72 \dots 211$) are cleanly overwritten with `Color::PANEL_BG` (`#1C2234`) without visual tearing or ghost remnants.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Peak GPU Load)*: Feed `gpu_percent = 95`. Meter fill width = $190\text{ px}$ ($X_{\text{local}} = 15 \dots 204$) in Blaze Red (`#FF3838`).
  2. *Step 2 (Rapid Drop)*: Feed `gpu_percent = 25`. Meter fill width = $50\text{ px}$ ($X_{\text{local}} = 15 \dots 64$) in Neon Green (`#10AC84`).
  3. *Step 3 (Bounding Box Audit)*: Intercept differential redraw actions.
- **Concrete Assertions**:
  - Active fill rect updated: $X_{\text{local}} = 15 \dots 64$, color = `#10AC84`.
  - Abandoned track delta rect: $X_{\text{local}} = 65 \dots 204$ ($140 \times 22\text{ px}$), filled with `Color::PANEL_BG` (`#1C2234`).
  - Zero Blaze Red (`#FF3838`) pixels remain in region $X_{\text{local}} \in [65, 204]$.
  - No SPI writes outside the meter track bounding box.

##### `T3-INT-08`: F01 (4-Quadrant Grid) + F09 (Dynamic Thermal Palette) + F10 (Dual Temp & Peak Highlight)
- **Features Under Test**: F01 (4-Quadrant Card Grid), F09 (Dynamic Thermal Palette), F10 (Dual Temp & Peak Highlight).
- **Scenario**: Extreme thermal event where CPU Temp hits 88°C and GPU Temp hits 74°C. Q4 card border dynamically turns Crimson (`#FF3838`), while Q1, Q2, and Q3 card borders remain undisturbed in default `Color::BORDER` (`#323E5A`).
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Normal Thermals)*: Feed `cpu_temp_c = 55`, `gpu_temp_c = 52`. Verify all 4 card borders are `#323E5A`.
  2. *Step 2 (Thermal Overheat Spike)*: Feed `cpu_temp_c = 88`, `gpu_temp_c = 74`.
  3. *Step 3 (Border & Badge Verification)*: Inspect border pixels for Q1, Q2, Q3, Q4.
- **Concrete Assertions**:
  - Q4 card border ($X \in [243, 472]$, $Y \in [165, 309]$ outer 2px boundary) turns `Color::new(255, 56, 56)` (Crimson `#FF3838`).
  - Q1, Q2, Q3 card borders retain `Color::new(50, 62, 90)` (`#323E5A`) with 0 modifications.
  - Q4 CPU temperature numeral (88°C) highlighted in Crimson with `[PEAK]` badge.
  - Q4 GPU temperature numeral (74°C) rendered in Gold (`#FECA57`).

##### `T3-INT-09`: F13 (Zero-Heap Architecture) + F14 (Static SRAM Ceiling) + F16 (Serial Packet Protocol)
- **Features Under Test**: F13 (Zero-Heap Architecture), F14 (Static SRAM Ceiling), F16 (Serial Packet Protocol).
- **Scenario**: Non-blocking USART RX sliding window state machine receives a continuous stream of 8-byte frames on ATmega328P. Validate zero dynamic heap allocations and static SRAM $< 100\text{ bytes}$.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Static Symbol Inspection)*: Run `avr-nm -n target/avr-none/release/gadget-firmware-uno.elf`.
  2. *Step 2 (Heap Symbol Audit)*: Search symbol table for `malloc`, `realloc`, `free`, `__rust_alloc`, `alloc_error_handler`.
  3. *Step 3 (Serial Stream Ingestion)*: Feed 10,000 serial bytes into the firmware receiver.
- **Concrete Assertions**:
  - `malloc`, `free`, and all dynamic allocation symbols are completely ABSENT from binary.
  - Static memory sections: `.data + .bss < 100 bytes`.
  - Stack frame for USART RX buffer: exactly $8\text{ bytes}$ stack array (`[0u8; 8]`) and $1\text{ byte}$ index counter (`rx_idx: usize`).
  - Memory consumption is strictly constant across 10,000 bytes.

##### `T3-INT-10`: F03 (Big Block Numerals) + F11 (Differential Redraw Engine) + F12 (Zero-Flicker Execution)
- **Features Under Test**: F03 (Big Block Numerals), F11 (Differential Redraw Engine), F12 (Zero-Flicker Execution).
- **Scenario**: Rapid width transitions of numeric values (single-digit $\to$ 3-digit $\to$ single-digit: `8%` $\to$ `100%` $\to$ `0%`). Verify clean erasure of the 2nd and 3rd digit columns without leaving ghost digits or causing full-card redraw.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (1-digit reading)*: Feed `cpu_percent = 8`. Numeral occupies 1 digit column + `%`.
  2. *Step 2 (3-digit reading)*: Feed `cpu_percent = 100`. Numeral expands to 3 digit columns (`1`, `0`, `0`) + `%`.
  3. *Step 3 (1-digit reading)*: Feed `cpu_percent = 0`. Numeral contracts to 1 digit column (`0`) + `%`.
- **Concrete Assertions**:
  - In Step 3, the previous digit positions for tens and hundreds columns ($X_{\text{local}} = 38 \dots 84$, $Y_{\text{local}} = 26 \dots 61$) are filled with `Color::PANEL_BG` (`#1C2234`).
  - No leftover pixel fragments of `'1'` or `'0'` exist in the cleared columns.
  - Redraw bounding box is exactly $106 \times 36\text{ px}$.
  - `display.clear_count == 0`.

##### `T3-INT-11`: F16 (Serial Packet Protocol) + F17 (Host Hardware Telemetry) + Out-of-Range Clamping
- **Features Under Test**: F16 (Serial Packet Protocol), F17 (Host Hardware Telemetry), Protocol Range Clamping.
- **Scenario**: Host daemon encounters aberrant sysfs readings (e.g. CPU load reported as 108% due to multi-thread sampling race, or thermals reported as 135°C). Host clamping logic guarantees valid wire packets, and firmware decodes safely.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Host Ingestion)*: Mock `/proc/stat` delta resulting in calculated CPU = 108.4%.
  2. *Step 2 (Host Packet Creation)*: Call `TelemetryPacket::new(108, 135, 150, 102, 90, 105)`.
  3. *Step 3 (Wire Encoding & Decode)*: Encode into `[u8; 8]` wire frame and decode in firmware.
- **Concrete Assertions**:
  - `packet.cpu_percent == 100` (clamped).
  - `packet.ram_percent == 100` (clamped).
  - `packet.gpu_percent == 100` (clamped).
  - `packet.battery_percent == 100` (clamped).
  - `packet.cpu_temp_c == 135` (raw u8 passed; firmware formats as 3-digit number or clamps display to 99°C).
  - Firmware renders reading without buffer overflow or crash.

##### `T3-INT-12`: F05 (Chunky Visual Meters) + F08 (Dynamic RAM Palette) + F11 (Differential Redraw)
- **Features Under Test**: F05 (Chunky Visual Meters), F08 (Dynamic RAM Palette), F11 (Differential Redraw Engine).
- **Scenario**: Incremental creeping RAM consumption ($69\% \to 70\% \to 84\% \to 85\%$). Differentiate between a subtle 1% increment (2px delta update) and a palette-crossing threshold that triggers a full bar recolor.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Base Load)*: `ram_percent = 69` (Vivid Violet `#A55EEA`, fill width = $138\text{ px}$).
  2. *Step 2 (Cross Threshold 1)*: `ram_percent = 70` (Crosses to Magenta Rose `#D980FA`, fill width = $140\text{ px}$).
  3. *Step 3 (Subtle Increment)*: `ram_percent = 71` (Same palette `#D980FA`, fill width = $142\text{ px}$).
  4. *Step 4 (Cross Threshold 2)*: `ram_percent = 85` (Crosses to Danger Red `#EA2027`, fill width = $170\text{ px}$).
- **Concrete Assertions**:
  - *Step 2*: Full bar fill ($140 \times 22\text{ px}$) redrawn in new Magenta Rose palette (`#D980FA`). Dirty area = $3,080\text{ pixels}$.
  - *Step 3*: Only $2\text{ px}$ delta track ($2 \times 22\text{ px}$) appended at $X = 140 \dots 141$. Dirty area = $44\text{ pixels}$ ($132\text{ bytes}$ SPI).
  - *Step 4*: Full bar fill ($170 \times 22\text{ px}$) redrawn in Danger Red palette (`#EA2027`). Dirty area = $3,740\text{ pixels}$.

##### `T3-INT-13`: F01 (4-Quadrant Grid) + F02 (Card Header Bar) + Multi-Quadrant Simultaneous Update (F11 + F12)
- **Features Under Test**: F01 (Grid), F02 (Card Headers), F11 (Differential Redraw), F12 (Zero-Flicker).
- **Scenario**: Worst-case telemetry frame: all 4 metrics swing simultaneously (CPU 15% $\to$ 95%, GPU 10% $\to$ 88%, RAM 30% $\to$ 82%, CPU Temp 42°C $\to$ 84°C). Verify all 4 cards update differentially in sequence within $< 45\text{ ms}$ over 8MHz SPI without screen tearing.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Initial State)*: Apply low-load packet `packet_1 = [0xAA, 0x55, 15, 42, 30, 10, 40, 100]`.
  2. *Step 2 (Worst-Case Spike)*: Apply high-load packet `packet_2 = [0xAA, 0x55, 95, 84, 82, 88, 76, 100]`.
  3. *Step 3 (Performance Audit)*: Measure total dirty bounding box pixel count and SPI bytes emitted.
- **Concrete Assertions**:
  - Total pixels redrawn:
    - 4 numeral bounding boxes: $4 \times (106 \times 36) = 15,264\text{ pixels}$
    - 4 chunky meter updates: $\le 4 \times (200 \times 22) = 17,600\text{ pixels}$
    - Peak badge update: $48 \times 16 = 768\text{ pixels}$
    - Total dirty pixels $\le 33,632\text{ pixels}$.
  - Total SPI bytes $\le 33,632 \times 3 + \text{command overhead} \approx 102\text{ KB}$.
  - Transmission duration at 8MHz SPI ($1.0\,\mu\text{s}/\text{byte}$) $\approx 35–45\text{ ms}$ ($< 50\text{ ms}$ ceiling).
  - All 4 header bars and grid card borders remain pristine with zero redraw.
  - `display.clear_count == 0`.

##### `T3-INT-14`: F03 (Big Block Numerals) + F14 (Static SRAM Ceiling) + F15 (Flash Ceiling < 28KB)
- **Features Under Test**: F03 (Big Block Numerals), F14 (Static SRAM Ceiling), F15 (Flash Ceiling < 28KB).
- **Scenario**: Compile complete firmware (`cargo +nightly build --release`) with big numeral engine included. Verify compiled ELF binary complies with both $< 28\text{ KB}$ Flash and $< 100\text{ bytes}$ static SRAM.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Compile)*: Execute `cargo +nightly build --release` in `software/gadget-firmware-uno`.
  2. *Step 2 (Size Analysis)*: Execute `avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf`.
  3. *Step 3 (Symbol Section Audit)*: Execute `avr-size -A`.
- **Concrete Assertions**:
  - Exit code == 0.
  - Program (.text + .data + .bootloader) $< 28,672\text{ bytes}$ (typically $< 12,000\text{ bytes}$).
  - Data (.data + .bss) $< 100\text{ bytes}$ (typically $< 60\text{ bytes}$).
  - Firmware leaves $> 4\text{ KB}$ Flash headroom for bootloader and $> 1.9\text{ KB}$ dynamic stack headroom.

##### `T3-INT-15`: F11 (Differential Redraw Engine) + F16 (Serial Packet Protocol) on Packet Noise
- **Features Under Test**: F11 (Differential Redraw Engine), F16 (Serial Packet Protocol).
- **Scenario**: Serial UART stream is corrupted by line noise, framing errors, and false magic byte insertions. Verify that corrupted packets are discarded without triggering spurious display redraws, and that the display recovers immediately upon receiving the next valid packet.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Establish State)*: Feed valid frame `[0xAA, 0x55, 50, 60, 50, 50, 60, 100]`. Display renders.
  2. *Step 2 (Inject Noise Stream)*: Feed 32 bytes of random noise: `[0x00, 0xFF, 0xAA, 0x12, 0x55, 0x7E, 0xAA, 0x54, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, ...]`.
  3. *Step 3 (Verify Display Unchanged)*: Count SPI transactions during Step 2.
  4. *Step 4 (Valid Packet Resync)*: Feed valid frame `[0xAA, 0x55, 75, 65, 80, 45, 60, 100]`.
- **Concrete Assertions**:
  - In Step 2, `TelemetryPacket::decode` returns `None` for all corrupted combinations.
  - During Step 2, SPI `set_window` calls == 0 and SPI bytes transmitted == 0.
  - In Step 4, receiver state machine locks onto `0xAA 0x55`, decodes new packet, and updates display to `CPU 75%`, `RAM 80%`.

##### `T3-INT-16`: F06 (CPU) + F07 (GPU) + F08 (RAM) + F09 (Thermal) Palette Distinctness
- **Features Under Test**: F06, F07, F08, F09 (All 4 dynamic palettes).
- **Scenario**: Simultaneous comparison of all 4 quadrant colors across nominal, elevated, and maximum stress conditions. Verify high chromatic distinction to prevent user confusion between metrics.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Nominal State)*: CPU 30%, GPU 30%, RAM 30%, Temp 45°C.
  2. *Step 2 (Stress State)*: CPU 95%, GPU 95%, RAM 95%, Temp 85°C.
- **Concrete Assertions**:
  - *Nominal State*:
    - Q1: Electric Cyan (`#00D2D3` / Hue $\approx 180^\circ$)
    - Q2: Neon Green (`#10AC84` / Hue $\approx 164^\circ$, green dominant)
    - Q3: Vivid Violet (`#A55EEA` / Hue $\approx 274^\circ$, purple)
    - Q4: Cool Mint (`#1DD1A1` / Hue $\approx 160^\circ$, mint blue)
    - Euclidean RGB distance between any two palettes $\ge 65.0$.
  - *Stress State*:
    - Q1: Alert Coral (`#FF6B6B` / Coral red-pink)
    - Q2: Warning Orange (`#FF9F43` / Bright Amber orange)
    - Q3: Danger Red (`#EA2027` / Deep crimson-red)
    - Q4: Thermal Crimson (`#FF3838` / Pure bright red)
    - Distinct visual identification of each quadrant maintained via card position and header title.

##### `T3-INT-17`: F10 (Dual Temp & Peak Highlight) + F17 (Host Hardware Telemetry) Multi-GPU Fallbacks
- **Features Under Test**: F10 (Dual Temp & Peak Highlight), F17 (Host Hardware Telemetry).
- **Scenario**: Host daemon operating on dual-GPU or hybrid-graphics hardware (e.g. AMD iGPU + NVIDIA dGPU, or AMD discrete GPU). Host accurately prioritizes hardware sensors and passes both CPU and GPU temperatures into bytes 3 and 6.
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Sensor Enumeration)*: Mock `/sys/class/hwmon` containing `k10temp` (CPU), `amdgpu` (iGPU), and `nvidia-smi` available.
  2. *Step 2 (Host Sampler Execution)*: Run `read_cpu_temp()` and `read_gpu_metrics()`.
  3. *Step 3 (Frame Verification)*: Validate produced `TelemetryPacket`.
- **Concrete Assertions**:
  - `read_cpu_temp()` selects `k10temp/temp1_input` (e.g. 78°C) over ambient `acpitz` (e.g. 25°C).
  - `read_gpu_metrics()` extracts NVIDIA dGPU metrics via `nvidia-smi` (e.g. 65% load, 72°C) rather than defaulting to fallback 50°C.
  - Wire frame byte 3 == 78, byte 6 == 72.
  - Firmware renders Q4 with CPU 78°C tagged with `[PEAK]` in Gold.

##### `T3-INT-18`: F05 (Chunky Visual Meters) + F13 (Zero-Heap) + F15 (Flash Ceiling) Integer Gauge Math
- **Features Under Test**: F05 (Chunky Visual Meters), F13 (Zero-Heap), F15 (Flash Ceiling).
- **Scenario**: Gauge fill width calculation on 8-bit AVR without software floating-point emulation. Verify that $200\text{ px}$ inner track allows exact integer scaling (`fill_w = val * 2`), avoiding soft-float runtime bloat (`__addsf3`, `__mulsf3`).
- **Multi-Step Execution Sequence**:
  1. *Step 1 (Disassembly Inspection)*: Inspect compiled firmware assembly using `avr-objdump -d`.
  2. *Step 2 (Symbol Audit)*: Search for GCC soft-float library symbols (`__divsf3`, `__floatsisf`, `__mulsf3`).
  3. *Step 3 (Boundary Value Calculation)*: Evaluate `fill_width(val)` for $val \in [0, 1, 50, 99, 100]$.
- **Concrete Assertions**:
  - Zero software floating-point routines linked into AVR ELF binary.
  - Flash binary size remains $< 15\text{ KB}$ (well below $28\text{ KB}$).
  - Exact fill widths produced:
    - $0\% \to 0\text{ px}$
    - $1\% \to 2\text{ px}$
    - $50\% \to 100\text{ px}$
    - $99\% \to 198\text{ px}$
    - $100\% \to 200\text{ px}$
  - Calculation executes in $\le 4$ AVR CPU cycles (single 8-bit shift or add).

---

### Part B: Tier 4 — Real-World Application Scenarios (9 Scenarios)

```
========================================================================================================================
TIER 4 REAL-WORLD APPLICATION SCENARIOS
========================================================================================================================
Scenario ID   Workload Name                    Primary Stress Dynamics & Lifecycle Phases
------------------------------------------------------------------------------------------------------------------------
T4-APP-01     Desktop Cold Boot & Init         Power-on reset, SPI init, blank layout, host daemon launch, first live frame
T4-APP-02     Idle Desktop Fluctuations        Low ambient load (CPU 2-8%, GPU 0-2%, RAM 28%), nominal palettes, 0% tearing
T4-APP-03     Heavy Compilation Workload       Rust cargo build --release (16 threads): CPU 100%, RAM ramp, CPU Temp 84°C
T4-APP-04     AAA 4K Gaming Session            Heavy 4K gaming: GPU 99% Blaze Red, GPU Temp 82°C Crimson, GPU takes [PEAK]
T4-APP-05     Thermal Throttling & Spike       AVX2 stress: Temp spikes to 102°C (3 digits), Q4 border Crimson, throttle drop
T4-APP-06     Out-of-Memory Stress (99% RAM)   RAM climbs 45% -> 99% -> 100% -> OOM kill -> 22%; ghost 3rd digit clean wipe
T4-APP-07     Host Telemetry Dropout           USB disconnect (5s silence), display freezes cleanly, reconnects without restart
T4-APP-08     Serial Noise & Resync            UART line noise & bad magic injection, receiver drops noise, resyncs next packet
T4-APP-09     Sustained 1-Hour Long-Run        3,600s endurance test: 0 heap leaks, stack depth bounded, 0 full-screen clears
========================================================================================================================
```

---

#### Detailed Specifications: T4-APP-01 through T4-APP-09

##### `T4-APP-01`: Desktop Cold Boot & Initialization
- **Scenario**: Cold power-on of desktop monitor gadget + host machine boot sequence.
- **Workflow & Lifecycle Timeline**:
  - *Phase 1 (Hardware Reset & Display Initialization)*:
    - Microcontroller powers on. D8 (RST) pulsed LOW for $10\text{ ms}$, then HIGH.
    - Firmware transmits ILI9488 initialization sequence over 8MHz SPI: `0x01` (SWRESET), `0x11` (SLPOUT), `0x3A` (`COLMOD = 0x66`, 18-bit RGB666), `0x36` (`MADCTL = 0xA8`, landscape rotation), `0x29` (DISPON).
    - Initial full-screen clear: Whole screen ($480 \times 320$) wiped once to `Color::DARK_BG` (`#121622`).
  - *Phase 2 (Static Card Grid Layout Draw)*:
    - Firmware calls `Dashboard::draw_layout(&mut display)`.
    - 4 symmetric cards ($230 \times 145\text{ px}$) drawn at $(7, 10)$, $(243, 10)$, $(7, 165)$, $(243, 165)$ with $2\text{ px}$ borders (`#323E5A`) and panel fill (`#1C2234`).
    - 4 card header bars drawn: `"CPU LOAD"`, `"GPU LOAD"`, `"RAM USAGE"`, `"THERMALS"`.
    - Placeholder numerals rendered (`"-- %"` or `"0 %"`).
    - Empty chunky meter tracks drawn ($202 \times 24\text{ px}$).
    - Firmware writes `"GADGET_READY\n"` to USART at 57,600 baud.
  - *Phase 3 (Host Daemon Discovery & First Packet)*:
    - Linux host background daemon launches. Detects serial port `/dev/ttyUSB0` (or `/dev/ttyACM0`).
    - Reads initial 200ms warmup delta from `/proc/stat`.
    - Host transmits first 8-byte frame: `[0xAA, 0x55, 12, 45, 34, 5, 42, 100]`.
  - *Phase 4 (First Differential Update)*:
    - Firmware USART RX receives 8 bytes, decodes packet.
    - `Dashboard::update` renders live metrics: CPU 12%, GPU 5%, RAM 34%, CPU Temp 45°C, GPU Temp 42°C.
- **Concrete Assertions**:
  - `display.clear_count == 1` (executed exclusively during Phase 1 boot, never in `update`).
  - Static grid drawn with exact coordinates: Q1 at $(7, 10)$, Q2 at $(243, 10)$, Q3 at $(7, 165)$, Q4 at $(243, 165)$.
  - Phase 4 differential update executes with zero full clears.
  - All 4 meter tracks fill to initial values: CPU $24\text{ px}$, GPU $10\text{ px}$, RAM $68\text{ px}$.

##### `T4-APP-02`: Idle Desktop with Fluctuating Ambient Load
- **Scenario**: Desktop PC at idle with slight ambient background load (audio playback, background browser tabs, system daemons).
- **Workflow & Lifecycle Timeline**:
  - *Timeline (5 Seconds at 1Hz)*:
    - $T = 1\text{s}$: `[0xAA, 0x55, 3, 39, 28, 0, 41, 100]` (CPU 3%, CPU Temp 39°C, RAM 28%, GPU 0%, GPU Temp 41°C)
    - $T = 2\text{s}$: `[0xAA, 0x55, 6, 40, 28, 1, 41, 100]` (CPU 6%, CPU Temp 40°C, RAM 28%, GPU 1%, GPU Temp 41°C)
    - $T = 3\text{s}$: `[0xAA, 0x55, 8, 41, 29, 2, 42, 100]` (CPU 8%, CPU Temp 41°C, RAM 29%, GPU 2%, GPU Temp 42°C)
    - $T = 4\text{s}$: `[0xAA, 0x55, 4, 40, 29, 0, 41, 100]` (CPU 4%, CPU Temp 40°C, RAM 29%, GPU 0%, GPU Temp 41°C)
    - $T = 5\text{s}$: `[0xAA, 0x55, 2, 39, 28, 0, 40, 100]` (CPU 2%, CPU Temp 39°C, RAM 28%, GPU 0%, GPU Temp 40°C)
- **Concrete Assertions**:
  - Palette stability: All quadrants remain strictly in their nominal palettes:
    - Q1: Electric Cyan (`#00D2D3`)
    - Q2: Neon Green (`#10AC84`)
    - Q3: Vivid Violet (`#A55EEA`)
    - Q4: Cool Mint (`#1DD1A1`)
  - Low bus utilization:
    - Numeral updates touch only 1 digit column ($X_{\text{local}} = 14 \dots 34$).
    - Meter deltas are tiny ($4\text{ px}$ to $12\text{ px}$).
    - Average SPI transfer per tick $\le 4,500\text{ bytes}$ ($\le 6\text{ ms}$ transmission time, $< 1\%$ bus duty cycle).
  - `display.clear_count == 0`.

##### `T4-APP-03`: Heavy Compilation Workload (Rust `cargo build --release`)
- **Scenario**: Multi-core compilation session compiling a large Rust codebase (`cargo build --release -j16`).
- **Workflow & Lifecycle Timeline**:
  - *Phase 1 (Pre-Build Idle, $T = 0\text{s}$)*:
    - `packet = [0xAA, 0x55, 5, 42, 32, 2, 40, 100]`.
  - *Phase 2 (Compile Burst - 16 Cores Saturated, $T = 5\text{s} \dots 30\text{s}$)*:
    - CPU jumps to 100%: `packet = [0xAA, 0x55, 100, 84, 65, 4, 42, 100]`.
    - CPU reading: `"100 %"` (3 digits) in Alert Coral (`#FF6B6B`).
    - CPU meter: 100% full ($200\text{ px}$) in Alert Coral.
    - CPU Temp reaches 84°C (Crimson `#FF3838`).
    - CPU assigned `[PEAK]` badge in Q4. Q4 border turns Crimson.
  - *Phase 3 (Linker Stage - Single Thread Memory Spike, $T = 45\text{s}$)*:
    - Compiling ends; link stage starts. CPU drops to 12% (Cyan `#00D2D3`).
    - RAM spikes to 86% as linker loads large object files: RAM reading `"86 %"` in Danger Red (`#EA2027`).
    - RAM meter fills to $172\text{ px}$ in Danger Red.
    - CPU Temp cools to 65°C (Gold `#FECA57`). Q4 border reverts to `#323E5A`.
  - *Phase 4 (Build Complete & Return to Idle, $T = 60\text{s}$)*:
    - `packet = [0xAA, 0x55, 3, 46, 35, 2, 41, 100]`.
    - CPU returns to Cyan, RAM returns to Violet ($70\text{ px}$ fill), thermals return to Cool Mint.
- **Concrete Assertions**:
  - CPU palette transitions correctly: Cyan $\to$ Alert Coral $\to$ Cyan.
  - RAM palette transitions correctly: Violet $\to$ Danger Red $\to$ Violet.
  - Thermal peak assignment dynamically tracks CPU during compile burst and removes peak badge as it cools.
  - All meter contraction and expansion actions leave zero artifact pixels.

##### `T4-APP-04`: AAA 4K Gaming Session (Full GPU Load + High Thermals)
- **Scenario**: Launching a graphically intensive 4K game with ray tracing on RTX 4050/4090.
- **Workflow & Lifecycle Timeline**:
  - *Phase 1 (Game Menu Screen, $T = 0\text{s}$)*:
    - `packet = [0xAA, 0x55, 25, 52, 45, 40, 54, 100]`.
    - GPU 40% (Neon Green `#10AC84`, $80\text{ px}$ fill).
  - *Phase 2 (4K Ray Tracing Gameplay, $T = 15\text{s}$)*:
    - GPU load surges to 98%: `packet = [0xAA, 0x55, 58, 68, 72, 98, 82, 100]`.
    - GPU reading: `"98 %"` in Blaze Red (`#FF3838`).
    - GPU meter: $196\text{ px}$ fill in Blaze Red.
    - GPU Temp reaches 82°C (Crimson `#FF3838`).
    - Q4 Thermals: CPU 68°C (Gold), GPU 82°C (Crimson).
    - `[PEAK]` badge explicitly assigned to GPU!
    - Q4 card border shifts to Crimson `#FF3838`.
  - *Phase 3 (Cutscene / Reduced GPU Load, $T = 40\text{s}$)*:
    - GPU load drops to 70%: `packet = [0xAA, 0x55, 62, 70, 72, 70, 79, 100]`.
    - GPU palette transitions to Warning Orange (`#FF9F43`).
    - GPU Temp remains hot at 79°C; GPU retains `[PEAK]` badge.
  - *Phase 4 (Exit Game, $T = 60\text{s}$)*:
    - `packet = [0xAA, 0x55, 8, 48, 38, 2, 45, 100]`.
    - All metrics normalize; Q4 border reverts to `#323E5A`.
- **Concrete Assertions**:
  - GPU palette transitions: Neon Green $\to$ Blaze Red $\to$ Warning Orange $\to$ Neon Green.
  - `[PEAK]` badge correctly tags GPU (not CPU) during gameplay phases.
  - Frame delivery remains jitter-free; differential updates complete in $< 25\text{ ms}$ per second.

##### `T4-APP-05`: Thermal Throttling & Peak Temperature Spike
- **Scenario**: Severe thermal stress test (Prime95 / AVX2 stress) causing temperatures to spike into triple digits, triggering thermal throttling.
- **Workflow & Lifecycle Timeline**:
  - *Phase 1 (Pre-Stress, $T = 0\text{s}$)*:
    - `packet = [0xAA, 0x55, 80, 68, 50, 20, 55, 100]`.
  - *Phase 2 (Temperature Surge, $T = 10\text{s}$)*:
    - CPU Temp crosses critical 75°C threshold: 76°C $\to$ 88°C $\to$ 96°C.
    - Reading displays in Crimson (`#FF3838`).
    - Q4 border turns Crimson.
  - *Phase 3 (Triple-Digit Spike - 102°C, $T = 20\text{s}$)*:
    - CPU Temp reaches 102°C: `packet = [0xAA, 0x55, 99, 102, 50, 20, 56, 100]`.
    - 3-digit numeral rendering test: Numeral `"102"` + `"°C"`.
    - Glyph width expands to 3 digits ($3 \times 24 = 72\text{ px}$).
    - Bounding box must not overflow card bounds ($X_{\text{local}} = 14 \dots 100$, well within $230\text{ px}$ card width).
  - *Phase 4 (Thermal Throttling & Recovery, $T = 30\text{s}$)*:
    - CPU clocks throttle down; CPU load drops to 42%.
    - Temperature declines: 92°C $\to$ 78°C $\to$ 64°C $\to$ 55°C.
    - Numeral contracts back to 2 digits (`"55"`).
- **Concrete Assertions**:
  - 3-digit temperature 102°C renders cleanly without truncating or overflowing Q4 card border.
  - Contraction from 3 digits to 2 digits cleanly erases the 3rd digit column without leaving phantom glyphs.
  - Q4 border correctly returns to default `#323E5A` once temperature drops below 75°C.

##### `T4-APP-06`: Out-of-Memory Stress Condition (99% RAM)
- **Scenario**: Heavy dataset processing / memory leak triggering extreme RAM pressure up to 100%, followed by Linux OOM killer termination.
- **Workflow & Lifecycle Timeline**:
  - *Phase 1 (Baseline Memory, $T = 0\text{s}$)*:
    - RAM at 45%: `packet = [0xAA, 0x55, 20, 48, 45, 10, 44, 100]`. (Violet `#A55EEA`, $90\text{ px}$ fill).
  - *Phase 2 (Memory Leak Accumulation, $T = 10\text{s} \dots 25\text{s}$)*:
    - RAM climbs: 65% $\to$ 78% (Magenta Rose `#D980FA`, $156\text{ px}$ fill) $\to$ 88% (Danger Red `#EA2027`, $176\text{ px}$ fill) $\to$ 99% ($198\text{ px}$ fill).
  - *Phase 3 (Extreme 100% Saturation, $T = 30\text{s}$)*:
    - RAM hits 100%: `packet = [0xAA, 0x55, 95, 75, 100, 10, 45, 100]`.
    - Reading: `"100 %"` (3 digits) in Danger Red (`#EA2027`).
    - Meter: $200\text{ px}$ fill (entire inner track).
  - *Phase 4 (OOM Killer Intervention, $T = 31\text{s}$)*:
    - Kernel OOM killer terminates memory-hogging process.
    - RAM instantly plummets from 100% down to 22%: `packet = [0xAA, 0x55, 15, 50, 22, 10, 44, 100]`.
    - Reading contracts to `"22 %"`.
    - Meter contracts to $44\text{ px}$ fill in Vivid Violet (`#A55EEA`).
- **Concrete Assertions**:
  - Instant transition from 100% to 22% cleanly clears the 3rd digit column (no ghost `'0'` producing `"220%"`).
  - Chunky meter delta rect ($X_{\text{local}} = 59 \dots 214$, $156 \times 22\text{ px}$) is completely overwritten with `Color::PANEL_BG` (`#1C2234`).
  - Zero red pixels remain in the vacated track area.
  - Palette shifts immediately from Danger Red back to Vivid Violet.

##### `T4-APP-07`: Host Telemetry Dropout & Reconnection Recovery
- **Scenario**: Physical USB disconnect, host daemon crash, or laptop system suspend/resume cycle.
- **Workflow & Lifecycle Timeline**:
  - *Phase 1 (Active Telemetry)*:
    - Telemetry packets arrive normally at 1Hz: `[0xAA, 0x55, 45, 58, 62, 35, 52, 90]`.
  - *Phase 2 (Telemetry Dropout / Disconnect)*:
    - USB cable unplugged or host daemon stopped.
    - Zero serial bytes received for 10 consecutive seconds.
    - Gadget firmware USART receiver loop handles `nb::Error::WouldBlock` continuously.
    - Gadget display retains last known valid telemetry reading cleanly.
    - Zero display blanking, zero resets, zero MCU watchdog panics.
  - *Phase 3 (Host Reconnect & Re-enumeration)*:
    - USB reconnected. Host daemon starts, queries Linux sysfs, reopens serial port `/dev/ttyUSB0` at 57,600 baud.
    - Host sends first reconnected packet: `[0xAA, 0x55, 18, 44, 55, 8, 42, 90]`.
  - *Phase 4 (Seamless Stream Recovery)*:
    - Firmware receiver decodes valid frame immediately.
    - `Dashboard::update` renders new metrics. Firmware transmits `"ACK\n"`.
- **Concrete Assertions**:
  - During Phase 2 serial silence: MCU does not hang, heap does not leak, display does not flicker.
  - During Phase 4 recovery: First valid frame restores live updates without needing MCU power cycle or reboot.
  - No frame synchronization offset (bytes decoded with 100% alignment).

##### `T4-APP-08`: Serial Noise & Frame Desynchronization Recovery
- **Scenario**: Severe electrical noise on UART line, baud rate glitch, or partial packet truncation.
- **Workflow & Lifecycle Timeline**:
  - *Phase 1 (Clean Baseline)*:
    - Valid packet: `[0xAA, 0x55, 50, 60, 50, 50, 60, 100]`.
  - *Phase 2 (Severe Line Glitch & Split Frame)*:
    - Injected noise: 4 corrupted bytes `[0xE3, 0x91, 0x00, 0xFF]`.
    - Followed by partial frame header and split: `[0xAA, 0x55, 75]`.
    - Followed by 300ms line silence, then corrupted byte `[0xAA]`, then valid frame start: `[0xAA, 0x55, 30, 48, 40, 15, 45, 100]`.
  - *Phase 3 (Receiver State Machine Ingestion)*:
    - State machine rejects noise bytes, resets index on invalid magic, buffers partial frame, resets on gap/bad byte, and resynchronizes cleanly on `[0xAA, 0x55]`.
- **Concrete Assertions**:
  - Zero invalid packets dispatched to `Dashboard::update`.
  - Display buffer exhibits zero glitch artifacts or scrambled text.
  - Full resynchronization achieved on the subsequent valid frame.
  - `rx_idx` correctly returns to 0 after every rejection.

##### `T4-APP-09`: Sustained 1-Hour Long-Run Emulation (Zero-Flicker & Zero-Heap Stability)
- **Scenario**: Accelerated 3,600-second (1 hour) continuous endurance emulation under shifting dynamic desktop workloads.
- **Workflow & Lifecycle Timeline**:
  - *Emulation Loop (3,600 Iterations at 1Hz)*:
    - Cycles continuously through 5 simulated user workload phases:
      1. $0 \dots 600\text{s}$: Idle desktop (ambient fluctuation)
      2. $601 \dots 1500\text{s}$: Heavy compilation (CPU 100%, high thermals)
      3. $1501 \dots 1800\text{s}$: Cool down & web browsing
      4. $1801 \dots 3000\text{s}$: 4K gaming session (GPU 98%, GPU Temp 82°C)
      5. $3001 \dots 3600\text{s}$: Idle desktop return
  - *Telemetry Injection*: 3,600 valid 8-byte `TelemetryPacket` frames generated and fed through `Dashboard::update`.
- **Concrete Assertions**:
  - **Zero Dynamic Allocations**: Total heap allocations throughout 3,600 iterations == $0\text{ bytes}$. Heap break / pointer unchanged.
  - **Bounded Stack Depth**: Maximum stack usage measured across all calls $\le 256\text{ bytes}$ (leaves $> 1.7\text{ KB}$ stack headroom on ATmega328P).
  - **Static SRAM Invariance**: Static SRAM usage measured before, during, and after run remains constant at $< 100\text{ bytes}$.
  - **Zero-Flicker Guarantee**: Total calls to `display.clear()` across all 3,600 iterations == 0.
  - **SPI Transfer Bandwidth**:
    - Average SPI bytes transferred per tick $\le 12,500\text{ bytes}$ ($\le 16\text{ ms}$ SPI time at 8MHz).
    - Peak SPI bytes in worst single tick $\le 42,000\text{ bytes}$ ($\le 45\text{ ms}$ SPI time, well within 1000ms window).
  - Display state at $T = 3600\text{s}$ matches expected final packet metrics exactly, with 0 visual tearing or corruption.

---

## 5. Verification Method

To independently verify the test specifications against the codebase and test harness:

### 5.1 Unit & Test Harness Compilation Check
```bash
# 1. Verify gadget-core builds and passes unit tests in host mode
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-core
cargo test

# 2. Verify gadget-common builds and passes serialization tests
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-common
cargo test

# 3. Verify gadget-host builds and passes dry-run sampling
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-host
cargo test
cargo run -- --dry-run
```

### 5.2 AVR Binary & Static SRAM Footprint Check
```bash
# 4. Verify ATmega328P firmware binary meets Flash < 28KB and SRAM < 100B
cd /home/mahdi/Programming/perfomance-monitor/software/gadget-firmware-uno
cargo +nightly build --release
avr-size -C --mcu=atmega328p target/avr-none/release/gadget-firmware-uno.elf
```
*Pass Criteria*:
- Program (.text + .data) $\le 28,672\text{ bytes}$ (28 KB).
- Data (.data + .bss) $< 100\text{ bytes}$.
- Symbol audit confirms absence of `malloc`, `realloc`, `free`.

### 5.3 E2E Test Suite Execution
When implemented in `tests/e2e/`:
```bash
# Run Tier 3 Cross-Feature Interaction Tests
python3 tests/e2e/test_runner.py --tier 3 --verbose

# Run Tier 4 Real-World Application Scenario Tests
python3 tests/e2e/test_runner.py --tier 4 --verbose

# Run All Tiers with Structured Summary Table
python3 tests/e2e/test_runner.py --summary
```
*Pass Criteria*:
- All 18 Tier 3 tests pass (`T3-INT-01` .. `T3-INT-18`).
- All 9 Tier 4 tests pass (`T4-APP-01` .. `T4-APP-09`).
- Clean exit code 0.
