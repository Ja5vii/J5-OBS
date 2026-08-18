import sys

with open('e:\\GitHub\\J5-OBS\\instance-manager\\api.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

insert_idx = 0
for i, line in enumerate(lines):
    if line.strip().startswith('app.router.add_post("/api/auth/login"'):
        insert_idx = i
        break

branding_code = '''
    # --- Global Branding ---
    async def get_active_branding(request):
        try:
            active = await manager.db.get_active_branding()
            if not active:
                return web.json_response({"error": "No active branding"}, status=404)
            import json
            if isinstance(active["config_json"], str):
                active["config_json"] = json.loads(active["config_json"])
            # Format datetime
            active["published_at"] = active["published_at"].isoformat()
            return web.json_response(active)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @auth
    @require_admin
    async def publish_branding(request):
        data = await request.json()
        version_id = data.get("id")
        version_tag = data.get("version_tag")
        config_json = data.get("config_json")
        signature = data.get("signature", "")
        
        if not all([version_id, version_tag, config_json]):
            return web.json_response({"error": "Missing required fields"}, status=400)
            
        try:
            await manager.db.publish_branding(version_id, version_tag, config_json, signature)
            await manager.db.log_audit_event(request["user"]["id"], "BRANDING_PUBLISHED", version_tag)
            return web.json_response({"ok": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @auth
    @require_admin
    async def get_all_branding_versions(request):
        try:
            versions = await manager.db.get_all_branding_versions()
            for v in versions:
                v["published_at"] = v["published_at"].isoformat()
            return web.json_response({"versions": versions})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
'''

route_code = '''
    app.router.add_get("/api/branding/active", get_active_branding)
    app.router.add_post("/api/admin/branding", publish_branding)
    app.router.add_get("/api/admin/branding/versions", get_all_branding_versions)
'''

lines.insert(insert_idx, branding_code)

for i, line in enumerate(lines):
    if line.strip().startswith('app.router.add_get("/api/templates"'):
        lines.insert(i + 1, route_code)
        break

with open('e:\\GitHub\\J5-OBS\\instance-manager\\api.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
