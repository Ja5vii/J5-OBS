import re

with open(r'e:\GitHub\J5-OBS\instance-manager\database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix empty strings for owner_id in database.py
content = content.replace("if owner_id:", "if owner_id and owner_id.strip():")

with open(r'e:\GitHub\J5-OBS\instance-manager\database.py', 'w', encoding='utf-8') as f:
    f.write(content)
