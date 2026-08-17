#!/bin/bash
echo "=== J5 OBS Shutdown ==="

INSTALL_DIR="/home/container"
PID_FILE="${INSTALL_DIR}/j5-obs/manager.pid"

if [ -f "${PID_FILE}" ]; then
    MANAGER_PID=$(cat "${PID_FILE}")
    if kill -0 "${MANAGER_PID}" 2>/dev/null; then
        kill -TERM "${MANAGER_PID}"
        WAIT=0
        while kill -0 "${MANAGER_PID}" 2>/dev/null && [ "${WAIT}" -lt 15 ]; do
            sleep 0.5
            WAIT=$((WAIT + 1))
        done
        kill -9 "${MANAGER_PID}" 2>/dev/null || true
    fi
    rm -f "${PID_FILE}"
fi

pkill -9 -f "obs --multiplatform" 2>/dev/null || true
pkill -9 -f "Xvfb" 2>/dev/null || true
wait 2>/dev/null || true
