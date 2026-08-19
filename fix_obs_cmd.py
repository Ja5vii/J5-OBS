filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        obs_cmd = [
            "obs",
            "--multiplatform",
            "--portable",
            "--profile", profile_name,
            "--collection", inst.get("scene_collection", "Main"),
            "--scene", "Main",
            "--startstreaming",
        ]"""

replacement = """        obs_cmd = [
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

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected OBS CLI websocket arguments")
else:
    print("Target not found")
