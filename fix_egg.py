import json

path = r'e:\GitHub\J5-OBS\egg-j5-obs-multi-instance.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

if 'meta' not in data:
    data['meta'] = {}

data['meta']['version'] = 'PTDL_v2'
if '_comment' not in data:
    data['_comment'] = 'DO NOT EDIT: FILE GENERATED AUTOMATICALLY BY PTERODACTYL PANEL - PTERODACTYL.IO'
if 'exported_at' not in data:
    data['exported_at'] = '2023-01-01T00:00:00+00:00'
    
# Let's ensure top-level properties expected by Pterodactyl exist
expected = ["name", "author", "description", "features", "docker_images", "file_denylist", "startup", "config", "scripts", "variables"]

# Docker images format changed in v2
if 'image' in data:
    data['docker_images'] = {
        "Ubuntu 22.04 (Base)": "ghcr.io/pterodactyl/yolks:ubuntu_22.04"
    }

if 'config' not in data:
    data['config'] = {
        "files": "{}",
        "startup": "{\r\n    \"done\": \"Instance Manager ready\"\r\n}",
        "logs": "{}",
        "stop": "^^C"
    }

if 'scripts' not in data:
    data['scripts'] = {
        "installation": {
            "script": "#!/bin/bash\napt-get update -y && apt-get install -y git\ncd /mnt/server\nif [ ! -d .git ]; then\n    git clone ${GIT_ADDRESS} .\nelse\n    git pull\nfi\nchmod +x install.sh\n./install.sh",
            "container": "ubuntu:22.04",
            "entrypoint": "bash"
        }
    }

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
