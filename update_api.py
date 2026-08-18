import sys
import re

with open(r'e:\GitHub\J5-OBS\instance-manager\api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we don't allow username updates except maybe admins. Actually prompt said NO ONE CAN UPDATE USERNAME.
content = re.sub(r'if data\.get\("username"\): updates\["username"\] = data\["username"\]\n', '', content)

audit_logs_endpoint = """
    @auth
    @require_admin
    async def get_audit_logs(request):
        logs = await manager.db.get_audit_logs()
        return web.json_response({"audit_logs": logs})

    @auth
    async def update_connection(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response({"error": "Not found or Forbidden"}, status=403)
        data = await request.json()
        import secrets
        
        updates = {}
        if "platform" in data:
            updates["platform"] = data["platform"]
        if "rtmp_key" in data:
            updates["rtmp_key"] = data["rtmp_key"]
            
        # Optional custom RTMP
        if "rtmp_url" in data:
            updates["rtmp_url"] = data["rtmp_url"]
        else:
            # Generate automatically based on platform if needed, or leave empty if it's twitch, wait OBS needs full URL if it's custom.
            # But we are using service.json type "rtmp_custom". So rtmp_url is required.
            pass
            
        # Generate connection ID if it doesn't exist
        inst = await manager.db.get_instance(request.match_info["id"])
        if not inst.get("connection_id"):
            updates["connection_id"] = f"j5_{request['user']['username']}_{secrets.token_hex(4)}"

        if updates:
            await manager.db.update_instance(request.match_info["id"], **updates)
            await manager.db.log_audit_event(request["user"]["id"], "UPDATE_CONNECTION", request.match_info["id"], updates)

        return web.json_response(await manager.db.get_instance(request.match_info["id"]))
"""

content = content.replace('    @auth\n    async def manager_status(request):', audit_logs_endpoint + '\n    @auth\n    async def manager_status(request):')

# We should also log other actions
content = content.replace(
    'return web.json_response(await manager.start_instance(request.match_info["id"]))',
    'res = await manager.start_instance(request.match_info["id"])\n            await manager.db.log_audit_event(request["user"]["id"], "START_INSTANCE", request.match_info["id"])\n            return web.json_response(res)'
)
content = content.replace(
    'return web.json_response(await manager.stop_instance(request.match_info["id"]))',
    'res = await manager.stop_instance(request.match_info["id"])\n            await manager.db.log_audit_event(request["user"]["id"], "STOP_INSTANCE", request.match_info["id"])\n            return web.json_response(res)'
)

# Add routes
routes = """    app.router.add_get("/api/audit", get_audit_logs)
    app.router.add_patch("/api/instances/{id}/connection", update_connection)
    app.router.add_get("/api/instances/{id}/stats", get_stats)"""
content = content.replace('    app.router.add_get("/api/instances/{id}/stats", get_stats)', routes)

with open(r'e:\GitHub\J5-OBS\instance-manager\api.py', 'w', encoding='utf-8') as f:
    f.write(content)
