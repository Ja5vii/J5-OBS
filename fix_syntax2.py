filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "f.write(f\"[OBSWebSocket]" in line:
        new_lines.append("        with open(os.path.join(global_dir, \"global.ini\"), \"w\") as f:\n")
        new_lines.append("            f.write(f\"[OBSWebSocket]\\nServerPort={inst.get('websocket_port')}\\nServerPassword={inst.get('ws_password', '')}\\nServerEnabled=true\\n\")\n")
        skip = True
        continue
    
    if skip:
        if "ServerEnabled=true" in line:
            skip = False
        continue
        
    if "with open(os.path.join(global_dir, \"global.ini\"), \"w\") as f:" in line:
        # We already added this
        pass
    else:
        new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Fixed syntax error 2")
