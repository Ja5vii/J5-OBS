filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'if manager.process_manager.is_running(inst_id):',
    'if manager.process_manager.is_running(inst_id) and target_inst.get("auto_stop", True):'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
