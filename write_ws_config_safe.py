import os
filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        self._write_obs_config(instance_id, profile_dir, scene_dir, inst)"""

replacement = """        global_dir = os.path.join(inst_dir, "config", "obs-studio")
        os.makedirs(global_dir, exist_ok=True)
        with open(os.path.join(global_dir, "global.ini"), "w") as f:
            f.write("[OBSWebSocket]\\nServerPort=" + str(inst.get('websocket_port', 4455)) + "\\nServerPassword=" + inst.get('ws_password', '') + "\\nServerEnabled=true\\n")
        self._write_obs_config(instance_id, profile_dir, scene_dir, inst)"""

content = content.replace(target, replacement)

target2 = """        obs_cmd = [
            "obs",
            "--multiplatform",
            "--portable",
            "--profile", profile_name,
            "--collection", inst.get("scene_collection", "Main"),
            "--scene", "Main",
            "--startstreaming",
        ]"""

replacement2 = """        obs_cmd = [
            "obs",
            "--multiplatform",
            "--portable",
            "--profile", profile_name,
            "--collection", inst.get("scene_collection", "Main"),
            "--scene", "Main",
            "--websocket_port", str(inst.get("websocket_port", 4455)),
            "--websocket_password", inst.get("ws_password", ""),
            "--startstreaming",
        ]"""

content = content.replace(target2, replacement2)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected safely")
