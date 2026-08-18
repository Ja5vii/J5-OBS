filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement_users = '''async def list_users(request):
    users = await manager.db.get_all_users()
    for u in users:
        if "created_at" in u and u["created_at"]:
            u["created_at"] = str(u["created_at"])
    return web.json_response({"users": users})'''

replacement_audit = '''async def get_audit_logs(request):
    logs = await manager.db.get_audit_logs()
    for l in logs:
        if "timestamp" in l and l["timestamp"]:
            l["timestamp"] = str(l["timestamp"])
    return web.json_response({"audit_logs": logs})'''

content = content.replace('''async def list_users(request):
    users = await manager.db.get_all_users()
    return web.json_response({"users": users})''', replacement_users)

content = content.replace('''async def get_audit_logs(request):
    logs = await manager.db.get_audit_logs()
    return web.json_response({"audit_logs": logs})''', replacement_audit)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
