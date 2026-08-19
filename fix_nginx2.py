filepath = r'e:\GitHub\J5-OBS\instance-manager\main.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """            subprocess.Popen([
                "nginx",
                "-e", os.path.join(self.base_dir, "j5-obs", "logs", "nginx-error.log"),
                "-c", os.path.join(self.base_dir, "instance-manager", "nginx.conf")
            ])"""

replacement = """            subprocess.Popen([
                "nginx",
                "-g", f"error_log {os.path.join(self.base_dir, 'j5-obs', 'logs', 'nginx-error.log')};",
                "-c", os.path.join(self.base_dir, "instance-manager", "nginx.conf")
            ])"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed NGINX launch with -g")
else:
    print("Target not found")
