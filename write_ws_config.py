import os
filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        self._write_obs_config(instance_id, profile_dir, scene_dir, inst)"""

replacement = """        global_dir = os.path.join(inst_dir, "config", "obs-studio")
        os.makedirs(global_dir, exist_ok=True)
        with open(os.path.join(global_dir, "global.ini"), "w") as f:
            f.write(f"[OBSWebSocket]\nServerPort={inst.get('websocket_port')}\nServerPassword={inst.get('ws_password', '')}\nServerEnabled=true\n")
        self._write_obs_config(instance_id, profile_dir, scene_dir, inst)"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected global.ini")
else:
    print("Target not found")
