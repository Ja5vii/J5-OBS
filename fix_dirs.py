filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'profile_dir = os.path.join(inst_dir, "profiles")',
    'profile_dir = os.path.join(inst_dir, "config", "obs-studio", "basic", "profiles")'
)
content = content.replace(
    'scene_dir = os.path.join(inst_dir, "scenes")',
    'scene_dir = os.path.join(inst_dir, "config", "obs-studio", "basic", "scenes")'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
