import os
filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'env["DBUS_SESSION_BUS_ADDRESS"] = "disabled"\n        env["XDG_RUNTIME_DIR"] = "/tmp"'
replacement = 'env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/dev/null"\n        runtime_dir = os.path.join(inst_dir, "runtime")\n        os.makedirs(runtime_dir, exist_ok=True)\n        env["XDG_RUNTIME_DIR"] = runtime_dir'

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed env!")
else:
    print("Target not found")
