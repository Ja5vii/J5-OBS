filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'allowed = {"name", "rtmp_url", "rtmp_key", "profile", "scene_collection"}',
    'allowed = {"name", "rtmp_url", "rtmp_key", "profile", "scene_collection", "auto_stop"}'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
