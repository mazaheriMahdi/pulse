## 2026-09-22T18:32:01Z

You are UI UX Spec Miner (spec_miner_survey_3).
Your working directory is: /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_survey_3
Workspace root: /home/mahdi/Programming/perfomance-monitor

Authoritative User Request:
Read /home/mahdi/Programming/perfomance-monitor/.agents/ORIGINAL_REQUEST.md first before doing anything else.

Objective:
Extract and document the comprehensive specifications for the 4-Quadrant Big Block UI/UX:
1. Quadrant layout specs: 480x320 landscape display, 4 distinct quadrants (approx 230x145 px each) with stylish border cards.
   - Q1: CPU Load (%)
   - Q2: GPU Load (%)
   - Q3: RAM Usage (%)
   - Q4: Thermals (CPU Temp & GPU Temp in °C with peak highlight)
2. Typography specs: >= 28–36px tall numerals (scale 4–5 font or bespoke 7-segment / chunky glyphs), arm's-length legibility (60–90cm / 70+cm), zero tiny text on primary readings.
3. Meter & visual specs: chunky visual meters (segmented bar, bold progress track, or color-shifting bar), color palettes:
   - CPU: Electric Cyan (#00D2D3) -> Alert Coral
   - GPU: Neon Green (#10AC84 / #05C46B) -> Warning Orange
   - RAM: Vivid Violet (#A55EEA) -> Danger Red
   - Thermals: Cool Blue/Mint (<60°C) -> Gold (60–75°C) -> Crimson (>75°C)
4. Efficiency & Performance specs: differential redraw bounding boxes, zero-heap, 2KB SRAM ceiling, 8MHz SPI, 28KB Flash, 100B static SRAM.
5. Derive an exhaustive requirement matrix and verification checklist for E2E testing and implementation.

Rules:
- Strictly read-only. Do not modify source code.
- Write your comprehensive specification report to /home/mahdi/Programming/perfomance-monitor/.agents/spec_miner_survey_3/handoff.md.
- Notify orchestrator when done via send_message.
