# 1. Portability via embedded-hal for MCU Agnosticism

Date: 2026-09-22

## Context
The prototype is being constructed on an Arduino Uno (ATmega328P, AVR, 16MHz, 2KB SRAM) for immediate physical validation, while the intended production platform is an ESP32 (Xtensa/RISC-V, 240MHz, 512KB SRAM, WiFi/BLE).

## Decision
All display driver communication, drawing primitives, and UI rendering logic will be written against standard `embedded-hal` and `embedded-graphics` traits in a platform-agnostic `gadget-core` / `ili9488-rs` layer. Microcontroller-specific crates (`firmware-uno` and eventually `firmware-esp32`) will only act as thin entrypoints that initialize board peripherals (SPI, GPIO, UART) and pass them into the shared engine.

## Consequences
- The display driving and pet animation code can be switched between Uno and ESP32 with zero rewrites to the rendering logic.
- Firmware code must adhere to strict `no_std` zero-allocation guidelines to run comfortably within the Uno's 2KB SRAM ceiling while scaling up to the ESP32.
