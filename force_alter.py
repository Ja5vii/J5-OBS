filepath = r'e:\GitHub\J5-OBS\instance-manager\database.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """            async with self.pool.acquire() as conn:
                await conn.execute(SCHEMA)"""

replacement = """            async with self.pool.acquire() as conn:
                await conn.execute(SCHEMA)
                try: await conn.execute("ALTER TABLE instances ADD COLUMN platform VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN rtmp_url VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN rtmp_key VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN connection_id VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN auto_stop BOOLEAN DEFAULT true;")
                except Exception: pass"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected ALTER TABLE")
else:
    print("Target not found")
