filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """        with open(os.path.join(global_dir, "global.ini"), "w") as f:
            f.write(f"[OBSWebSocket]\nServerPort={inst.get('websocket_port')}\nServerPassword={inst.get('ws_password', '')}\nServerEnabled=true\n")"""

content = content.replace("f.write(f\"[OBSWebSocket]\nServerPort={inst.get('websocket_port')}\nServerPassword={inst.get('ws_password', '')}\nServerEnabled=true\n\")", "f.write(f\"[OBSWebSocket]\\nServerPort={inst.get('websocket_port')}\\nServerPassword={inst.get('ws_password', '')}\\nServerEnabled=true\\n\")")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed syntax error")
