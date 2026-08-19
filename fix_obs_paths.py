filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('os.path.join(inst_dir, "obs-studio", "basic", "profiles", "default")', 'os.path.join(inst_dir, "config", "obs-studio", "basic", "profiles", "default")')
content = content.replace('os.path.join(inst_dir, "obs-studio", "basic", "scenes")', 'os.path.join(inst_dir, "config", "obs-studio", "basic", "scenes")')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
