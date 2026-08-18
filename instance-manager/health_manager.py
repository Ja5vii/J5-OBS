import asyncio
import time
import psutil


class HealthManager:
    __slots__ = ("manager", "config", "logger", "_task", "_stop")

    def __init__(self, manager, config, logger):
        self.manager = manager
        self.config = config
        self.logger = logger
        self._task = None
        self._stop = asyncio.Event()

    def start(self):
        self._stop.clear()
        self._task = asyncio.ensure_future(self._run())

    def stop(self):
        self._stop.set()
        if self._task:
            self._task.cancel()

    async def _run(self):
        interval = self.config.get()["recovery"]["health_check_interval"]
        while not self._stop.is_set():
            try:
                await self._check_all()
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    async def _check_all(self):
        instances = await self.manager.db.get_all_instances()
        for inst in instances:
            iid = inst["instance_id"]
            if inst["status"] in ("ONLINE", "STREAMING") and not self.manager.process_manager.is_running(iid):
                self.logger.warning(f"{iid} process died (was {inst['status']})")
                await self.manager.db.update_instance(iid, status="CRASHED", pid=None)
                self.manager.recovery_manager.handle_crash(iid)

    async def get_stats(self, instance_id):
        inst = await self.manager.db.get_instance(instance_id)
        if not inst:
            return None
        s = {
            "instance_id": instance_id,
            "status": inst["status"],
            "pid": inst["pid"],
            "display": inst["display"],
            "websocket_port": inst["websocket_port"],
            "rtmp_url": inst.get("rtmp_url", ""),
            "cpu_percent": 0.0,
            "ram_mb": 0,
            "uptime_seconds": 0,
        }
        pid = inst["pid"]
        if pid and self.manager.process_manager.is_running(instance_id):
            try:
                p = psutil.Process(pid)
                s["cpu_percent"] = p.cpu_percent(interval=0.05)
                s["ram_mb"] = round(p.memory_info().rss / 1048576, 1)
                s["uptime_seconds"] = int(time.time() - p.create_time())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return s
