filepath = r'e:\GitHub\J5-OBS\instance-manager\database.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'scene_collection VARCHAR(255),',
    'scene_collection VARCHAR(255),\n    auto_stop BOOLEAN DEFAULT true,'
)

alter_code = """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN auto_stop BOOLEAN DEFAULT true")
            except Exception:
                pass # Column probably already exists
"""

content = content.replace(
    'async with self.pool.acquire() as conn:\n            await conn.execute(SCHEMA)',
    'async with self.pool.acquire() as conn:\n            await conn.execute(SCHEMA)' + alter_code
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
