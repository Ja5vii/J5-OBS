filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix ALL remaining bare web.json_response(...) that don't already have dumps=
import re

# Replace the specific broken line in update_instance (line ~275 area)
content = content.replace(
    'return web.json_response(await manager.db.get_instance(request.match_info["id"]))',
    'return web.json_response(dumps=custom_dumps, data=await manager.db.get_instance(request.match_info["id"]))'
)

# Also fix list_instances which returns a list
# Find any remaining web.json_response( without dumps=
matches = list(re.finditer(r'web\.json_response\((?!dumps=)(?!\s*dumps=)', content))
remaining = [(m.start(), content[m.start():m.start()+80]) for m in matches]
print(f"Remaining bare json_response calls: {len(remaining)}")
for start, snippet in remaining:
    print(f"  {repr(snippet)}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
