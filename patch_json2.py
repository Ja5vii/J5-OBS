import re

filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all remaining web.json_response(X) with web.json_response(dumps=custom_dumps, data=X)
content = re.sub(r'web\.json_response\((?!dumps=)([^{}\[\]]+)\)', r'web.json_response(dumps=custom_dumps, data=\1)', content)

# But wait, what if it's web.json_response(active) ?
# That matches!

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
