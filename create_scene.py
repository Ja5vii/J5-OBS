import os
import json

def generate_scene(connection_id):
    rtmp_url = f"rtmp://127.0.0.1:1935/live/{connection_id}"
    
    return {
        "current_scene": "Main",
        "current_program_scene": "Main",
        "name": "Main",
        "scene_order": [{"name": "Main"}],
        "scenes": [
            {
                "id": "scene",
                "name": "Main",
                "settings": {
                    "id_counter": 2,
                    "items": [
                        {
                            "align": 5,
                            "bounds": {"x": 1920.0, "y": 1080.0},
                            "bounds_align": 0,
                            "bounds_type": 2,
                            "id": 1,
                            "locked": False,
                            "name": "Moblin_RTMP",
                            "pos": {"x": 0.0, "y": 0.0},
                            "rot": 0.0,
                            "scale": {"x": 1.0, "y": 1.0},
                            "visible": True,
                            "source_file": ""
                        }
                    ]
                }
            }
        ],
        "sources": [
            {
                "id": "ffmpeg_source",
                "name": "Moblin_RTMP",
                "settings": {
                    "input": rtmp_url,
                    "is_local_file": False,
                    "hw_decode": False,
                    "clear_on_media_end": False,
                    "restart_on_activate": True
                }
            }
        ]
    }

filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

injection = """
        scene_path = os.path.join(inst_dir, "obs-studio", "basic", "scenes")
        os.makedirs(scene_path, exist_ok=True)
        
        main_scene_json = os.path.join(scene_path, "Main.json")
        scene_data = {
            "current_scene": "Main",
            "current_program_scene": "Main",
            "name": "Main",
            "scene_order": [{"name": "Main"}],
            "scenes": [
                {
                    "id": "scene",
                    "name": "Main",
                    "settings": {
                        "id_counter": 2,
                        "items": [
                            {
                                "align": 5,
                                "bounds": {"x": 1920.0, "y": 1080.0},
                                "bounds_align": 0,
                                "bounds_type": 2,
                                "id": 1,
                                "locked": False,
                                "name": "Moblin_RTMP",
                                "pos": {"x": 0.0, "y": 0.0},
                                "rot": 0.0,
                                "scale": {"x": 1.0, "y": 1.0},
                                "visible": True
                            }
                        ]
                    }
                }
            ],
            "sources": [
                {
                    "id": "ffmpeg_source",
                    "name": "Moblin_RTMP",
                    "settings": {
                        "input": f"rtmp://127.0.0.1:1935/live/{inst.get('connection_id')}",
                        "is_local_file": False,
                        "hw_decode": False,
                        "clear_on_media_end": False,
                        "restart_on_activate": True
                    }
                }
            ]
        }
        with open(main_scene_json, "w") as f:
            json.dump(scene_data, f)
"""

if 'def _start_obs(' in content:
    content = content.replace('def _start_obs(', 'def _start_obs(' + injection) # Wait, it's better to put it where profile is created
    pass

with open(r'e:\GitHub\J5-OBS\create_scene.py', 'w') as f:
    pass # I will just use replace_file_content instead of script for accuracy
