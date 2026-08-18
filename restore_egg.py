import json
import subprocess

# Get the original JSON string
result = subprocess.run(["git", "show", "HEAD~1:egg-j5-obs-multi-instance.json"], capture_output=True, text=True, check=True)
data = json.loads(result.stdout)

# Add our new DB variables
db_vars = [
    {
      "name": "Database Host",
      "description": "PostgreSQL Host address",
      "env_variable": "J5_DB_HOST",
      "default_value": "127.0.0.1",
      "user_viewable": True,
      "user_editable": True,
      "rules": "required|string"
    },
    {
      "name": "Database Port",
      "description": "PostgreSQL Port",
      "env_variable": "J5_DB_PORT",
      "default_value": "5432",
      "user_viewable": True,
      "user_editable": True,
      "rules": "required|integer"
    },
    {
      "name": "Database User",
      "description": "PostgreSQL Username",
      "env_variable": "J5_DB_USER",
      "default_value": "postgres",
      "user_viewable": True,
      "user_editable": True,
      "rules": "required|string"
    },
    {
      "name": "Database Password",
      "description": "PostgreSQL Password",
      "env_variable": "J5_DB_PASS",
      "default_value": "",
      "user_viewable": True,
      "user_editable": True,
      "rules": "required|string"
    },
    {
      "name": "Database Name",
      "description": "PostgreSQL Database Name",
      "env_variable": "J5_DB_NAME",
      "default_value": "j5obs",
      "user_viewable": True,
      "user_editable": True,
      "rules": "required|string"
    }
]

# Check if they are already in there
existing_vars = [v["env_variable"] for v in data["variables"]]
for v in db_vars:
    if v["env_variable"] not in existing_vars:
        data["variables"].append(v)

with open(r"e:\GitHub\J5-OBS\egg-j5-obs-multi-instance.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

