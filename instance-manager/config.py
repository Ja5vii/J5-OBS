import os
import json


DEFAULT_CONFIG = {
    "manager": {"host": "0.0.0.0", "port": 8080, "token": "", "log_level": "INFO"},
    "ports": {"websocket_base": 4455, "rtmp_base": 1935},
    "displays": {"base": 100, "resolution": "1280x720", "depth": 24},
    "resources": {"max_instances": 10, "auto_start": False},
    "recovery": {"auto_restart": True, "max_restarts": 3, "restart_delay": 10, "health_check_interval": 15},
    "security": {"rate_limit_per_minute": 120},
    "logging": {"level": "INFO", "max_bytes": 5242880, "backup_count": 3},
}


class ManagerConfig:
    __slots__ = ("base_dir", "config_path", "_config")

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.config_path = os.path.join(base_dir, "j5-obs", "config", "config.json")
        self._config = None

    def get(self):
        if self._config is not None:
            return self._config
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                user = json.load(f)
            self._config = self._deep_merge(DEFAULT_CONFIG, user)
        else:
            self._config = dict(DEFAULT_CONFIG)
        self._apply_env()
        return self._config

    def _deep_merge(self, base, override):
        r = dict(base)
        for k, v in override.items():
            if k in r and isinstance(r[k], dict) and isinstance(v, dict):
                r[k] = self._deep_merge(r[k], v)
            else:
                r[k] = v
        return r

    def _apply_env(self):
        env = {
            "J5_MANAGER_PORT": ("manager", "port", int),
            "J5_MANAGER_TOKEN": ("manager", "token", str),
            "OBS_WEBSOCKET_BASE_PORT": ("ports", "websocket_base", int),
            "OBS_DISPLAY_BASE": ("displays", "base", int),
            "OBS_MAX_INSTANCES": ("resources", "max_instances", int),
            "AUTO_RESTART": ("recovery", "auto_restart", lambda v: v.lower() in ("true", "1")),
            "MAX_RESTARTS": ("recovery", "max_restarts", int),
            "RESTART_DELAY": ("recovery", "restart_delay", int),
            "AUTO_START_INSTANCES": ("resources", "auto_start", lambda v: v.lower() in ("true", "1")),
        }
        for ek, (s, k, c) in env.items():
            ev = os.environ.get(ek)
            if ev is not None:
                try:
                    self._config[s][k] = c(ev)
                except (ValueError, TypeError):
                    pass
