filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

log_api_code = """
    @auth
    async def get_obs_log(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.Response(status=403)
            
        inst_id = request.match_info["id"]
        log_path = os.path.join(manager.base_dir, "instances", inst_id, "logs", "obs.log")
        if not os.path.exists(log_path):
            return web.Response(status=404, text="Log not found")
            
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Return last 100 lines
        return web.Response(text="".join(lines[-100:]))
"""

content = content.replace(
    'app.router.add_get("/api/instances/{id}/stats", get_stats)',
    'app.router.add_get("/api/instances/{id}/stats", get_stats)\n    app.router.add_get("/api/instances/{id}/log", get_obs_log)'
)

content = content.replace(
    'app.router.add_get("/api/templates", list_templates)',
    'app.router.add_get("/api/templates", list_templates)\n' + log_api_code
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
