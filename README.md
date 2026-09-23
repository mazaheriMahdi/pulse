# Desktop Performance Monitor (Rust + Arduino Uno + ILI9488)

A high-performance hardware monitor desktop gadget built in 100% Rust that connects to your laptop via USB Serial and displays real-time CPU, GPU, RAM, Temperatures, and Battery on a 3.5" TFT display (480x320).

---

## 🔌 Hardware Wiring Diagram

Connect the **3.5" TFT SPI Display (ILI9488 / MSP3520)** to the **Arduino Uno** as follows:

| Display Pin | Arduino Uno Pin | Purpose |
|-------------|-----------------|---------|
| **VCC**     | `5V` (or `3.3V`)| Power Supply |
| **GND**     | `GND`           | Ground |
| **SDI (MOSI)**| **Pin 11**    | Hardware SPI Data |
| **SCK (CLK)** | **Pin 13**    | Hardware SPI Clock |
| **SDO (MISO)**| **Pin 12**    | Hardware SPI MISO (Optional) |
| **CS**      | **Pin 10**      | Chip Select |
| **DC / RS** | **Pin 9**       | Data / Command Selection |
| **RESET**   | **Pin 8**       | Hardware Reset |
| **LED**     | `3.3V`          | Backlight (Always ON) |

---

## 📊 Dashboard Gauges & Telemetry

The 480×320 screen is laid out in two cards with differential rendering:
- **Left Panel [ CPU & Memory ]**:
  - **CPU LOAD**: Real-time Linux kernel `/proc/stat` delta percentage (`0–100%`).
  - **CPU TEMP**: Direct hwmon `k10temp` reading in °C.
  - **RAM USAGE**: Precise memory usage from `/proc/meminfo` (`0–100%`).
  - **BATTERY**: Power level from `/sys/class/power_supply` (`0–100%`).
- **Right Panel [ GPU & Thermal ]**:
  - **GPU LOAD**: Dedicated NVIDIA GPU utilization queried via `nvidia-smi` (`0–100%`).
  - **GPU TEMP**: Dedicated NVIDIA GPU core temperature in °C.
  - **HARDWARE & STATUS**: Real-time thermal status badge (Cool / High / Critical Hot).

---

## 🚀 How to Run

### 1. Re-flashing the Arduino Uno Firmware (if modified)
```bash
cd software/gadget-firmware-uno
cargo +nightly run
```

### 2. Launch the Laptop Host Daemon
In your terminal, run:
```bash
cd software/gadget-host
cargo run -- --port /dev/ttyUSB0 --baud 57600
```
To test without serial hardware:
```bash
cargo run -- --dry-run
```
