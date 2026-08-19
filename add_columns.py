filepath = r'e:\GitHub\J5-OBS\instance-manager\database.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    restart_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,"""

replacement = """    restart_count INTEGER DEFAULT 0,
    platform VARCHAR(255),
    rtmp_url VARCHAR(255),
    rtmp_key VARCHAR(255),
    connection_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,"""

if target in content:
    content = content.replace(target, replacement)
    
    # Add migration script to init_db
    init_target = """        async with self.pool.acquire() as conn:
            await conn.execute(SCHEMA)"""
    init_replacement = """        async with self.pool.acquire() as conn:
            await conn.execute(SCHEMA)
            # Migrations
            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN platform VARCHAR(255);")
            except Exception: pass
            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN rtmp_url VARCHAR(255);")
            except Exception: pass
            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN rtmp_key VARCHAR(255);")
            except Exception: pass
            try:
                await conn.execute("ALTER TABLE instances ADD COLUMN connection_id VARCHAR(255);")
            except Exception: pass"""
    content = content.replace(init_target, init_replacement)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added columns to schema")
else:
    print("Target not found")
