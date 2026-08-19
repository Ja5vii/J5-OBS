filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re
content = re.sub(r'[ \t]+env\["OBS_STUDIO_DISABLE_SOURCE_CHROME"\] = "1"', '        env["OBS_STUDIO_DISABLE_SOURCE_CHROME"] = "1"', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
