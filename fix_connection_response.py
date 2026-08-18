filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix update_connection return - it's the one right after "await manager.db.log_audit_event" about UPDATE_CONNECTION
old = '        return web.json_response(await manager.db.get_instance(request.match_info["id"]))\n\n\n    # --- Global Branding ---'
new = '        return web.json_response(dumps=custom_dumps, data=await manager.db.get_instance(request.match_info["id"]))\n\n\n    # --- Global Branding ---'
if old in content:
    content = content.replace(old, new)
    print("Replaced update_connection response")
else:
    # Try to find by context
    import re
    content = re.sub(
        r'(UPDATE_CONNECTION.*?\n\s+)\n(\s+return web\.json_response\(await manager\.db\.get_instance)',
        r'\1\n\2',
        content, flags=re.DOTALL
    )
    # Just manually fix it - find the update_connection function
    idx = content.find('async def update_connection(request):')
    if idx != -1:
        # Find the last return in that function
        func_chunk = content[idx:idx+2000]
        fixed_chunk = func_chunk.replace(
            'return web.json_response(await manager.db.get_instance(request.match_info["id"]))',
            'return web.json_response(dumps=custom_dumps, data=await manager.db.get_instance(request.match_info["id"]))',
            1
        )
        content = content[:idx] + fixed_chunk + content[idx+2000:]
        print("Fixed via manual search")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
