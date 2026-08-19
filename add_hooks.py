filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

hooks_code = """
    # --- Internal RTMP Hooks ---
    async def internal_on_publish(request):
        data = await request.post()
        connection_id = data.get("name")
        if not connection_id:
            return web.Response(status=400)
            
        manager.logger.info(f"Stream ingest connected: {connection_id}")
        instances = await manager.db.get_all_instances()
        target_inst = next((i for i in instances if i.get("connection_id") == connection_id), None)
        if not target_inst:
            manager.logger.warning(f"Rejecting unknown stream key: {connection_id}")
            return web.Response(status=404)
            
        inst_id = target_inst["instance_id"]
        if not manager.is_running(inst_id):
            manager.logger.info(f"Auto-starting instance {inst_id} due to incoming stream")
            # Run start asynchronously so we can return 200 immediately to NGINX
            import asyncio
            asyncio.create_task(manager.start_instance(inst_id))
            
        return web.Response(status=200)

    async def internal_on_publish_done(request):
        data = await request.post()
        connection_id = data.get("name")
        if not connection_id:
            return web.Response(status=400)
            
        manager.logger.info(f"Stream ingest disconnected: {connection_id}")
        instances = await manager.db.get_all_instances()
        target_inst = next((i for i in instances if i.get("connection_id") == connection_id), None)
        if not target_inst:
            return web.Response(status=404)
            
        inst_id = target_inst["instance_id"]
        if manager.is_running(inst_id):
            manager.logger.info(f"Auto-stopping instance {inst_id} due to stream disconnect")
            import asyncio
            asyncio.create_task(manager.stop_instance(inst_id))
            
        return web.Response(status=200)

"""

# Insert before @auth async def list_users
content = content.replace('    @auth\n    async def list_users(request):', hooks_code + '    @auth\n    async def list_users(request):')

# Add routes
routes_code = """
    app.router.add_post("/api/internal/on_publish", internal_on_publish)
    app.router.add_post("/api/internal/on_publish_done", internal_on_publish_done)
"""

content = content.replace('app.router.add_get("/api/status", manager_status)', 'app.router.add_get("/api/status", manager_status)' + routes_code)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
