filepath = r'e:\GitHub\J5-OBS\instance-manager\database.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN connection_id VARCHAR(255);")
            except Exception: pass"""

replacement = """            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN connection_id VARCHAR(255);")
            except Exception: pass
            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN auto_stop BOOLEAN DEFAULT true;")
            except Exception: pass"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added auto_stop alter table")
else:
    print("Target not found")
