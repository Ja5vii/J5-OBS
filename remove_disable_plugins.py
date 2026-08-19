filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('env["OBS_DISABLE_PLUGINS"] = "1"', '# env["OBS_DISABLE_PLUGINS"] = "1"')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed OBS_DISABLE_PLUGINS")
