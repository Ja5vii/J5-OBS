filepath = r'e:\GitHub\J5-OBS\instance-manager\display_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                vnc_proc = subprocess.Popen(
                    [binary, "-display", display_str, "-SecurityTypes", "None", "-rfbport", vnc_port],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )"""

replacement = """                import sys
                vnc_proc = subprocess.Popen(
                    [binary, "display=" + display_str, "SecurityTypes=None", "rfbport=" + vnc_port],
                    stdout=sys.stderr,
                    stderr=sys.stderr,
                )"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed VNC args and routing to stderr")
else:
    print("Target not found")
