filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        if updates:
            await manager.db.update_instance(request.match_info["id"], **updates)
            await manager.db.log_audit_event(request["user"]["id"], "UPDATE_CONNECTION", request.match_info["id"], updates)

        return web.json_response(dumps=custom_dumps, data=await manager.db.get_instance(request.match_info["id"]))"""

replacement = """        try:
            if updates:
                await manager.db.update_instance(request.match_info["id"], **updates)
                await manager.db.log_audit_event(request["user"]["id"], "UPDATE_CONNECTION", request.match_info["id"], updates)
    
            return web.json_response(dumps=custom_dumps, data=await manager.db.get_instance(request.match_info["id"]))
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            manager.logger.error(f"update_connection crashed: {err}")
            return web.json_response(dumps=custom_dumps, data={"error": str(err)}, status=500)"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected try-except in update_connection")
else:
    print("Target not found!")
