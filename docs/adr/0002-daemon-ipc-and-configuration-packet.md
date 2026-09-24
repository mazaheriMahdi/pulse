# 2. Daemon-Client IPC Architecture and Dual-Magic Configuration Protocol

Date: 2026-09-24

## Context
The PULSE Studio desktop companion app allows end-users to select faces, customize accent colors, adjust display toggles, preview metrics in real time, and configure the gadget. On Linux, serial ports (e.g. `/dev/ttyUSB1`) enforce exclusive access: having both the background telemetry daemon (`gadget-host`) and the graphical studio (`pulse-studio`) attempt to open the serial port directly results in `EADDRINUSE` / device busy errors. Furthermore, flashing the ATmega328P flash memory on every configuration change introduces 5-8 second delays and flash wear.

## Decision
1. **Client-Daemon IPC Architecture**:
   - `gadget-host` remains the exclusive owner of the physical serial port and acts as an IPC server over a Unix domain socket (`/tmp/pulse-studio.sock`).
   - `pulse-studio` acts as a Tauri desktop GUI client connecting to this socket to receive real-time telemetry packets for its live preview and to send configuration requests.
   - If the daemon is not running when PULSE Studio launches, Studio spawns it automatically.

2. **Dual-Magic 8-Byte Packet Protocol**:
   - `TelemetryPacket` uses header `[0xAA, 0x55]` followed by 6 metric bytes.
   - `ConfigurationPacket` uses inverted header `[0x55, 0xAA]` followed by `face_id`, `accent_color_id`, `brightness`, `refresh_hz`, and bitfield `flags`.
   - Both packets share the exact same 8-byte length, allowing the AVR firmware's stream parser to process both without buffer reallocation or state desync.
   - Configuration is applied immediately in-memory and saved to ATmega328P internal EEPROM so it persists across power cycles.

## Consequences
- Zero serial contention on host system; seamless transitions when opening or closing PULSE Studio.
- Instant (<50ms) face and color switching without resetting the MCU or interrupting the telemetry stream.
- Zero extra memory footprint on the ATmega328P (retaining the 2KB SRAM budget).
