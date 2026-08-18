import json

path = r'e:\GitHub\J5-OBS\egg-j5-obs-multi-instance.json'
with open(path, 'r', encoding='utf-8') as f:
    old_data = json.load(f)

# Strict PTDL_v2 structure
new_data = {
    "_comment": "DO NOT EDIT: FILE GENERATED AUTOMATICALLY BY PTERODACTYL PANEL - PTERODACTYL.IO",
    "meta": {
        "version": "PTDL_v2",
        "update_url": None
    },
    "exported_at": "2023-01-01T00:00:00+00:00",
    "name": old_data.get("name", "J5 OBS Multi-Instance"),
    "author": old_data.get("author", "J5 Studio"),
    "description": old_data.get("description", "Multi-instance OBS Studio host for Pterodactyl."),
    "features": None,
    "docker_images": old_data.get("docker_images", {
        "J5 OBS Base": "ghcr.io/pterodactyl/yolks:ubuntu_22.04"
    }),
    "file_denylist": [],
    "startup": old_data.get("startup", "./startup.sh"),
    "config": old_data.get("config", {
        "files": "{}",
        "startup": "{\r\n    \"done\": \"Instance Manager ready\"\r\n}",
        "logs": "{}",
        "stop": "^^C"
    }),
    "scripts": old_data.get("scripts", {
        "installation": {
            "script": "#!/bin/bash\napt-get update -y && apt-get install -y git\ncd /mnt/server\nif [ ! -d .git ]; then\n    git clone ${GIT_ADDRESS} .\nelse\n    git pull\nfi\nchmod +x install.sh\n./install.sh",
            "container": "ghcr.io/pterodactyl/installers:debian",
            "entrypoint": "bash"
        }
    }),
    "variables": old_data.get("variables", [])
}

with open(path, 'w', encoding='utf-8') as f:
    json.dump(new_data, f, indent=4)
