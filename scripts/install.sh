#!/usr/bin/env bash
set -e

# ==============================================================================
# PULSE STUDIO — Installer Script for Linux
# Installs PULSE Studio & Gadget Host with Nothing Dot-Matrix Icon Suite
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_BASE="${HOME}/.local/share/icons/hicolor"

echo "=========================================="
echo "  PULSE STUDIO INSTALLER (DOT-DESIGN)     "
echo "=========================================="

mkdir -p "${BIN_DIR}"
mkdir -p "${DESKTOP_DIR}"
mkdir -p "${ICON_BASE}"

# 1. Build release binaries if not found
echo "[1/4] Checking release binaries..."
if [ ! -f "${ROOT_DIR}/software/gadget-host/target/release/gadget-host" ]; then
    echo "  > Building gadget-host (release)..."
    (cd "${ROOT_DIR}/software/gadget-host" && cargo build --release)
fi

PULSE_BIN="${ROOT_DIR}/software/pulse-studio/src-tauri/target/release/pulse-studio"
if [ ! -f "${PULSE_BIN}" ]; then
    PULSE_BIN="${ROOT_DIR}/target/release/pulse-studio"
fi

if [ ! -f "${PULSE_BIN}" ]; then
    echo "  > Building pulse-studio (release)..."
    (cd "${ROOT_DIR}/software/pulse-studio/src-tauri" && cargo build --release)
    PULSE_BIN="${ROOT_DIR}/software/pulse-studio/src-tauri/target/release/pulse-studio"
    if [ ! -f "${PULSE_BIN}" ]; then
        PULSE_BIN="${ROOT_DIR}/target/release/pulse-studio"
    fi
fi

HOST_BIN="${ROOT_DIR}/software/gadget-host/target/release/gadget-host"
if [ ! -f "${HOST_BIN}" ]; then
    HOST_BIN="${ROOT_DIR}/target/release/gadget-host"
fi

# 2. Copy binaries to ~/.local/bin
echo "[2/4] Installing binaries to ${BIN_DIR}..."
cp -f "${PULSE_BIN}" "${BIN_DIR}/pulse-studio"
chmod +x "${BIN_DIR}/pulse-studio"

cp -f "${HOST_BIN}" "${BIN_DIR}/gadget-host"
chmod +x "${BIN_DIR}/gadget-host"

# 3. Install dot-matrix icons across all standard resolutions
echo "[3/4] Installing Nothing Dot-Matrix icon suite..."
ICONS_SRC="${ROOT_DIR}/software/pulse-studio/src-tauri/icons"

declare -A ICON_MAP=(
    ["32x32"]="32x32.png"
    ["48x48"]="48x48.png"
    ["64x64"]="64x64.png"
    ["128x128"]="128x128.png"
    ["256x256"]="128x128@2x.png"
    ["512x512"]="icon.png"
)

for size in "${!ICON_MAP[@]}"; do
    dest_dir="${ICON_BASE}/${size}/apps"
    mkdir -p "${dest_dir}"
    src_file="${ICONS_SRC}/${ICON_MAP[$size]}"
    if [ -f "${src_file}" ]; then
        cp -f "${src_file}" "${dest_dir}/pulse-studio.png"
    fi
done

# Scalable SVG
mkdir -p "${ICON_BASE}/scalable/apps"
if [ -f "${ICONS_SRC}/icon.svg" ]; then
    cp -f "${ICONS_SRC}/icon.svg" "${ICON_BASE}/scalable/apps/pulse-studio.svg"
fi

# 4. Install Desktop Entry
echo "[4/4] Registering Desktop Application launcher..."
cat <<DESKTOPEOF > "${DESKTOP_DIR}/pulse-studio.desktop"
[Desktop Entry]
Type=Application
Name=Pulse Studio
GenericName=Hardware Monitor & Control Studio
Comment=Nothing OS & Teenage Engineering inspired hardware monitor studio for PULSE gadget
Exec=${BIN_DIR}/pulse-studio
Icon=pulse-studio
Terminal=false
Categories=Utility;System;Monitor;HardwareSettings;
StartupNotify=true
StartupWMClass=pulse-studio
Keywords=pulse;hardware;monitor;gadget;nothing;matrix;
DESKTOPEOF

chmod +x "${DESKTOP_DIR}/pulse-studio.desktop"

# Refresh desktop & icon databases
update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
if [ ! -f "${ICON_BASE}/index.theme" ]; then cp /usr/share/icons/hicolor/index.theme "${ICON_BASE}/index.theme" 2>/dev/null || true; fi
gtk-update-icon-cache -f -t "${ICON_BASE}" 2>/dev/null || true

echo "=========================================="
echo "  INSTALLATION SUCCESSFUL!                "
echo "  Launcher: ${DESKTOP_DIR}/pulse-studio.desktop"
echo "  Binary:   ${BIN_DIR}/pulse-studio"
echo "  Icon:     ${ICON_BASE}/512x512/apps/pulse-studio.png"
echo "=========================================="
