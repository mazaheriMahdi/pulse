# Tier 1 Test Case Specifications (85 Test Cases across 17 Features)
# Author: spec_miner_e2e_2

def get_tier1_tests():
    tests = []

    # =========================================================================
    # FEATURE 01: 4-Quadrant Card Grid (Survey / R1)
    # =========================================================================
    tests.append({
        "id": "T1-F01-01",
        "feature": "Feature 01: 4-Quadrant Card Grid (Survey / R1)",
        "desc": "Verify 4-quadrant screen partitioning geometry and card counts on 480x320 display.",
        "inputs": "Call `Dashboard::new()`, then `draw_layout(&mut display)` on a 480x320 display mock.",
        "expected": "Screen is partitioned into exactly 4 rectangular card bounding boxes of 230x145 pixels each.",
        "assertions": "Mock records 4 card rects: Q1 at (7, 10, 230, 145), Q2 at (243, 10, 230, 145), Q3 at (7, 165, 230, 145), Q4 at (243, 165, 230, 145)."
    })
    tests.append({
        "id": "T1-F01-02",
        "feature": "Feature 01: 4-Quadrant Card Grid (Survey / R1)",
        "desc": "Verify card border thickness (2px) and default border color (`Color::BORDER`).",
        "inputs": "`draw_layout(&mut display)` called on blank display.",
        "expected": "Each card is outlined with a 2-pixel solid border in Color::BORDER (`#323E5A` / RGB: 50, 62, 90).",
        "assertions": "Pixels at card perimeter (e.g. X in [7..8, 235..236], Y in [10..11, 153..154] for Q1) equal (50, 62, 90)."
    })
    tests.append({
        "id": "T1-F01-03",
        "feature": "Feature 01: 4-Quadrant Card Grid (Survey / R1)",
        "desc": "Verify horizontal and vertical outer margins and center gutters.",
        "inputs": "`draw_layout(&mut display)` called on display.",
        "expected": "Left margin = 7px, right margin = 7px, center X gap = 6px; Top margin = 10px, bottom margin = 10px, center Y gap = 10px.",
        "assertions": "Assert Q1.x = 7; Q2.x = 243; Q2.right = 472 (479 - 7); Q3.y = 165; Q3.bottom = 309 (319 - 10); Q1_Q2_gap = 243 - 237 = 6; Q1_Q3_gap = 165 - 155 = 10."
    })
    tests.append({
        "id": "T1-F01-04",
        "feature": "Feature 01: 4-Quadrant Card Grid (Survey / R1)",
        "desc": "Verify card interior background fill (`Color::PANEL_BG`) vs screen background (`Color::DARK_BG`).",
        "inputs": "`draw_layout(&mut display)` called on display.",
        "expected": "Screen backdrop is filled with Color::DARK_BG (`#121622` / RGB: 18, 22, 34); card interiors are filled with Color::PANEL_BG (`#1C2234` / RGB: 28, 34, 52).",
        "assertions": "Pixel (0, 0) == (18, 22, 34); Pixel (3, 3) == (18, 22, 34); Pixel (240, 50) == (18, 22, 34); Pixel (15, 20) == (28, 34, 52); Pixel (250, 20) == (28, 34, 52)."
    })
    tests.append({
        "id": "T1-F01-05",
        "feature": "Feature 01: 4-Quadrant Card Grid (Survey / R1)",
        "desc": "Verify functional metric mapping across all four quadrants.",
        "inputs": "Feed telemetry packet `[0xAA, 0x55, 42, 58, 65, 80, 71, 95]` to `Dashboard::update`.",
        "expected": "Q1 renders CPU Load (42%), Q2 renders GPU Load (80%), Q3 renders RAM Usage (65%), Q4 renders Thermals (58°C & 71°C).",
        "assertions": "Region Q1 contains '42%'; Region Q2 contains '80%'; Region Q3 contains '65%'; Region Q4 contains '58' and '71'."
    })

    # =========================================================================
    # FEATURE 02: Card Header Bar (Survey / R1)
    # =========================================================================
    tests.append({
        "id": "T1-F02-01",
        "feature": "Feature 02: Card Header Bar (Survey / R1)",
        "desc": "Verify Q1 header title text and accent color.",
        "inputs": "`draw_layout(&mut display)` called.",
        "expected": "Q1 renders 'CPU LOAD' at local (14, 8) in Electric Cyan (`#00D2D3` / RGB: 0, 210, 211).",
        "assertions": "Mock text spy records string 'CPU LOAD' at global position (21, 18) with color (0, 210, 211)."
    })
    tests.append({
        "id": "T1-F02-02",
        "feature": "Feature 02: Card Header Bar (Survey / R1)",
        "desc": "Verify Q2 header title text and accent color.",
        "inputs": "`draw_layout(&mut display)` called.",
        "expected": "Q2 renders 'GPU LOAD' at local (14, 8) in Neon Green (`#10AC84` / RGB: 16, 172, 132).",
        "assertions": "Mock text spy records string 'GPU LOAD' at global position (257, 18) with color (16, 172, 132)."
    })
    tests.append({
        "id": "T1-F02-03",
        "feature": "Feature 02: Card Header Bar (Survey / R1)",
        "desc": "Verify Q3 header title text and accent color.",
        "inputs": "`draw_layout(&mut display)` called.",
        "expected": "Q3 renders 'RAM USAGE' at local (14, 8) in Vivid Violet (`#A55EEA` / RGB: 165, 94, 234).",
        "assertions": "Mock text spy records string 'RAM USAGE' at global position (21, 173) with color (165, 94, 234)."
    })
    tests.append({
        "id": "T1-F02-04",
        "feature": "Feature 02: Card Header Bar (Survey / R1)",
        "desc": "Verify Q4 header title text and accent color.",
        "inputs": "`draw_layout(&mut display)` called.",
        "expected": "Q4 renders 'THERMALS' at local (14, 8) in Cool Mint (`#1DD1A1` / RGB: 29, 209, 161).",
        "assertions": "Mock text spy records string 'THERMALS' at global position (257, 173) with color (29, 209, 161)."
    })
    tests.append({
        "id": "T1-F02-05",
        "feature": "Feature 02: Card Header Bar (Survey / R1)",
        "desc": "Verify header typography font size (Scale 2, 14px height).",
        "inputs": "Inspect glyph dimensions emitted during card header rendering.",
        "expected": "Header labels use scale 2 font (10x14px glyphs, pitch 12px), clearly legible for section identification.",
        "assertions": "Height of rendered header characters == 14px; width == 10px; total label height <= 16px."
    })

    # =========================================================================
    # FEATURE 03: Big Block Numerals (Survey / R2)
    # =========================================================================
    tests.append({
        "id": "T1-F03-01",
        "feature": "Feature 03: Big Block Numerals (Survey / R2)",
        "desc": "Verify big block numeral height compliance (>= 28–36px).",
        "inputs": "Feed telemetry packet with CPU load = 75%.",
        "expected": "Primary numeric glyphs ('7' and '5') rendered with height between 28px and 36px.",
        "assertions": "Rendered digit bounding box height >= 28px and <= 36px."
    })
    tests.append({
        "id": "T1-F03-02",
        "feature": "Feature 03: Big Block Numerals (Survey / R2)",
        "desc": "Verify two-digit numeral rendering with percentage suffix (`62%`).",
        "inputs": "Feed telemetry packet `[0xAA, 0x55, 62, 50, 50, 50, 50, 100]`.",
        "expected": "Digits '6' and '2' rendered at card local (14, 26), followed by '%' unit suffix.",
        "assertions": "Digits decoded from framebuffer match '62'; '%' suffix detected adjacent to '2'; total width in [50..85] px."
    })
    tests.append({
        "id": "T1-F03-03",
        "feature": "Feature 03: Big Block Numerals (Survey / R2)",
        "desc": "Verify three-digit numeral rendering (`100%`).",
        "inputs": "Feed telemetry packet `[0xAA, 0x55, 100, 50, 50, 50, 50, 100]`.",
        "expected": "Digits '1', '0', '0' and '%' fit cleanly within the numeral bounding box (width <= 106px).",
        "assertions": "Digits decoded match '100'; rightmost extent X < 130; no collision with card right border (X=230)."
    })
    tests.append({
        "id": "T1-F03-04",
        "feature": "Feature 03: Big Block Numerals (Survey / R2)",
        "desc": "Verify single-digit numeral rendering (`7%`).",
        "inputs": "Feed telemetry packet `[0xAA, 0x55, 7, 50, 50, 50, 50, 100]`.",
        "expected": "Single digit '7' rendered with '%' suffix; previous digit spaces cleanly filled with `PANEL_BG`.",
        "assertions": "Only digit '7' is present; preceding character slots are blank `PANEL_BG`."
    })
    tests.append({
        "id": "T1-F03-05",
        "feature": "Feature 03: Big Block Numerals (Survey / R2)",
        "desc": "Verify unit suffix baseline alignment with big numerals.",
        "inputs": "Inspect baseline Y coordinate of '%' and '°C' relative to numeral glyph baseline.",
        "expected": "Unit suffix baseline aligns with the bottom baseline of the big block numerals.",
        "assertions": "Suffix baseline Y == Numeral baseline Y; suffix height in [14..20] px."
    })

    # =========================================================================
    # FEATURE 04: Arm's-Length Legibility (Survey / R2)
    # =========================================================================
    tests.append({
        "id": "T1-F04-01",
        "feature": "Feature 04: Arm's-Length Legibility (Survey / R2)",
        "desc": "Verify optical visual angle >= 20 arcminutes at 60 cm desk distance.",
        "inputs": "Numeral pixel height = 28px on 166 DPI screen (pixel pitch = 0.153mm), viewing distance = 600mm.",
        "expected": "Physical height = 4.28mm; subtended visual angle = 24.5 arcminutes.",
        "assertions": "Calculated visual angle >= 20.0 arcminutes; complies with ISO 9241-303."
    })
    tests.append({
        "id": "T1-F04-02",
        "feature": "Feature 04: Arm's-Length Legibility (Survey / R2)",
        "desc": "Verify optical visual angle >= 20 arcminutes at 70 cm sitting distance.",
        "inputs": "Numeral pixel height = 28px, viewing distance = 700mm.",
        "expected": "Physical height = 4.28mm; subtended visual angle = 21.0 arcminutes.",
        "assertions": "Calculated visual angle >= 20.0 arcminutes; glanceable from normal sitting posture."
    })
    tests.append({
        "id": "T1-F04-03",
        "feature": "Feature 04: Arm's-Length Legibility (Survey / R2)",
        "desc": "Verify optical visual angle >= 20 arcminutes at 90 cm maximum desk distance with 35px font.",
        "inputs": "Numeral pixel height = 35px (scale 5), viewing distance = 900mm.",
        "expected": "Physical height = 5.36mm; subtended visual angle = 20.5 arcminutes.",
        "assertions": "Calculated visual angle >= 20.0 arcminutes."
    })
    tests.append({
        "id": "T1-F04-04",
        "feature": "Feature 04: Arm's-Length Legibility (Survey / R2)",
        "desc": "Verify complete elimination of sub-14px text on primary telemetry paths.",
        "inputs": "Audit all font rendering calls in `gadget-core` during primary metric updates.",
        "expected": "Zero primary readings use Scale 1 (7px) font. Primary numerals use >= 28px, secondary labels use >= 14px.",
        "assertions": "Assertion passes: no call to draw primary metric has font_height < 28px; no label has font_height < 14px."
    })
    tests.append({
        "id": "T1-F04-05",
        "feature": "Feature 04: Arm's-Length Legibility (Survey / R2)",
        "desc": "Verify glyph stroke thickness for high glanceability.",
        "inputs": "Measure vertical and horizontal stroke width of rendered big numerals.",
        "expected": "Stroke thickness is >= 4 pixels, providing high contrast and visual weight.",
        "assertions": "Stroke width >= 4px on all numeric segments."
    })

    # =========================================================================
    # FEATURE 05: Chunky Visual Meters (Survey / R3)
    # =========================================================================
    tests.append({
        "id": "T1-F05-01",
        "feature": "Feature 05: Chunky Visual Meters (Survey / R3)",
        "desc": "Verify chunky meter track physical dimensions (20–24px height, 200px width).",
        "inputs": "Inspect meter track geometry in card layout.",
        "expected": "Outer track height = 24px, inner fill height = 22px, inner fill width = 200px.",
        "assertions": "Track outer height in [20, 24]; inner height == 22px; inner width == 200px."
    })
    tests.append({
        "id": "T1-F05-02",
        "feature": "Feature 05: Chunky Visual Meters (Survey / R3)",
        "desc": "Verify exact linear 1:2 scaling relationship (1% = 2 pixels).",
        "inputs": "Feed telemetry values: 10%, 25%, 50%, 75%.",
        "expected": "Active bar fill width is exactly 20px, 50px, 100px, 150px respectively.",
        "assertions": "Measured fill width == 2 * value pixels for each input."
    })
    tests.append({
        "id": "T1-F05-03",
        "feature": "Feature 05: Chunky Visual Meters (Survey / R3)",
        "desc": "Verify 100% full-scale meter fill.",
        "inputs": "Feed metric value = 100%.",
        "expected": "Fill width is exactly 200px, filling the active track completely.",
        "assertions": "Fill width == 200px; unfilled track width == 0px."
    })
    tests.append({
        "id": "T1-F05-04",
        "feature": "Feature 05: Chunky Visual Meters (Survey / R3)",
        "desc": "Verify 0% zero-scale meter fill.",
        "inputs": "Feed metric value = 0%.",
        "expected": "Fill width is 0px; inner track is entirely filled with background Color::DARK_BG.",
        "assertions": "Fill width == 0px; all 200x22 pixels in track match Color::DARK_BG (`#121622`)."
    })
    tests.append({
        "id": "T1-F05-05",
        "feature": "Feature 05: Chunky Visual Meters (Survey / R3)",
        "desc": "Verify meter track border outline and inset styling.",
        "inputs": "Inspect track perimeter pixels.",
        "expected": "Track is surrounded by a 1px border in Color::BORDER (`#323E5A`).",
        "assertions": "Perimeter border pixels at local (14, 70) to (215, 93) match (50, 62, 90)."
    })

    # =========================================================================
    # FEATURE 06: Dynamic CPU Palette (Survey / R3)
    # =========================================================================
    tests.append({
        "id": "T1-F06-01",
        "feature": "Feature 06: Dynamic CPU Palette (Survey / R3)",
        "desc": "Verify CPU nominal load palette (< 60%).",
        "inputs": "Telemetry packet with `cpu_percent = 30`.",
        "expected": "Meter and numeral color is Electric Cyan (`#00D2D3` / RGB: 0, 210, 211).",
        "assertions": "Color == (0, 210, 211)."
    })
    tests.append({
        "id": "T1-F06-02",
        "feature": "Feature 06: Dynamic CPU Palette (Survey / R3)",
        "desc": "Verify CPU warning load palette (60–84%).",
        "inputs": "Telemetry packet with `cpu_percent = 72`.",
        "expected": "Meter and numeral color is Coral Amber (`#FFA502` / RGB: 255, 165, 2).",
        "assertions": "Color == (255, 165, 2)."
    })
    tests.append({
        "id": "T1-F06-03",
        "feature": "Feature 06: Dynamic CPU Palette (Survey / R3)",
        "desc": "Verify CPU alert load palette (>= 85%).",
        "inputs": "Telemetry packet with `cpu_percent = 92`.",
        "expected": "Meter and numeral color is Alert Coral (`#FF6B6B` / RGB: 255, 107, 107).",
        "assertions": "Color == (255, 107, 107)."
    })
    tests.append({
        "id": "T1-F06-04",
        "feature": "Feature 06: Dynamic CPU Palette (Survey / R3)",
        "desc": "Verify CPU color at lower bound (0%).",
        "inputs": "Telemetry packet with `cpu_percent = 0`.",
        "expected": "Color is Electric Cyan (`#00D2D3`).",
        "assertions": "Color == (0, 210, 211)."
    })
    tests.append({
        "id": "T1-F06-05",
        "feature": "Feature 06: Dynamic CPU Palette (Survey / R3)",
        "desc": "Verify CPU color at upper bound (100%).",
        "inputs": "Telemetry packet with `cpu_percent = 100`.",
        "expected": "Color is Alert Coral (`#FF6B6B`).",
        "assertions": "Color == (255, 107, 107)."
    })

    # =========================================================================
    # FEATURE 07: Dynamic GPU Palette (Survey / R3)
    # =========================================================================
    tests.append({
        "id": "T1-F07-01",
        "feature": "Feature 07: Dynamic GPU Palette (Survey / R3)",
        "desc": "Verify GPU nominal load palette (< 65%).",
        "inputs": "Telemetry packet with `gpu_percent = 45`.",
        "expected": "Color is Neon Green (`#10AC84` / RGB: 16, 172, 132).",
        "assertions": "Color == (16, 172, 132)."
    })
    tests.append({
        "id": "T1-F07-02",
        "feature": "Feature 07: Dynamic GPU Palette (Survey / R3)",
        "desc": "Verify GPU warning load palette (65–84%).",
        "inputs": "Telemetry packet with `gpu_percent = 75`.",
        "expected": "Color is Warning Orange (`#FF9F43` / RGB: 255, 159, 67).",
        "assertions": "Color == (255, 159, 67)."
    })
    tests.append({
        "id": "T1-F07-03",
        "feature": "Feature 07: Dynamic GPU Palette (Survey / R3)",
        "desc": "Verify GPU danger load palette (>= 85%).",
        "inputs": "Telemetry packet with `gpu_percent = 95`.",
        "expected": "Color is Blaze Red (`#FF3838` / RGB: 255, 56, 56).",
        "assertions": "Color == (255, 56, 56)."
    })
    tests.append({
        "id": "T1-F07-04",
        "feature": "Feature 07: Dynamic GPU Palette (Survey / R3)",
        "desc": "Verify GPU color at lower bound (0%).",
        "inputs": "Telemetry packet with `gpu_percent = 0`.",
        "expected": "Color is Neon Green (`#10AC84`).",
        "assertions": "Color == (16, 172, 132)."
    })
    tests.append({
        "id": "T1-F07-05",
        "feature": "Feature 07: Dynamic GPU Palette (Survey / R3)",
        "desc": "Verify GPU color at upper bound (100%).",
        "inputs": "Telemetry packet with `gpu_percent = 100`.",
        "expected": "Color is Blaze Red (`#FF3838`).",
        "assertions": "Color == (255, 56, 56)."
    })

    # =========================================================================
    # FEATURE 08: Dynamic RAM Palette (Survey / R3)
    # =========================================================================
    tests.append({
        "id": "T1-F08-01",
        "feature": "Feature 08: Dynamic RAM Palette (Survey / R3)",
        "desc": "Verify RAM nominal usage palette (< 70%).",
        "inputs": "Telemetry packet with `ram_percent = 55`.",
        "expected": "Color is Vivid Violet (`#A55EEA` / RGB: 165, 94, 234).",
        "assertions": "Color == (165, 94, 234)."
    })
    tests.append({
        "id": "T1-F08-02",
        "feature": "Feature 08: Dynamic RAM Palette (Survey / R3)",
        "desc": "Verify RAM elevated usage palette (70–84%).",
        "inputs": "Telemetry packet with `ram_percent = 78`.",
        "expected": "Color is Magenta Rose (`#D980FA` / RGB: 217, 128, 250).",
        "assertions": "Color == (217, 128, 250)."
    })
    tests.append({
        "id": "T1-F08-03",
        "feature": "Feature 08: Dynamic RAM Palette (Survey / R3)",
        "desc": "Verify RAM danger usage palette (>= 85%).",
        "inputs": "Telemetry packet with `ram_percent = 92`.",
        "expected": "Color is Danger Red (`#EA2027` / RGB: 234, 32, 39).",
        "assertions": "Color == (234, 32, 39)."
    })
    tests.append({
        "id": "T1-F08-04",
        "feature": "Feature 08: Dynamic RAM Palette (Survey / R3)",
        "desc": "Verify RAM color at lower bound (0%).",
        "inputs": "Telemetry packet with `ram_percent = 0`.",
        "expected": "Color is Vivid Violet (`#A55EEA`).",
        "assertions": "Color == (165, 94, 234)."
    })
    tests.append({
        "id": "T1-F08-05",
        "feature": "Feature 08: Dynamic RAM Palette (Survey / R3)",
        "desc": "Verify RAM color at upper bound (100%).",
        "inputs": "Telemetry packet with `ram_percent = 100`.",
        "expected": "Color is Danger Red (`#EA2027`).",
        "assertions": "Color == (234, 32, 39)."
    })

    # =========================================================================
    # FEATURE 09: Dynamic Thermal Palette (Survey / R3)
    # =========================================================================
    tests.append({
        "id": "T1-F09-01",
        "feature": "Feature 09: Dynamic Thermal Palette (Survey / R3)",
        "desc": "Verify thermal cool palette (< 60°C).",
        "inputs": "Telemetry packet with temperature = 48°C.",
        "expected": "Color is Cool Mint (`#1DD1A1` / RGB: 29, 209, 161).",
        "assertions": "Color == (29, 209, 161)."
    })
    tests.append({
        "id": "T1-F09-02",
        "feature": "Feature 09: Dynamic Thermal Palette (Survey / R3)",
        "desc": "Verify thermal warm/elevated palette (60–75°C).",
        "inputs": "Telemetry packet with temperature = 68°C.",
        "expected": "Color is Gold / Amber (`#FECA57` / RGB: 254, 202, 87).",
        "assertions": "Color == (254, 202, 87)."
    })
    tests.append({
        "id": "T1-F09-03",
        "feature": "Feature 09: Dynamic Thermal Palette (Survey / R3)",
        "desc": "Verify thermal critical palette (> 75°C).",
        "inputs": "Telemetry packet with temperature = 82°C.",
        "expected": "Color is Crimson (`#FF3838` / RGB: 255, 56, 56).",
        "assertions": "Color == (255, 56, 56)."
    })
    tests.append({
        "id": "T1-F09-04",
        "feature": "Feature 09: Dynamic Thermal Palette (Survey / R3)",
        "desc": "Verify thermal color at lower bound (0°C).",
        "inputs": "Telemetry packet with temperature = 0°C.",
        "expected": "Color is Cool Mint (`#1DD1A1`).",
        "assertions": "Color == (29, 209, 161)."
    })
    tests.append({
        "id": "T1-F09-05",
        "feature": "Feature 09: Dynamic Thermal Palette (Survey / R3)",
        "desc": "Verify thermal color at upper bound (100°C).",
        "inputs": "Telemetry packet with temperature = 100°C.",
        "expected": "Color is Crimson (`#FF3838`).",
        "assertions": "Color == (255, 56, 56)."
    })

    # =========================================================================
    # FEATURE 10: Dual Temp & Peak Highlight (Survey / R1, R3)
    # =========================================================================
    tests.append({
        "id": "T1-F10-01",
        "feature": "Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)",
        "desc": "Verify simultaneous CPU and GPU temperature display in Q4.",
        "inputs": "Packet with `cpu_temp_c = 64`, `gpu_temp_c = 78`.",
        "expected": "Q4 displays both CPU (64°C) and GPU (78°C) numeric values side-by-side.",
        "assertions": "Q4 region contains strings '64' and '78' with '°C' units."
    })
    tests.append({
        "id": "T1-F10-02",
        "feature": "Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)",
        "desc": "Verify peak highlight badge on higher GPU temperature.",
        "inputs": "Packet with `cpu_temp_c = 58`, `gpu_temp_c = 72`.",
        "expected": "GPU temperature is tagged with `[PEAK]` highlight badge in Gold (`#FECA57`); CPU text is dimmed in `Color::TEXT_MUTED`.",
        "assertions": "Badge `[PEAK]` located adjacent to GPU text; GPU color == (254, 202, 87); CPU color == (130, 145, 175)."
    })
    tests.append({
        "id": "T1-F10-03",
        "feature": "Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)",
        "desc": "Verify peak highlight badge on higher CPU temperature.",
        "inputs": "Packet with `cpu_temp_c = 84`, `gpu_temp_c = 65`.",
        "expected": "CPU temperature is tagged with `[PEAK]` highlight badge in Crimson (`#FF3838`); GPU text is dimmed in `Color::TEXT_MUTED`.",
        "assertions": "Badge `[PEAK]` located adjacent to CPU text; CPU color == (255, 56, 56); GPU color == (130, 145, 175)."
    })
    tests.append({
        "id": "T1-F10-04",
        "feature": "Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)",
        "desc": "Verify Q4 card border switches to Crimson when peak temp > 75°C.",
        "inputs": "Packet with `cpu_temp_c = 82`, `gpu_temp_c = 70` (peak = 82°C).",
        "expected": "Q4 card border turns Crimson (`#FF3838`), warning user of high thermal state.",
        "assertions": "Q4 border pixels match (255, 56, 56)."
    })
    tests.append({
        "id": "T1-F10-05",
        "feature": "Feature 10: Dual Temp & Peak Highlight (Survey / R1, R3)",
        "desc": "Verify Q4 card border remains default `Color::BORDER` when peak temp <= 75°C.",
        "inputs": "Packet with `cpu_temp_c = 65`, `gpu_temp_c = 74` (peak = 74°C).",
        "expected": "Q4 card border remains Color::BORDER (`#323E5A` / RGB: 50, 62, 90).",
        "assertions": "Q4 border pixels match (50, 62, 90)."
    })

    # =========================================================================
    # FEATURE 11: Differential Redraw Engine (Survey / R4)
    # =========================================================================
    tests.append({
        "id": "T1-F11-01",
        "feature": "Feature 11: Differential Redraw Engine (Survey / R4)",
        "desc": "Verify dirty bounding-box isolation on single metric change.",
        "inputs": "Initial packet: `[0xAA, 0x55, 40, 50, 50, 50, 50, 100]`. Second packet: `[0xAA, 0x55, 45, 50, 50, 50, 50, 100]`.",
        "expected": "Only Q1 (CPU) numeral box and meter delta rect are redrawn; Q2, Q3, Q4 receive 0 SPI pixel writes.",
        "assertions": "All SPI window commands (0x2A, 0x2B) during second update are within X: [7..236], Y: [10..154]."
    })
    tests.append({
        "id": "T1-F11-02",
        "feature": "Feature 11: Differential Redraw Engine (Survey / R4)",
        "desc": "Verify zero SPI transactions emitted on identical consecutive packets.",
        "inputs": "Initial packet: `[0xAA, 0x55, 50, 60, 70, 80, 65, 100]`. Second packet: identical.",
        "expected": "Differential redraw engine detects equality and emits 0 SPI transactions.",
        "assertions": "Mock SPI byte count during second update == 0 bytes."
    })
    tests.append({
        "id": "T1-F11-03",
        "feature": "Feature 11: Differential Redraw Engine (Survey / R4)",
        "desc": "Verify independent quadrant dirty tracking.",
        "inputs": "Packet changing only RAM (Q3) and GPU Temp (Q4).",
        "expected": "Redraws occur only within Q3 and Q4 bounds; Q1 and Q2 are completely untouched.",
        "assertions": "Zero SPI writes directed at Q1 or Q2 pixel coordinates."
    })
    tests.append({
        "id": "T1-F11-04",
        "feature": "Feature 11: Differential Redraw Engine (Survey / R4)",
        "desc": "Verify SPI bandwidth economy for typical single-metric update (< 5,000 bytes).",
        "inputs": "Single metric increments by 2%.",
        "expected": "Total SPI transmission payload < 5,000 bytes (< 6.25 ms bus time at 8MHz).",
        "assertions": "Total SPI bytes <= 5000."
    })
    tests.append({
        "id": "T1-F11-05",
        "feature": "Feature 11: Differential Redraw Engine (Survey / R4)",
        "desc": "Verify worst-case multi-quadrant dirty bounding box updates (< 35,000 bytes).",
        "inputs": "All 4 quadrants change simultaneously.",
        "expected": "Targeted dirty bounding boxes are refreshed without clearing the full screen; total SPI bytes < 35,000 bytes (< 45ms).",
        "assertions": "display.clear() was NOT called; total SPI bytes <= 35000."
    })

    # =========================================================================
    # FEATURE 12: Zero-Flicker Execution (Survey / R4)
    # =========================================================================
    tests.append({
        "id": "T1-F12-01",
        "feature": "Feature 12: Zero-Flicker Execution (Survey / R4)",
        "desc": "Verify static layout is drawn exactly once during initialization.",
        "inputs": "Call `Dashboard::new()`, then `draw_layout()`, followed by 10 `update()` ticks.",
        "expected": "`draw_layout()` executed once; full screen clear and card border draws are not repeated in `update()`.",
        "assertions": "Mock display `clear()` call count == 1 (only at startup); `draw_layout` call count == 1."
    })
    tests.append({
        "id": "T1-F12-02",
        "feature": "Feature 12: Zero-Flicker Execution (Survey / R4)",
        "desc": "Verify continuous telemetry updates execute with zero full-screen clears.",
        "inputs": "Feed 30 telemetry packets with fluctuating values.",
        "expected": "`display.clear()` is called 0 times during all 30 updates, completely eliminating full-screen strobe flashes.",
        "assertions": "`clear()` call count during update loop == 0."
    })
    tests.append({
        "id": "T1-F12-03",
        "feature": "Feature 12: Zero-Flicker Execution (Survey / R4)",
        "desc": "Verify in-place numeral box clearing without perturbing adjacent elements.",
        "inputs": "Update CPU load from 45% to 46%.",
        "expected": "Only the 106x36px numeral box is cleared with `PANEL_BG` and redrawn; header and borders remain intact.",
        "assertions": "Surrounding header pixels in [0..220, 0..24] and borders undergo 0 redraws."
    })
    tests.append({
        "id": "T1-F12-04",
        "feature": "Feature 12: Zero-Flicker Execution (Survey / R4)",
        "desc": "Verify incremental meter delta fill without redrawing existing bar.",
        "inputs": "CPU load increases from 40% to 45% (both in Electric Cyan).",
        "expected": "Only the +10px delta rect (200 * 5 / 100 = 10px) is filled; existing 80px bar is not redrawn.",
        "assertions": "SPI window set strictly for delta region X: [95..104]; pixels 0..79 untouched."
    })
    tests.append({
        "id": "T1-F12-05",
        "feature": "Feature 12: Zero-Flicker Execution (Survey / R4)",
        "desc": "Verify total update cycle duration is comfortably under 50ms at 8MHz SPI.",
        "inputs": "Simulate worst-case 4-quadrant update at 8MHz SPI clock.",
        "expected": "Update finishes in < 50ms, allowing a 1000ms update rate with > 95% bus idle time.",
        "assertions": "Simulated transmission duration <= 50.0 ms."
    })

    # =========================================================================
    # FEATURE 13: Zero-Heap Architecture (Survey / R4)
    # =========================================================================
    tests.append({
        "id": "T1-F13-01",
        "feature": "Feature 13: Zero-Heap Architecture (Survey / R4)",
        "desc": "Verify `#![no_std]` compliance in `gadget-core`.",
        "inputs": "Inspect `software/gadget-core/src/lib.rs`.",
        "expected": "`#![no_std]` declared at crate root; no reference to `extern crate alloc;`.",
        "assertions": "`#![no_std]` is present; `alloc` is absent."
    })
    tests.append({
        "id": "T1-F13-02",
        "feature": "Feature 13: Zero-Heap Architecture (Survey / R4)",
        "desc": "Verify `#![no_std]` compliance in `gadget-common`.",
        "inputs": "Inspect `software/gadget-common/src/lib.rs`.",
        "expected": "`#![no_std]` declared; stack-only structures.",
        "assertions": "`#![no_std]` is present; zero heap dependencies."
    })
    tests.append({
        "id": "T1-F13-03",
        "feature": "Feature 13: Zero-Heap Architecture (Survey / R4)",
        "desc": "Verify `#![no_std]` and `#![no_main]` in `gadget-firmware-uno`.",
        "inputs": "Inspect `software/gadget-firmware-uno/src/main.rs`.",
        "expected": "`#![no_std]` and `#![no_main]` declared; uses `panic-halt`.",
        "assertions": "`#![no_std]` and `#![no_main]` are present."
    })
    tests.append({
        "id": "T1-F13-04",
        "feature": "Feature 13: Zero-Heap Architecture (Survey / R4)",
        "desc": "Verify complete absence of dynamic memory allocation symbols in ELF binary.",
        "inputs": "Run `avr-nm` on `gadget-firmware-uno.elf`.",
        "expected": "Zero occurrences of `malloc`, `free`, `realloc`, `__rust_alloc`, `__rust_dealloc`.",
        "assertions": "Symbol audit returns 0 heap allocation symbols."
    })
    tests.append({
        "id": "T1-F13-05",
        "feature": "Feature 13: Zero-Heap Architecture (Survey / R4)",
        "desc": "Verify deterministic call stack bounds (< 256 bytes frame).",
        "inputs": "Analyze call graph stack depth of `Dashboard::update`.",
        "expected": "Max stack frame depth is < 256 bytes, safe for 2KB SRAM ATmega328P.",
        "assertions": "Max function stack frame < 256 bytes."
    })

    # =========================================================================
    # FEATURE 14: Static SRAM Ceiling (Survey / R4)
    # =========================================================================
    tests.append({
        "id": "T1-F14-01",
        "feature": "Feature 14: Static SRAM Ceiling (Survey / R4)",
        "desc": "Verify total static SRAM (.data + .bss) is <= 100 bytes on ATmega328P.",
        "inputs": "Run `avr-size -C --mcu=atmega328p gadget-firmware-uno.elf`.",
        "expected": "Data section total (.data + .bss) <= 100 bytes.",
        "assertions": "Data size reported by avr-size <= 100 bytes."
    })
    tests.append({
        "id": "T1-F14-02",
        "feature": "Feature 14: Static SRAM Ceiling (Survey / R4)",
        "desc": "Verify `.data` section size <= 80 bytes.",
        "inputs": "Run `avr-size -A gadget-firmware-uno.elf`.",
        "expected": "`.data` section is <= 80 bytes.",
        "assertions": "`.data` <= 80 bytes."
    })
    tests.append({
        "id": "T1-F14-03",
        "feature": "Feature 14: Static SRAM Ceiling (Survey / R4)",
        "desc": "Verify `.bss` section size <= 20 bytes.",
        "inputs": "Run `avr-size -A gadget-firmware-uno.elf`.",
        "expected": "`.bss` section is <= 20 bytes (only peripheral singletons).",
        "assertions": "`.bss` <= 20 bytes."
    })
    tests.append({
        "id": "T1-F14-04",
        "feature": "Feature 14: Static SRAM Ceiling (Survey / R4)",
        "desc": "Verify font tables are stored in Flash (PROGMEM) or procedural generator, not SRAM.",
        "inputs": "Inspect symbol table of `gadget-firmware-uno.elf`.",
        "expected": "No 475-byte `FONT_5X7` in `.data` (RAM address 0x800100+).",
        "assertions": "Font table symbols reside in Flash (.text/.progmem) or are procedurally synthesized."
    })
    tests.append({
        "id": "T1-F14-05",
        "feature": "Feature 14: Static SRAM Ceiling (Survey / R4)",
        "desc": "Verify `Dashboard` struct size is <= 16 bytes on stack.",
        "inputs": "Check `core::mem::size_of::<Dashboard>()`.",
        "expected": "`Dashboard` struct contains only `last_packet: Option<TelemetryPacket>` (9 bytes) + `initialized: bool` (1 byte) + padding <= 16 bytes.",
        "assertions": "`size_of::<Dashboard>()` <= 16."
    })

    # =========================================================================
    # FEATURE 15: Flash Ceiling (< 28KB) (Survey / R4)
    # =========================================================================
    tests.append({
        "id": "T1-F15-01",
        "feature": "Feature 15: Flash Ceiling (< 28KB) (Survey / R4)",
        "desc": "Verify total compiled Flash binary size < 28,672 bytes (28 KB).",
        "inputs": "Run `avr-size -C --mcu=atmega328p gadget-firmware-uno.elf`.",
        "expected": "Program (.text + .data + .bootloader) < 28,672 bytes.",
        "assertions": "Program bytes < 28672."
    })
    tests.append({
        "id": "T1-F15-02",
        "feature": "Feature 15: Flash Ceiling (< 28KB) (Survey / R4)",
        "desc": "Verify release build profile compiler optimizations in Cargo.toml.",
        "inputs": "Inspect `software/gadget-firmware-uno/Cargo.toml`.",
        "expected": "`opt-level = 's'` or `'z'`, `lto = true`, `codegen-units = 1`.",
        "assertions": "Profile flags are configured for aggressive size reduction."
    })
    tests.append({
        "id": "T1-F15-03",
        "feature": "Feature 15: Flash Ceiling (< 28KB) (Survey / R4)",
        "desc": "Verify bootloader safety margin (>= 4 KB Flash headroom).",
        "inputs": "Calculate $32,768 - \\text{Program Bytes}$.",
        "expected": "Free Flash >= 4,096 bytes (leaves room for 2KB bootloader + 2KB future headroom).",
        "assertions": "32768 - Program Bytes >= 4096."
    })
    tests.append({
        "id": "T1-F15-04",
        "feature": "Feature 15: Flash Ceiling (< 28KB) (Survey / R4)",
        "desc": "Verify individual function sizes remain compact (< 2,048 bytes).",
        "inputs": "Run `avr-nm --size-sort -C gadget-firmware-uno.elf`.",
        "expected": "No single compiled function exceeds 2,048 bytes of Flash.",
        "assertions": "Max function size <= 2048 bytes."
    })
    tests.append({
        "id": "T1-F15-05",
        "feature": "Feature 15: Flash Ceiling (< 28KB) (Survey / R4)",
        "desc": "Verify unused modules (e.g. `pet.rs`) are stripped via LTO.",
        "inputs": "Inspect symbol table for unlinked companion pet symbols.",
        "expected": "Zero symbols related to `pet.rs` exist in the ELF binary.",
        "assertions": "No `pet` symbol found in ELF."
    })

    # =========================================================================
    # FEATURE 16: Serial Packet Protocol (Survey / R5)
    # =========================================================================
    tests.append({
        "id": "T1-F16-01",
        "feature": "Feature 16: Serial Packet Protocol (Survey / R5)",
        "desc": "Verify happy-path packet encode and decode roundtrip.",
        "inputs": "Construct `TelemetryPacket::new(45, 68, 72, 85, 62, 95)`.",
        "expected": "Encodes into 8 bytes `[0xAA, 0x55, 45, 68, 72, 85, 62, 95]`, and decodes back to identical struct.",
        "assertions": "Encoded array matches expected; `decode(&buf).unwrap() == packet`."
    })
    tests.append({
        "id": "T1-F16-02",
        "feature": "Feature 16: Serial Packet Protocol (Survey / R5)",
        "desc": "Verify magic header bytes `MAGIC_0 == 0xAA` and `MAGIC_1 == 0x55`.",
        "inputs": "Inspect `MAGIC_0` and `MAGIC_1` constants.",
        "expected": "`MAGIC_0` is `0xAA`, `MAGIC_1` is `0x55`.",
        "assertions": "`buf[0] == 0xAA && buf[1] == 0x55`."
    })
    tests.append({
        "id": "T1-F16-03",
        "feature": "Feature 16: Serial Packet Protocol (Survey / R5)",
        "desc": "Verify exact field mapping of all 6 payload bytes.",
        "inputs": "Decode `[0xAA, 0x55, 12, 34, 56, 78, 90, 99]`.",
        "expected": "cpu=12, cpu_temp=34, ram=56, gpu=78, gpu_temp=90, battery=99.",
        "assertions": "packet.cpu_percent == 12; packet.cpu_temp_c == 34; packet.ram_percent == 56; packet.gpu_percent == 78; packet.gpu_temp_c == 90; packet.battery_percent == 99."
    })
    tests.append({
        "id": "T1-F16-04",
        "feature": "Feature 16: Serial Packet Protocol (Survey / R5)",
        "desc": "Verify fixed packet length constant `PACKET_LEN == 8`.",
        "inputs": "Check `gadget_common::PACKET_LEN`.",
        "expected": "Constant equals 8.",
        "assertions": "`PACKET_LEN == 8`."
    })
    tests.append({
        "id": "T1-F16-05",
        "feature": "Feature 16: Serial Packet Protocol (Survey / R5)",
        "desc": "Verify non-blocking UART receiver sliding window synchronization in firmware.",
        "inputs": "Stream bytes with noise prefix: `[0x00, 0xFF, 0xAA, 0x55, 50, 60, 70, 80, 65, 100]`.",
        "expected": "Firmware discards leading noise, locks onto `0xAA 0x55`, decodes packet upon receiving 8th byte, and transmits 'ACK\\n'.",
        "assertions": "Packet decoded cleanly; UART output contains 'ACK'."
    })

    # =========================================================================
    # FEATURE 17: Host Hardware Telemetry (Survey / R5)
    # =========================================================================
    tests.append({
        "id": "T1-F17-01",
        "feature": "Feature 17: Host Hardware Telemetry (Survey / R5)",
        "desc": "Verify CPU telemetry sampling from `/proc/stat` delta.",
        "inputs": "Feed two mock `/proc/stat` samples over 200ms interval.",
        "expected": "Accurately computes CPU load percentage via `(delta_total - delta_idle) / delta_total * 100`.",
        "assertions": "Result matches mathematical formula within +/- 1%."
    })
    tests.append({
        "id": "T1-F17-02",
        "feature": "Feature 17: Host Hardware Telemetry (Survey / R5)",
        "desc": "Verify RAM usage sampling from `/proc/meminfo`.",
        "inputs": "Mock `/proc/meminfo` with `MemTotal: 32000000 kB` and `MemAvailable: 8000000 kB`.",
        "expected": "RAM usage percentage computed as `(32000000 - 8000000) / 32000000 * 100 = 75%`.",
        "assertions": "Returned RAM percentage == 75."
    })
    tests.append({
        "id": "T1-F17-03",
        "feature": "Feature 17: Host Hardware Telemetry (Survey / R5)",
        "desc": "Verify CPU temperature collection via `k10temp` hwmon.",
        "inputs": "Mock `/sys/class/hwmon` with directory `name == 'k10temp'` containing `temp1_input = 74500`.",
        "expected": "Reads millidegrees and converts to `74°C` (`74500 / 1000`).",
        "assertions": "Returned CPU temperature == 74."
    })
    tests.append({
        "id": "T1-F17-04",
        "feature": "Feature 17: Host Hardware Telemetry (Survey / R5)",
        "desc": "Verify GPU telemetry parsing from `nvidia-smi` output.",
        "inputs": "Mock output from `nvidia-smi`: `'42, 65'\\n`.",
        "expected": "Parses GPU load = 42%, GPU temperature = 65°C.",
        "assertions": "GPU load == 42; GPU temperature == 65."
    })
    tests.append({
        "id": "T1-F17-05",
        "feature": "Feature 17: Host Hardware Telemetry (Survey / R5)",
        "desc": "Verify host CLI `--dry-run` flag execution.",
        "inputs": "Execute `cargo run -- --dry-run --interval 200` with timeout 1s.",
        "expected": "Prints formatted metrics line to stdout without attempting to open physical serial port.",
        "assertions": "Stdout contains `[Metrics] CPU:`; process exits cleanly."
    })

    return tests

print("Tier 1 test specifications compiled.")
