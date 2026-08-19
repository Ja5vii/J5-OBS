filepath = r'e:\GitHub\J5-OBS\instance-manager\display_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

vnc_code = """
        vnc_proc = None
        try:
            vnc_proc = subprocess.Popen(
                ["x11vnc", "-display", display_str, "-nopw", "-listen", "127.0.0.1", "-rfbport", vnc_port, "-xkb", "-forever", "-shared"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass # x11vnc not installed
        self._xvfb_processes[instance_id] = {"xvfb": proc, "vnc": vnc_proc}
"""

content = content.replace("""        vnc_proc = subprocess.Popen(
            ["x11vnc", "-display", display_str, "-nopw", "-listen", "127.0.0.1", "-rfbport", vnc_port, "-xkb", "-forever", "-shared"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._xvfb_processes[instance_id] = {"xvfb": proc, "vnc": vnc_proc}""", vnc_code)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
