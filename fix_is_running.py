filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('manager.is_running', 'manager.process_manager.is_running')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
