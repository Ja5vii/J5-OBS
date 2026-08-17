#!/bin/bash
set -e

INSTALL_DIR="/home/container"
MANAGER_DIR="${INSTALL_DIR}/instance_manager"
PID_FILE="${INSTALL_DIR}/j5-obs/manager.pid"
LOG_DIR="${INSTALL_DIR}/j5-obs/logs"

mkdir -p "${LOG_DIR}" "${INSTALL_DIR}/instances" "${INSTALL_DIR}/j5-obs/config" "${INSTALL_DIR}/j5-obs/database"

echo "$$" > "${PID_FILE}"

if command -v pulseaudio >/dev/null 2>&1; then
    pulseaudio --kill 2>/dev/null || true
fi

exec python3 -O "${MANAGER_DIR}/main.py"
