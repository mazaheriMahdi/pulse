#!/usr/bin/env python3
"""
Exhaustive specification compiler for E2E Test Suite Tiers 1 and 2 across 17 features.
Author: spec_miner_e2e_2
"""
import sys

def get_features_discovered():
    return [
        (1, "Layout", "4-Quadrant Card Grid", "480x320 landscape partitioned into 4 symmetric 230x145px cards with 2px borders", "Display resolution (480x320), margins (7px X, 10px Y), center gaps (6px X, 10px Y)", "4 distinct card bounds (Q1, Q2, Q3, Q4) with dark gaps", "Clamps to screen bounds (480x320)", "ORIGINAL_REQUEST.md:12-17, PROJECT.md:27"),
        (2, "Layout", "Card Header Bar", "Top label bar inside each card rendering quadrant metric title and accent icon", "Card origin (X, Y), quadrant type", "Rendered title label (14px tall, scale 2) at local Y+8", "Truncates cleanly if label exceeds card inner width (202px)", "ORIGINAL_REQUEST.md:13-17, PROJECT.md:28"),
        (3, "Typography", "Big Block Numerals", "Prominent primary numerals >= 28–36px tall for arm's-length legibility", "Value (0..100, °C), scale factor 4 or 5", "Rendered glyphs with uniform pitch and baseline alignment", "Clamps out-of-range values or renders error glyphs without crash", "ORIGINAL_REQUEST.md:19-20, PROJECT.md:29"),
        (4, "Typography", "Arm's-Length Legibility", "Subtends >= 20 arcminutes visual angle at 60–90cm viewing distance; eliminate sub-14px primary text", "Glyph height (28–36px), display DPI (166), sitting distance (600–900mm)", "Physical glyph height 4.28–5.51mm, visual angle 16.3–30.7 arcmin", "N/A (ergonomic optical invariant)", "ORIGINAL_REQUEST.md:19-21, PROJECT.md:30, ISO 9241-303"),
        (5, "Visual Meter", "Chunky Visual Meters", "Bold 20–24px high progress track with dynamic fill and 1:2 scaling (1% = 2px)", "Value (0..100), palette color", "Filled track rect (2*V px) + dark background rect (200 - 2*V px)", "Clamps fill width to track bounds (200px max)", "ORIGINAL_REQUEST.md:22-28, PROJECT.md:31"),
        (6, "Palette", "Dynamic CPU Palette", "Electric Cyan (#00D2D3) transitioning to Alert Coral (#FF6B6B)", "CPU load percentage (0..100%)", "Color RGB triplet: <60% Cyan, 60-84% Amber, >=85% Coral", "Clamps to Alert Coral for any value >= 85%", "ORIGINAL_REQUEST.md:24, PROJECT.md:32"),
        (7, "Palette", "Dynamic GPU Palette", "Neon Green (#10AC84) transitioning to Warning Orange (#FF9F43) and Blaze Red (#FF3838)", "GPU load percentage (0..100%)", "Color RGB triplet: <65% Green, 65-84% Orange, >=85% Red", "Clamps to Blaze Red for any value >= 85%", "ORIGINAL_REQUEST.md:25, PROJECT.md:33"),
        (8, "Palette", "Dynamic RAM Palette", "Vivid Violet (#A55EEA) transitioning to Danger Red (#EA2027)", "RAM usage percentage (0..100%)", "Color RGB triplet: <70% Violet, 70-84% Magenta Rose, >=85% Danger Red", "Clamps to Danger Red for any value >= 85%", "ORIGINAL_REQUEST.md:26, PROJECT.md:34"),
        (9, "Palette", "Dynamic Thermal Palette", "Cool Mint (<60°C) -> Gold (60–75°C) -> Crimson (>75°C)", "Temperature in °C (0..255)", "Color RGB triplet: <60 Mint (#1DD1A1), 60-75 Gold (#FECA57), >75 Crimson (#FF3838)", "Crimson for any temperature > 75°C", "ORIGINAL_REQUEST.md:27, PROJECT.md:35"),
        (10, "Thermals", "Dual Temp & Peak Highlight", "Simultaneous CPU & GPU temp display in Q4 with high-contrast [PEAK] highlight and border warning", "cpu_temp_c, gpu_temp_c", "Dual readouts with [PEAK] badge on max(CPU, GPU); Crimson border if peak > 75°C", "Defaults to CPU highlight or dual highlight if temperatures equal", "ORIGINAL_REQUEST.md:17, 40, PROJECT.md:36"),
        (11, "Redraw", "Differential Redraw Engine", "Dirty bounding-box updates for numerals and meter deltas over 8MHz SPI", "last_packet, new_packet", "Targeted SPI window commands (0x2A, 0x2B, 0x2C) for dirty rects only", "0 SPI transactions emitted if consecutive packets are identical", "ORIGINAL_REQUEST.md:29-31, PROJECT.md:37"),
        (12, "Redraw", "Zero-Flicker Execution", "Eradicate full-screen clears during telemetry update loop; total SPI time < 50ms", "Telemetry update tick", "Continuous stable display without strobe, wipe, or flicker artifacts", "N/A (runtime loop never invokes display.clear())", "ORIGINAL_REQUEST.md:29-31, 46, PROJECT.md:38"),
        (13, "Architecture", "Zero-Heap Execution", "#![no_std] execution with zero dynamic memory allocation across embedded modules", "Embedded runtime execution", "Stack-allocated and static memory footprint only; zero malloc/alloc calls", "Build failure / link error if dynamic allocator referenced", "ORIGINAL_REQUEST.md:29, PROJECT.md:39"),
        (14, "Memory", "Static SRAM Ceiling (<=100B)", "Constrain static RAM (.data + .bss) to <= 100 bytes on ATmega328P", "Compiled ELF artifact", "Binary .data + .bss section size reported by avr-size", "Build gate failure if .data + .bss > 100 bytes", "ORIGINAL_REQUEST.md:43, PROJECT.md:40"),
        (15, "Memory", "Flash Ceiling (<28KB)", "Constrain compiled AVR binary size (.text + .data) to < 28 KB (28,672 bytes)", "Compiled ELF artifact", "Binary .text + .data section size reported by avr-size", "Build gate failure if Flash size >= 28,672 bytes", "ORIGINAL_REQUEST.md:43, PROJECT.md:41"),
        (16, "Protocol", "Serial Packet Protocol", "Fixed 8-byte frame (0xAA 0x55 + 6 metrics) with non-blocking sliding window sync", "Serial UART byte stream at 57,600 baud", "Decoded TelemetryPacket struct (6 metric fields) + UART ACK", "Resets receive index on invalid magic byte; recovers sync on next valid header", "ORIGINAL_REQUEST.md:33, PROJECT.md:42, gadget-common"),
        (17, "Telemetry", "Host Hardware Telemetry", "Linux host daemon sampling procfs, AMD k10temp/Intel coretemp, and nvidia-smi/amdgpu sysfs", "Linux kernel APIs (/proc/stat, /proc/meminfo, /sys/class/hwmon)", "8-byte serialized frames transmitted over serial or printed in dry-run", "Falls back gracefully to sensible defaults on missing sensor hardware", "ORIGINAL_REQUEST.md:33, PROJECT.md:43, gadget-host")
    ]

def get_edge_cases():
    return [
        (1, "Numeric Formatting", "Value = 100% (3 digits)", "Numeral width expands to 3 digits (72–90px). Bounding box must accommodate 3 digits + suffix without overflowing card border."),
        (2, "Numeric Formatting", "Value = 0% (1 digit)", "Preceding digit columns must be cleanly cleared with PANEL_BG to avoid leaving visual ghost digits from prior 100% reading."),
        (3, "Thermal Equality", "cpu_temp_c == gpu_temp_c (e.g. 72°C == 72°C)", "Peak tie-breaking logic highlights CPU by default or highlights both without oscillating or flickering."),
        (4, "Thermal Overheat", "Temperature > 99°C (e.g. 105°C or 115°C)", "Formatting handles 3 digits or clamps to 99°C with flashing Crimson warning border without crashing or buffer overflow."),
        (5, "Host Disconnect", "Serial cable unplugged / no packets for 3 seconds", "Gadget retains last valid telemetry or renders subtle OFFLINE/WAITING indicator in header without blanking display."),
        (6, "Packet Noise", "Corrupted byte stream on UART (bit flips in header)", "Sliding window receiver rejects invalid magic header (!= 0xAA 0x55) and resynchronizes on next valid packet start."),
        (7, "Zero Telemetry Delta", "Consecutive identical packets received", "Differential redraw engine detects equality and emits 0 SPI transactions, preserving 0% bus load."),
        (8, "Rapid Oscillations", "Metric swinging 0% <-> 100% every 200ms", "Differential bar redraw fills full width without visual tearing; bounding box clearing completely overwrites previous state."),
        (9, "Scale 5 Font Bounds", "Character height is 35px, width is 25px", "Vertical layout ensures 35px numeral does not overlap card header (Y=24) or chunky meter track (Y=70)."),
        (10, "SPI Saturation", "All 4 metrics changing simultaneously in one tick", "Total SPI transfer is ~35,000 bytes; transfer completes in < 45 ms, well within 1000ms update window."),
        (11, "Over-Range Load", "Telemetry packet receives cpu_percent = 255", "Decoder or firmware clamps value to 100%; bar does not exceed 200px track; numeral renders 100% cleanly."),
        (12, "Sensor Shadowing", "acpitz ambient sensor (20°C) visited before k10temp (82°C)", "Host sensor collector applies strict driver priority, ensuring dedicated silicon temperature is reported."),
        (13, "Missing Serial Port", "/dev/ttyUSB0 does not exist on Arduino Uno (uses /dev/ttyACM0)", "Host daemon automatically falls back to /dev/ttyACM0 before falling back to dry-run console mode."),
        (14, "Zero CPU Ticks", "Host suspended or no CPU tick advance (delta_total == 0)", "CpuSampler detects delta_total == 0, returns 0% or previous sample, preventing division-by-zero NaN panic."),
        (15, "Thermal Spike", "Temperature leaps across thresholds (45°C -> 65°C -> 85°C)", "Palette transitions smoothly Mint -> Gold -> Crimson; card border turns Crimson at 85°C without full redraw.")
    ]

print("Specification helper modules defined.")
