filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '"--scene", "Main",',
    '"--scene", "Main",\n            "--startstreaming",'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
