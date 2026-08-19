import subprocess


class DisplayManager:
    def __init__(self, config):
        self.config = config
        self._allocated = {}
        self._xvfb_processes = {}

    async def initialize(self):
        self._allocated.clear()
        import asyncio
        import urllib.request
        import tarfile
        import os
        base_dir = os.environ.get("CONTAINER_DIR", "/home/container")
        tools_dir = os.path.join(base_dir, "tools")
        os.makedirs(tools_dir, exist_ok=True)
        self.vnc_binary = "x11vnc"
        
        try:
            # Check if x11vnc exists in system
            import subprocess
            subprocess.run(["x11vnc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            # Download TigerVNC if not present
            self.vnc_binary = os.path.join(tools_dir, "usr", "bin", "x0vncserver")
            if not os.path.exists(self.vnc_binary):
                print("Downloading standalone TigerVNC x0vncserver...")
                url = "https://sourceforge.net/projects/tigervnc/files/stable/1.13.1/tigervnc-1.13.1.x86_64.tar.gz/download"
                tar_path = os.path.join(tools_dir, "tigervnc.tar.gz")
                await asyncio.to_thread(urllib.request.urlretrieve, url, tar_path)
                print("Extracting TigerVNC...")
                def extract():
                    with tarfile.open(tar_path, "r:gz") as tar:
                        for member in tar.getmembers():
                            if member.name.endswith("x0vncserver"):
                                member.name = "usr/bin/x0vncserver"
                                tar.extract(member, path=tools_dir)
                                os.chmod(os.path.join(tools_dir, "usr", "bin", "x0vncserver"), 0o755)
                await asyncio.to_thread(extract)
                if os.path.exists(tar_path):
                    os.remove(tar_path)
                print("TigerVNC downloaded successfully!")

    def allocate(self, instance_id):
        cfg = self.config.get()
        base = cfg["displays"]["base"]
        used = set(self._allocated.values())
        for i in range(cfg["resources"]["max_instances"]):
            display_num = base + i + 1
            if display_num not in used:
                self._allocated[instance_id] = display_num
                return display_num
        raise RuntimeError("No available display numbers")

    def release(self, instance_id):
        self.stop_xvfb(instance_id)
        self._allocated.pop(instance_id, None)

    def get_display(self, instance_id):
        return self._allocated.get(instance_id)

    def start_xvfb(self, instance_id):
        display_num = self._allocated.get(instance_id)
        if display_num is None:
            raise ValueError(f"No display allocated for {instance_id}")
        if instance_id in self._xvfb_processes:
            return
        cfg = self.config.get()
        resolution = cfg["displays"]["resolution"]
        depth = cfg["displays"]["depth"]

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

        vnc_proc = None
        try:
            binary = getattr(self, "vnc_binary", "x11vnc")
            if "x0vncserver" in binary:
                # TigerVNC x0vncserver args
                import sys
                vnc_proc = subprocess.Popen(
                    [binary, "display=" + display_str, "SecurityTypes=None", "rfbport=" + vnc_port],
                    stdout=sys.stderr,
                    stderr=sys.stderr,
                )
            else:
                import sys
                vnc_proc = subprocess.Popen(
                    [binary, "-display", display_str, "-nopw", "-listen", "127.0.0.1", "-rfbport", vnc_port, "-xkb", "-forever", "-shared"],
                    stdout=sys.stderr,
                    stderr=sys.stderr,
                )
        except Exception as e:
            print(f"Failed to start VNC: {e}")
        self._xvfb_processes[instance_id] = {"xvfb": proc, "vnc": vnc_proc}



    def stop_xvfb(self, instance_id):
        procs = self._xvfb_processes.pop(instance_id, None)
        if not procs: return
        
        for p in (procs.get("vnc"), procs.get("xvfb")):
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()

    def get_display_env(self, instance_id):
        display_num = self._allocated.get(instance_id)
        if display_num is None:
            return {}
        return {"DISPLAY": f":{display_num}"}
