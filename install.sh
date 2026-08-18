#!/bin/bash
set -e

INSTALL_DIR="/home/container"
MANAGER_DIR="${INSTALL_DIR}/instance-manager"
CONFIG_DIR="${INSTALL_DIR}/j5-obs/config"
DATABASE_DIR="${INSTALL_DIR}/j5-obs/database"
LOG_DIR="${INSTALL_DIR}/j5-obs/logs"

mkdir -p "${INSTALL_DIR}/instances" "${CONFIG_DIR}" "${DATABASE_DIR}" "${LOG_DIR}"

if [ ! -f "${CONFIG_DIR}/config.json" ]; then
    cat > "${CONFIG_DIR}/config.json" << 'DEFAULTCONFIG'
{
  "manager": {"host": "0.0.0.0", "port": 8080, "token": "", "log_level": "INFO"},
  "ports": {"websocket_base": 4455, "rtmp_base": 1935},
  "displays": {"base": 100, "resolution": "1280x720", "depth": 24},
  "resources": {"max_instances": 10, "auto_start": false},
  "recovery": {"auto_restart": true, "max_restarts": 3, "restart_delay": 10, "health_check_interval": 15},
  "security": {"rate_limit_per_minute": 120},
  "logging": {"level": "INFO", "max_bytes": 5242880, "backup_count": 3}
}
DEFAULTCONFIG
fi

python3 -O "${MANAGER_DIR}/main.py" --init-only 2>/dev/null || true
echo "Installation complete."
