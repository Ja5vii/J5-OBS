filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """            if provided.startswith("Bearer "):
                provided = provided[7:]
            else:
                provided = request.headers.get("X-Auth-Token", "")"""

replacement = """            if provided.startswith("Bearer "):
                provided = provided[7:]
            else:
                provided = request.headers.get("X-Auth-Token", "")
            
            if not provided:
                provided = request.query.get("token", "")"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Not found")
