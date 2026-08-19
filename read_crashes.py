filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add a quick endpoint to read the crash logs instead of the obs log
injection = """
    @auth
    async def get_obs_crashes(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.Response(status=403)
            
        inst_id = request.match_info["id"]
        crash_dir = os.path.join(manager.base_dir, "instances", inst_id, "config", "obs-studio", "crashes")
        if not os.path.exists(crash_dir):
            return web.Response(status=404, text="No crashes dir")
            
        files = sorted(os.listdir(crash_dir))
        if not files:
            return web.Response(status=404, text="No crash files")
            
        with open(os.path.join(crash_dir, files[-1]), 'r', encoding='utf-8', errors='ignore') as f:
            return web.Response(text=f.read())
"""

if 'async def get_obs_crashes' not in content:
    content = content.replace('async def get_obs_log(request):', injection + '\n    @auth\n    async def get_obs_log(request):')
    content = content.replace('app.router.add_get("/api/instances/{id}/log", get_obs_log)', 'app.router.add_get("/api/instances/{id}/log", get_obs_log)\n    app.router.add_get("/api/instances/{id}/crashes", get_obs_crashes)')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        print("Injected crash API")
