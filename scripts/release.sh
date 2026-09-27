#!/usr/bin/env bash
set -e

# ==============================================================================
# PULSE STUDIO — Version Bump & Tag Release Script
# ==============================================================================

if [ -z "$1" ]; then
    echo "Usage: $0 <version> (e.g. 0.1.0 or v0.1.0)"
    exit 1
fi

RAW_VER="${1#v}"
TAG_VER="v${RAW_VER}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "  Bumping version to ${TAG_VER}           "
echo "=========================================="

# 1. Update Cargo.toml versions
echo "[1/4] Updating Cargo.toml files..."
sed -i "s/^version = \".*\"/version = \"${RAW_VER}\"/" "${ROOT_DIR}/software/gadget-common/Cargo.toml"
sed -i "s/^version = \".*\"/version = \"${RAW_VER}\"/" "${ROOT_DIR}/software/gadget-core/Cargo.toml"
sed -i "s/^version = \".*\"/version = \"${RAW_VER}\"/" "${ROOT_DIR}/software/gadget-firmware-uno/Cargo.toml"
sed -i "s/^version = \".*\"/version = \"${RAW_VER}\"/" "${ROOT_DIR}/software/gadget-host/Cargo.toml"
sed -i "s/^version = \".*\"/version = \"${RAW_VER}\"/" "${ROOT_DIR}/software/pulse-studio/src-tauri/Cargo.toml"

# 2. Update tauri.conf.json
echo "[2/4] Updating tauri.conf.json..."
sed -i "s/\"version\": \".*\"/\"version\": \"${RAW_VER}\"/" "${ROOT_DIR}/software/pulse-studio/src-tauri/tauri.conf.json"

# 3. Commit version bump
echo "[3/4] Committing version bump..."
git add "${ROOT_DIR}/software/*/Cargo.toml" "${ROOT_DIR}/software/pulse-studio/src-tauri/tauri.conf.json"
git commit -m "chore(release): bump version to ${TAG_VER}" || echo "No changes to commit"

# 4. Create and push tag
echo "[4/4] Creating tag ${TAG_VER} and pushing to GitHub..."
git tag -a "${TAG_VER}" -m "Release ${TAG_VER}"
git push origin master
git push origin "${TAG_VER}"

echo "=========================================="
echo "  TAG ${TAG_VER} PUSHED!                  "
echo "  GitHub Actions release pipeline is now running: "
echo "  https://github.com/mazaheriMahdi/pulse/actions"
echo "=========================================="
