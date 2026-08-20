import asyncio
import time
import psutil

import socket
import obsws_python as obsws
def _fetch_obs_stats(port, password):
    # Check if port is open to avoid obsws_python traceback spam
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)
        if s.connect_ex(('127.0.0.1', port)) != 0:
            return {"obs_error": "Connection refused"}
    
    import logging
    logging.getLogger("obsws_python").setLevel(logging.CRITICAL)
    
    try:
        client = obsws.ReqClient(host='127.0.0.1', port=port, password=password, timeout=1)
        stats = client.get_stats()
        stream = client.get_stream_status()
        return {
            "obs_cpu": getattr(stats, 'cpu_usage', 0),
            "obs_memory_mb": getattr(stats, 'memory_usage', 0),
            "obs_fps": getattr(stats, 'active_fps', 0),
            "obs_render_missed": getattr(stats, 'render_skipped_frames', 0),
            "obs_render_total": getattr(stats, 'render_total_frames', 0),
            "obs_output_skipped": getattr(stats, 'output_skipped_frames', 0),
            "obs_output_total": getattr(stats, 'output_total_frames', 0),
            "stream_active": getattr(stream, 'output_active', False),
            "stream_bytes": getattr(stream, 'output_bytes', 0),
            "stream_congestion": getattr(stream, 'output_congestion', 0.0),
        }
    except Exception as e:
        return {"obs_error": str(e)}


def calculate_health_score(cpu, fps, dropped_pct):
    """Return a qualitative health label based on CPU, FPS, and dropped frame percentage."""
    if cpu < 70 and fps >= 29.5 and dropped_pct < 0.5:
        return 'EXCELLENT'
    elif cpu < 85 and fps >= 28 and dropped_pct < 2:
        return 'GOOD'
    elif cpu < 95 and fps >= 24 and dropped_pct < 10:
        return 'WARNING'
    else:
        return 'CRITICAL'


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
                
                # Fetch OBS WebSocket stats
                port = inst["websocket_port"]
                password = inst.get("ws_password", "")
                if port:
                    import asyncio
                    obs_stats = await asyncio.to_thread(_fetch_obs_stats, port, password)
                    s.update(obs_stats)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Calculate health score from available metrics
        cpu = s.get("cpu_percent", 0) or 0
        fps = s.get("obs_fps", 0) or 0
        total_frames = s.get("obs_output_total", 0) or 0
        skipped_frames = s.get("obs_output_skipped", 0) or 0
        dropped_pct = (skipped_frames / total_frames * 100) if total_frames > 0 else 0.0
        s["health_score"] = calculate_health_score(cpu, fps, dropped_pct)

        return s

