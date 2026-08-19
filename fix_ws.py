filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    async def _force_start_stream(self, instance_id, ws_port, ws_password):
        import asyncio
        await asyncio.sleep(5)
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', ws_port)) != 0:
                    self.logger.error(f"{instance_id} OBS WebSocket not reachable to force stream.")
                    return
            import obsws_python as obsws"""

replacement = """    async def _force_start_stream(self, instance_id, ws_port, ws_password):
        import asyncio
        import socket
        
        # Retry for up to 30 seconds
        connected = False
        for _ in range(15):
            await asyncio.sleep(2)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', ws_port)) == 0:
                    connected = True
                    break
                    
        if not connected:
            self.logger.error(f"{instance_id} OBS WebSocket not reachable after 30 seconds.")
            return
            
        try:
            import obsws_python as obsws"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed WS retry")
else:
    print("Target not found")
