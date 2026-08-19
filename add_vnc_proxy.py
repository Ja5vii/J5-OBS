filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

vnc_proxy_code = """
    @auth
    async def vnc_proxy(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.Response(status=403)
        
        inst_id = request.match_info["id"]
        display_num = manager.display_manager.get_display(inst_id)
        if not display_num or not manager.process_manager.is_running(inst_id):
            return web.Response(status=404, text="Instance not running or no display")
            
        # x11vnc should be listening on 5900 + display_num
        vnc_port = 5900 + display_num
        
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        import asyncio
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', vnc_port)
        except Exception as e:
            manager.logger.error(f"VNC Connection failed: {e}")
            await ws.close()
            return ws
            
        async def downstream():
            try:
                while True:
                    data = await reader.read(4096)
                    if not data:
                        break
                    await ws.send_bytes(data)
            except Exception:
                pass
            finally:
                await ws.close()
                writer.close()
                
        async def upstream():
            try:
                async for msg in ws:
                    if msg.type == web.WSMsgType.BINARY:
                        writer.write(msg.data)
                        await writer.drain()
            except Exception:
                pass
            finally:
                writer.close()
                
        await asyncio.gather(downstream(), upstream())
        return ws
"""

content = content.replace(
    'app.router.add_get("/api/admin/branding/versions", get_all_branding_versions)',
    'app.router.add_get("/api/admin/branding/versions", get_all_branding_versions)\n    app.router.add_get("/api/instances/{id}/vnc", vnc_proxy)'
)

content = content.replace(
    'app.router.add_get("/api/templates", list_templates)',
    'app.router.add_get("/api/templates", list_templates)\n' + vnc_proxy_code
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
