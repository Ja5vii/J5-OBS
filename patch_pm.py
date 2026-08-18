import os

filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''
            # Inject absolute path to logo if it exists
            config_json = branding.get("config_json", {})
            if "logo_filename" in config_json:
                config_json["logo_absolute_path"] = os.path.join(self.manager.base_dir, "j5-obs", "branding_assets", config_json["logo_filename"])
            branding["config_json"] = config_json
            
            with open(os.path.join(inst_dir, "j5_branding.json"), "w", encoding="utf-8") as bf:
                json.dump(branding, bf)
'''

content = content.replace('with open(os.path.join(inst_dir, "j5_branding.json"), "w", encoding="utf-8") as bf:\n                json.dump(branding, bf)', replacement)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
