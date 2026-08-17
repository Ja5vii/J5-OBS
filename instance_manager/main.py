import os
import sys
import json
import asyncio
import signal
import hashlib

import aiohttp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from instance_manager.config import ManagerConfig
from instance_manager.database import Database
from instance_manager.port_manager import PortManager
from instance_manager.display_manager import DisplayManager
from instance_manager.process_manager import ProcessManager
from instance_manager.health_manager import HealthManager
from instance_manager.recovery_manager import RecoveryManager
from instance_manager.logger import Logger
from instance_manager.api import create_api_app


class InstanceManager:
    __slots__ = ("base_dir", "config", "logger", "db", "port_manager", "display_manager", "process_manager", "health_manager", "recovery_manager", "_running", "_templates")

    def __init__(self):
        self.base_dir = os.environ.get("CONTAINER_DIR", "/home/container")
        self.config = ManagerConfig(self.base_dir)
        self.logger = Logger(self.base_dir, self.config.get()["logging"])
        self.db = Database(self.base_dir)
        self.port_manager = PortManager(self.config)
        self.display_manager = DisplayManager(self.config)
        self.process_manager = ProcessManager(self, self.config, self.logger)
        self.health_manager = HealthManager(self, self.config, self.logger)
        self.recovery_manager = RecoveryManager(self, self.config, self.logger)
        self._running = False
        self._templates = None

    async def start(self):
        self._running = True
        self.logger.info("J5 OBS Instance Manager starting...")
        await self.db.initialize()
        await self.port_manager.initialize()
        await self.display_manager.initialize()
        self.process_manager.initialize()
        self.health_manager.start()
        self.recovery_manager.start()
        self.logger.info("Instance Manager ready")

    async def stop(self):
        self.logger.info("Shutting down...")
        self._running = False
        self.health_manager.stop()
        self.recovery_manager.stop()
        instances = await self.db.get_all_instances()
        for inst in instances:
            if inst["status"] in ("ONLINE", "STREAMING", "STARTING"):
                await self.process_manager.stop_instance(inst["instance_id"])
        await self.db.close()
        self.logger.info("Shutdown complete")

    def _load_templates(self):
        if self._templates is not None:
            return self._templates
        tdir = os.path.join(self.base_dir, "instance_manager", "templates")
        self._templates = {}
        if os.path.isdir(tdir):
            for f in os.listdir(tdir):
                if f.endswith(".json"):
                    with open(os.path.join(tdir, f)) as fh:
                        t = json.load(fh)
                        self._templates[t["name"]] = t
        return self._templates

    def _apply_template(self, template_name):
        if not template_name:
            return "", "Main"
        templates = self._load_templates()
        tmpl = templates.get(template_name)
        if not tmpl:
            raise ValueError(f"Template '{template_name}' not found")
        profile = tmpl.get("name", "default")
        scenes = tmpl.get("scenes", [])
        scene_col = scenes[0]["name"] if scenes else "Main"
        return profile, scene_col

    async def create_instance(self, name, template=None, owner_id=None):
        config = self.config.get()
        instances = await self.db.get_all_instances()
        active_ids = {i["instance_id"] for i in instances}
        next_num = 1
        while f"obs-{next_num:03d}" in active_ids:
            next_num += 1
            if next_num > config["resources"]["max_instances"]:
                raise RuntimeError("Maximum instances reached")
        instance_id = f"obs-{next_num:03d}"
        ws_port = self.port_manager.allocate(instance_id)
        display = self.display_manager.allocate(instance_id)
        profile, scene_col = self._apply_template(template)
        ws_password = hashlib.sha256(instance_id.encode()).hexdigest()[:16]
        await self.db.create_instance(
            instance_id=instance_id, name=name, owner_id=owner_id,
            display=display, websocket_port=ws_port,
            profile=profile, scene_collection=scene_col, ws_password=ws_password,
        )
        self.logger.info(f"Created {instance_id} (display={display}, ws={ws_port})")
        return await self.db.get_instance(instance_id)

    async def delete_instance(self, instance_id):
        inst = await self.db.get_instance(instance_id)
        if not inst:
            raise ValueError(f"{instance_id} not found")
        if inst["status"] in ("ONLINE", "STREAMING", "STARTING"):
            await self.process_manager.stop_instance(instance_id)
        self.port_manager.release(instance_id)
        self.display_manager.release(instance_id)
        await self.db.delete_instance(instance_id)
        import shutil
        inst_dir = os.path.join(self.base_dir, "instances", instance_id)
        if os.path.exists(inst_dir):
            shutil.rmtree(inst_dir)
        self.logger.info(f"Deleted {instance_id}")

    async def start_instance(self, instance_id):
        inst = await self.db.get_instance(instance_id)
        if not inst:
            raise ValueError(f"{instance_id} not found")
        if inst["status"] in ("ONLINE", "STREAMING", "STARTING"):
            return inst
        await self.process_manager.start_instance(instance_id)
        return await self.db.get_instance(instance_id)

    async def stop_instance(self, instance_id):
        inst = await self.db.get_instance(instance_id)
        if not inst:
            raise ValueError(f"{instance_id} not found")
        await self.process_manager.stop_instance(instance_id)
        return await self.db.get_instance(instance_id)

    async def restart_instance(self, instance_id):
        inst = await self.db.get_instance(instance_id)
        if not inst:
            raise ValueError(f"{instance_id} not found")
        if inst["status"] in ("ONLINE", "STREAMING", "STARTING", "STOPPING"):
            await self.process_manager.stop_instance(instance_id)
        await self.process_manager.start_instance(instance_id)
        return await self.db.get_instance(instance_id)


async def run_manager():
    manager = InstanceManager()
    await manager.start()
    config = manager.config.get()
    app = create_api_app(manager)
    runner = aiohttp.web.AppRunner(app, access_log=None)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, config["manager"]["host"], config["manager"]["port"])
    await site.start()
    manager.logger.info(f"API on {config['manager']['host']}:{config['manager']['port']}")
    stop_event = asyncio.Event()
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()
    await manager.stop()
    await runner.cleanup()


def main():
    if "--init-only" in sys.argv:
        base = os.environ.get("CONTAINER_DIR", "/home/container")
        import asyncio as _aio
        db = Database(base)
        _aio.run(db.initialize())
        _aio.run(db.close())
        return
    asyncio.run(run_manager())


if __name__ == "__main__":
    main()
