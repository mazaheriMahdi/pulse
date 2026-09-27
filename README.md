# PULSE — Desktop Hardware Monitor & Studio

[![CI Build & Test](https://github.com/mazaheriMahdi/pulse/actions/workflows/ci.yml/badge.svg)](https://github.com/mazaheriMahdi/pulse/actions/workflows/ci.yml)
[![GitHub Pages](https://github.com/mazaheriMahdi/pulse/actions/workflows/pages.yml/badge.svg)](https://mazaheriMahdi.github.io/pulse/)
[![Release Pipeline](https://github.com/mazaheriMahdi/pulse/actions/workflows/release.yml/badge.svg)](https://github.com/mazaheriMahdi/pulse/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

An ultra-refined desktop telemetry monitor and control studio built in **100% Rust** for microcontrollers (AVR / Arduino Uno + 3.5" IPS display) and Linux desktops, following the **Nothing (R) OS × Teenage Engineering** dot-matrix hardware design language.

🌐 **Live Web Studio / Previewer**: [https://mazaheriMahdi.github.io/pulse/](https://mazaheriMahdi.github.io/pulse/)

---

## 📸 Face Library

| Face | Description | Display Elements |
|------|-------------|------------------|
| **DUAL LOAD** | Dual CPU + GPU split load gauges | Giant 5×7 dot numerals, dual dot progress bars, thermal readouts |
| **CPU GRID** | Pure CPU performance diagnostics | $10 \times 10$ LED matrix load visualizer, frequency and core metrics |
| **GPU GRID** | Dedicated GPU compute & VRAM monitor | Real-time NVIDIA core load, memory saturation, temperature blip |
| **MEMORY** | RAM & Swap utilization breakdown | Active / Cached breakdown, dot segmented level gauges |
| **THERMAL** | Multi-zone temperature matrix | CPU & GPU heat sensors with dynamic hot indicators |
| **MINIMAL** | High-contrast ultra-minimalist single metric | Focused typography with compact status pill |
| **NETWORK** | Real-time upstream / downstream throughput | Dual channel MB/s meters, peak indicators, interface badge |

---

## ⚡ Quick Install (Linux)

### Option 1: Automatic Installer
Clone the repository and run the installer:
```bash
git clone https://github.com/mazaheriMahdi/pulse.git
cd pulse
./scripts/install.sh
```
This builds and installs:
- `pulse-studio` GUI to `~/.local/bin/pulse-studio`
- `gadget-host` daemon to `~/.local/bin/gadget-host`
- FreeDesktop `.desktop` launcher & Nothing dot-matrix icons to system menus.

### Option 2: Pre-compiled GitHub Releases
Download the latest `pulse-studio-linux-x86_64.tar.gz` from [Releases](https://github.com/mazaheriMahdi/pulse/releases), extract, and run `./scripts/install.sh`.

---

## 🔌 Hardware Wiring Diagram

Connect the **3.5" TFT SPI Display (ILI9488 / MSP3520)** to the **Arduino Uno**:

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

## 🛠️ Architecture & Crates

```
pulse/
├── software/
│   ├── gadget-common/       # no_std Telemetry & Configuration packet protocols
│   ├── gadget-core/         # no_std Embedded graphics & differential screen renderer
│   ├── gadget-firmware-uno/ # AVR Rust bare-metal firmware for Arduino Uno + ILI9488
│   ├── gadget-host/         # Linux background telemetry daemon (/proc, nvidia-smi, IPC)
│   └── pulse-studio/        # Tauri v2 Desktop GUI + Web simulator with Nothing dot styling
├── enclosure/               # 3D CAD models (.blend) and 3D printable STL files
├── scripts/                 # install.sh, uninstall.sh, release.sh
└── .github/workflows/       # CI/CD: Automated testing, GitHub Pages, and Releases
```

---

## 🚀 Release & Versioning

To trigger a new automated release:
```bash
./scripts/release.sh 0.1.0
```
This automatically updates versions across all `Cargo.toml` crates, updates `tauri.conf.json`, tags the release, and triggers the GitHub Actions release workflow.
