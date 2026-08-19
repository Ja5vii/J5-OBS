filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'env["GALLIUM_DRIVER"] = "llvmpipe"'
replacement = 'env["GALLIUM_DRIVER"] = "llvmpipe"\n        env["DBUS_SESSION_BUS_ADDRESS"] = "disabled"\n        env["XDG_RUNTIME_DIR"] = "/tmp"'

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed env!")
else:
    print("Target not found")
