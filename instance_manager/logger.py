import os
import logging
from logging.handlers import RotatingFileHandler


class Logger:
    _init = False

    def __init__(self, base_dir, config):
        self._logger = logging.getLogger("j5-obs")
        if not Logger._init and not self._logger.handlers:
            Logger._init = True
            self._logger.setLevel(getattr(logging, config.get("level", "INFO").upper(), logging.INFO))
            fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
            log_dir = os.path.join(base_dir, "j5-obs", "logs")
            os.makedirs(log_dir, exist_ok=True)
            fh = RotatingFileHandler(os.path.join(log_dir, "manager.log"), maxBytes=config.get("max_bytes", 5242880), backupCount=config.get("backup_count", 3))
            fh.setFormatter(fmt)
            self._logger.addHandler(fh)
            sh = logging.StreamHandler()
            sh.setFormatter(fmt)
            self._logger.addHandler(sh)

    def info(self, m): self._logger.info(m)
    def warning(self, m): self._logger.warning(m)
    def error(self, m): self._logger.error(m)
    def debug(self, m): self._logger.debug(m)
