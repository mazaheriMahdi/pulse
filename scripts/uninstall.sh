#!/usr/bin/env bash
set -e

# ==============================================================================
# PULSE STUDIO — Uninstaller Script for Linux
# Removes PULSE Studio binaries, desktop launchers, and icons
# ==============================================================================

BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_BASE="${HOME}/.local/share/icons/hicolor"

echo "=========================================="
echo "  UNINSTALLING PULSE STUDIO               "
echo "=========================================="

# 1. Remove binaries
echo "Removing binaries..."
rm -f "${BIN_DIR}/pulse-studio"
rm -f "${BIN_DIR}/gadget-host"

# 2. Remove desktop entry
echo "Removing desktop launcher..."
rm -f "${DESKTOP_DIR}/pulse-studio.desktop"

# 3. Remove icons
echo "Removing icons..."
for size in 32x32 48x48 64x64 128x128 256x256 512x512; do
    rm -f "${ICON_BASE}/${size}/apps/pulse-studio.png"
done
rm -f "${ICON_BASE}/scalable/apps/pulse-studio.svg"

# Refresh desktop & icon databases
update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
gtk-update-icon-cache -f -t "${ICON_BASE}" 2>/dev/null || true

echo "=========================================="
echo "  PULSE STUDIO UNINSTALLED SUCCESSFULLY   "
echo "=========================================="
