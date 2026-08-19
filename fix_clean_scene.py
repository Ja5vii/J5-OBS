filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip() == 'connection_id = inst_data.get("connection_id")':
        start_idx = i
    if start_idx != -1 and line.strip() == 'with open(scene_col_path, "w") as f:':
        end_idx = i + 2 # include the json.dump
        break

if start_idx != -1 and end_idx != -1:
    new_logic = """        connection_id = inst_data.get("connection_id")
        if connection_id:
            scene_collection = inst_data.get("scene_collection", "Main")
            os.makedirs(scene_dir, exist_ok=True)
            main_scene_json = os.path.join(scene_dir, f"{scene_collection}.json")
            
            # Always overwrite to ensure source is correct
            scene_data = {
                "current_scene": "Main",
                "current_program_scene": "Main",
                "name": scene_collection,
                "scene_order": [{"name": "Main"}],
                "scenes": [{"id": "scene","name": "Main","settings": {"id_counter": 2,"items": [{"align": 5,"bounds": {"x": 1920.0, "y": 1080.0},"bounds_align": 0,"bounds_type": 2,"id": 1,"locked": False,"name": "Moblin_RTMP","pos": {"x": 0.0, "y": 0.0},"rot": 0.0,"scale": {"x": 1.0, "y": 1.0},"visible": True}]}}],
                "sources": [{"id": "ffmpeg_source","name": "Moblin_RTMP","settings": {"input": f"rtmp://127.0.0.1:1935/live/{connection_id}","is_local_file": False,"hw_decode": False,"clear_on_media_end": False,"restart_on_activate": True}}]
            }
            with open(main_scene_json, "w") as f:
                json.dump(scene_data, f)
"""
    lines = lines[:start_idx] + [new_logic] + lines[end_idx:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("".join(lines))
    print("Fixed!")
else:
    print(f"Not found {start_idx} {end_idx}")
