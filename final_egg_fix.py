import json

path = r'e:\GitHub\J5-OBS\egg-j5-obs-multi-instance.json'
with open(path, 'r', encoding='utf-8') as f:
    old_data = json.load(f)

# Extract old variables
variables = old_data.get("variables", [])

valid_egg = {
    "_comment": "DO NOT EDIT: FILE GENERATED AUTOMATICALLY BY PTERODACTYL PANEL - PTERODACTYL.IO",
    "meta": {
        "version": "PTDL_v2",
        "update_url": None
    },
    "exported_at": "2024-01-01T00:00:00+00:00",
    "name": "J5 OBS Multi-Instance",
    "author": "j5@ja5vii.com",
    "description": "Multi-instance OBS Studio host for Pterodactyl. Manages N independent OBS instances with isolated configs, displays, WebSocket, and RTMP within a single Game Server.",
    "features": None,
    "docker_images": {
        "J5 OBS Image": "ghcr.io/ja5vii/obs-multi-instance:latest",
        "Ubuntu 22.04 (Fallback)": "ghcr.io/pterodactyl/yolks:ubuntu_22.04"
    },
    "file_denylist": [],
    "startup": "/home/container/startup.sh",
    "config": {
        "files": "{}",
        "startup": "{\r\n    \"done\": \"Instance Manager ready\"\r\n}",
        "logs": "{}",
        "stop": "^^C"
    },
    "scripts": {
        "installation": {
            "script": "#!/bin/bash\napt-get update -y && apt-get install -y git\ncd /mnt/server\nif [ ! -d .git ]; then\n    git clone ${GIT_ADDRESS} .\nelse\n    git pull\nfi\nchmod +x install.sh\n./install.sh",
            "container": "ghcr.io/pterodactyl/installers:debian",
            "entrypoint": "bash"
        }
    },
    "variables": variables
}

with open(path, 'w', encoding='utf-8') as f:
    json.dump(valid_egg, f, indent=4)
