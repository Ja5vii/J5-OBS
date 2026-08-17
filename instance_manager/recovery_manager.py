import asyncio


class RecoveryManager:
    def __init__(self, manager, config, logger):
        self.manager = manager
        self.config = config
        self.logger = logger
        self._pending = {}
        self._task = None
        self._stop_event = asyncio.Event()

    def start(self):
        self._stop_event.clear()
        self._task = asyncio.ensure_future(self._run())

    def stop(self):
        self._stop_event.set()
        if self._task:
            self._task.cancel()

    def handle_crash(self, instance_id):
        cfg = self.config.get()
        if not cfg["recovery"]["auto_restart"]:
            return
        self._pending[instance_id] = {
            "attempts": 0,
            "max": cfg["recovery"]["max_restarts"],
            "delay": cfg["recovery"]["restart_delay"],
        }
        self.logger.info(f"Crash recovery queued for {instance_id}")

    async def _run(self):
        while not self._stop_event.is_set():
            to_remove = []
            for instance_id, info in list(self._pending.items()):
                if info["attempts"] >= info["max"]:
                    self.logger.error(f"Instance {instance_id} exceeded max restarts ({info['max']})")
                    to_remove.append(instance_id)
                    continue
                inst = await self.manager.db.get_instance(instance_id)
                if not inst or inst["status"] not in ("CRASHED", "STANDBY"):
                    to_remove.append(instance_id)
                    continue
                info["attempts"] += 1
                self.logger.info(f"Recovery attempt {info['attempts']}/{info['max']} for {instance_id} in {info['delay']}s...")
                await asyncio.sleep(info["delay"])
                try:
                    await self.manager.start_instance(instance_id)
                    self.logger.info(f"Instance {instance_id} recovered successfully")
                    to_remove.append(instance_id)
                except Exception as e:
                    self.logger.error(f"Recovery failed for {instance_id}: {e}")
            for iid in to_remove:
                self._pending.pop(iid, None)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=5)
            except asyncio.TimeoutError:
                pass
