filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        if not inst.get("connection_id"):
            updates["connection_id"] = f"j5_{request['user']['username']}_{secrets.token_hex(4)}\""""
replacement = """        if not inst.get("connection_id"):
            username = request["user"].get("username", "admin")
            updates["connection_id"] = f"j5_{username}_{secrets.token_hex(4)}\""""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Target not found!")
