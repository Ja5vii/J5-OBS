filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'if "rtmp_key" in data:\n            updates["rtmp_key"] = data["rtmp_key"]',
    'if "rtmp_key" in data:\n            updates["rtmp_key"] = data["rtmp_key"]\n        if "auto_stop" in data:\n            updates["auto_stop"] = data["auto_stop"]'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
