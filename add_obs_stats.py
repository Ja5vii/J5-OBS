filepath = r'e:\GitHub\J5-OBS\instance-manager\health_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

obs_fetch_code = """
import obsws_python as obsws
def _fetch_obs_stats(port, password):
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
"""

content = content.replace('import psutil\n', 'import psutil\n' + obs_fetch_code)

async_call = """
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
"""

content = content.replace("""
        if pid and self.manager.process_manager.is_running(instance_id):
            try:
                p = psutil.Process(pid)
                s["cpu_percent"] = p.cpu_percent(interval=0.05)
                s["ram_mb"] = round(p.memory_info().rss / 1048576, 1)
                s["uptime_seconds"] = int(time.time() - p.create_time())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
""", async_call)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
