filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('env["QT_QPA_PLATFORM"] = "offscreen"\n', '')
content = content.replace('env["QT_XCB_GL_INTEGRATION"] = "none"\n', '')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
