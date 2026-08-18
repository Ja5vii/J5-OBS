#!/bin/bash
set -e

INSTALL_DIR="/home/container"
MANAGER_DIR="${INSTALL_DIR}/instance-manager"
PID_FILE="${INSTALL_DIR}/j5-obs/manager.pid"
LOG_DIR="${INSTALL_DIR}/j5-obs/logs"

mkdir -p "${LOG_DIR}" "${INSTALL_DIR}/instances" "${INSTALL_DIR}/j5-obs/config" "${INSTALL_DIR}/j5-obs/database" "${INSTALL_DIR}/j5-obs/branding_assets"

# Auto-update from GitHub
echo "Checking for updates from GitHub..."
if [ -d "${INSTALL_DIR}/.git" ]; then
    git fetch origin main || true
    git reset --hard origin/main || true
fi

echo "$$" > "${PID_FILE}"

if command -v pulseaudio >/dev/null 2>&1; then
    pulseaudio --kill 2>/dev/null || true
fi

exec python3 -O "${MANAGER_DIR}/main.py"
