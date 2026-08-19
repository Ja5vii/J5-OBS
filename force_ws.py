filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        self._processes[instance_id] = {"process": proc, "log_file": log_fh}
        await self.manager.db.update_instance(instance_id, pid=proc.pid, status="ONLINE")
        self.logger.info(f"{instance_id} started (PID: {proc.pid})")"""

injection = """    async def _force_start_stream(self, instance_id, ws_port, ws_password):
        import asyncio
        await asyncio.sleep(5)
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', ws_port)) != 0:
                    self.logger.error(f"{instance_id} OBS WebSocket not reachable to force stream.")
                    return
            import obsws_python as obsws
            client = obsws.ReqClient(host='127.0.0.1', port=ws_port, password=ws_password, timeout=3)
            res = client.get_stream_status()
            if not getattr(res, 'output_active', False):
                self.logger.info(f"{instance_id} Stream not active. Forcing StartStream via WebSocket...")
                client.start_stream()
                self.logger.info(f"{instance_id} StartStream command sent successfully via WS.")
            else:
                self.logger.info(f"{instance_id} Stream is already active.")
        except Exception as e:
            self.logger.error(f"{instance_id} WS StartStream FAILED: {e}")

"""

if "def _force_start_stream" not in content:
    content = content.replace("    async def stop_instance", injection + "    async def stop_instance")
    replacement = target + """\n        import asyncio\n        asyncio.create_task(self._force_start_stream(instance_id, inst.get("websocket_port"), inst.get("ws_password", "")))"""
    content = content.replace(target, replacement)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected WS force start")
else:
    print("Already injected")
