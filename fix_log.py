filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        log_path = os.path.join(manager.base_dir, "instances", inst_id, "logs", "obs.log")
        if not os.path.exists(log_path):
            return web.Response(status=404, text="Log not found")
            
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Return last 100 lines
        return web.Response(text="".join(lines[-100:]))"""

replacement = """        obs_log_dir = os.path.join(manager.base_dir, "instances", inst_id, "config", "obs-studio", "logs")
        log_path = None
        if os.path.exists(obs_log_dir):
            files = sorted([f for f in os.listdir(obs_log_dir) if f.endswith(".txt")])
            if files:
                log_path = os.path.join(obs_log_dir, files[-1])
        
        if not log_path:
            log_path = os.path.join(manager.base_dir, "instances", inst_id, "logs", "obs.log")
            
        if not os.path.exists(log_path):
            return web.Response(status=404, text="Log not found")
            
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Return last 200 lines
        return web.Response(text="".join(lines[-200:]))"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Target not found!")
