filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re
# Replace web.json_response( with web.json_response( but passing dumps. Wait, easier:
# Just import functools and json at the top.
# Then define custom_dumps = functools.partial(json.dumps, default=str)
# Then replace web.json_response( with web.json_response(dumps=custom_dumps, 

header = '''import json
import functools
custom_dumps = functools.partial(json.dumps, default=str)
'''

content = content.replace('from aiohttp import web', 'from aiohttp import web\n' + header)
content = content.replace('web.json_response({', 'web.json_response(dumps=custom_dumps, data={')
content = content.replace('web.json_response([', 'web.json_response(dumps=custom_dumps, data=[')

# Also revert my previous patch_dates.py manually to avoid duplicates
content = content.replace('''for u in users:
        if "created_at" in u and u["created_at"]:
            u["created_at"] = str(u["created_at"])''', '')
            
content = content.replace('''for l in logs:
        if "timestamp" in l and l["timestamp"]:
            l["timestamp"] = str(l["timestamp"])''', '')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
