import os

filepath = r'e:\GitHub\J5-OBS\instance-manager\display_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_init = """    async def initialize(self):
        self._allocated.clear()"""

replacement_init = """    async def initialize(self):
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
                print("TigerVNC downloaded successfully!")"""

target_start = """        vnc_proc = None
        try:
            vnc_proc = subprocess.Popen(
                ["x11vnc", "-display", display_str, "-nopw", "-listen", "127.0.0.1", "-rfbport", vnc_port, "-xkb", "-forever", "-shared"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass # x11vnc not installed"""

replacement_start = """        vnc_proc = None
        try:
            binary = getattr(self, "vnc_binary", "x11vnc")
            if "x0vncserver" in binary:
                # TigerVNC x0vncserver args
                vnc_proc = subprocess.Popen(
                    [binary, "-display", display_str, "-SecurityTypes", "None", "-rfbport", vnc_port],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                vnc_proc = subprocess.Popen(
                    [binary, "-display", display_str, "-nopw", "-listen", "127.0.0.1", "-rfbport", vnc_port, "-xkb", "-forever", "-shared"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            print(f"Failed to start VNC: {e}")"""

content = content.replace(target_init, replacement_init)
content = content.replace(target_start, replacement_start)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected TigerVNC standalone")
