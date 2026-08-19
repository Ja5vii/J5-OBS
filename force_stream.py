import os

filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace basic.ini writing
target_ini = """        basic_ini = os.path.join(profile_path, "basic.ini")
        if not os.path.exists(basic_ini):
            with open(basic_ini, "w") as f:
                f.write(f"[General]\\nName={instance_id}\\n[Output]\\nFilenameFormatting=%CCYY-%MM-%DD %hh-%mm-%ss\\n")"""

replacement_ini = """        basic_ini = os.path.join(profile_path, "basic.ini")
        # Always overwrite basic.ini to ensure x264 software encoder is forced
        with open(basic_ini, "w") as f:
            f.write(f"[General]\\nName={instance_id}\\n")
            f.write("[Video]\\nBaseCX=1920\\nBaseCY=1080\\nOutputCX=1920\\nOutputCY=1080\\nFPSCommon=30\\n")
            f.write("[SimpleOutput]\\nVBitrate=3000\\nStreamEncoder=x264\\nRecEncoder=x264\\n")
            f.write("[Output]\\nMode=Simple\\n")
            f.write("[AdvOut]\\nEncoder=obs_x264\\n")"""

content = content.replace(target_ini, replacement_ini)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced basic.ini")
