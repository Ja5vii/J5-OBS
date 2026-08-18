filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'return web.json_response(await manager.restart_instance(request.match_info["id"]))',
    'return web.json_response(dumps=custom_dumps, data=await manager.restart_instance(request.match_info["id"]))'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
