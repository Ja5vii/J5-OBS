filepath = r'e:\GitHub\J5-OBS\instance-manager\display_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_code = """
        display_str = f":{display_num}"
        proc = subprocess.Popen(
            ["Xvfb", display_str, "-screen", "0", f"{resolution}x{depth}", "-ac", "+extension", "GLX", "+render", "-noreset"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Give Xvfb a moment to start before launching VNC
        import time
        time.sleep(0.5)
        vnc_port = str(5900 + display_num)
        vnc_proc = subprocess.Popen(
            ["x11vnc", "-display", display_str, "-bg", "-nopw", "-listen", "127.0.0.1", "-rfbport", vnc_port, "-xkb", "-forever", "-shared"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._xvfb_processes[instance_id] = {"xvfb": proc, "vnc": vnc_proc}
"""

content = content.replace("""        display_str = f":{display_num}"
        proc = subprocess.Popen(
            ["Xvfb", display_str, "-screen", "0", f"{resolution}x{depth}", "-ac", "+extension", "GLX", "+render", "-noreset"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._xvfb_processes[instance_id] = proc""", start_code)

stop_code = """    def stop_xvfb(self, instance_id):
        procs = self._xvfb_processes.pop(instance_id, None)
        if not procs: return
        
        for p in (procs.get("vnc"), procs.get("xvfb")):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()"""

content = content.replace("""    def stop_xvfb(self, instance_id):
        proc = self._xvfb_processes.pop(instance_id, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()""", stop_code)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
