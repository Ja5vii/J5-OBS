import os

with open(r'e:\GitHub\J5-OBS\instance-manager\database.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_schema = """CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    token TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS instances (
    instance_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT,
    status TEXT NOT NULL DEFAULT 'STANDBY',
    pid INTEGER,
    display INTEGER,
    websocket_port INTEGER,
    ws_password TEXT,
    rtmp_url TEXT,
    rtmp_key TEXT,
    connection_id TEXT,
    platform TEXT,
    profile TEXT,
    scene_collection TEXT,
    restart_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id TEXT,
    action TEXT NOT NULL,
    target TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL
);
"""

content = content.split('SCHEMA = """')[0] + 'SCHEMA = """\n' + new_schema + '"""\n' + content.split('"""\n\n\nclass Database:')[1]

audit_method = """

    async def log_audit_event(self, actor_id, action, target=None, metadata=None):
        import json
        now = datetime.now(timezone.utc).isoformat()
        meta_str = json.dumps(metadata) if metadata else None
        await self._db.execute(
            "INSERT INTO audit_logs (actor_id, action, target, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (actor_id, action, target, meta_str, now)
        )
        await self._db.commit()

    async def get_audit_logs(self, limit=100):
        cursor = await self._db.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
"""

content = content.replace("    async def close(self):", audit_method + "\n    async def close(self):")

content = content.replace(
    "async def create_instance(self, instance_id, name, owner_id=None, display=0, websocket_port=4455, ws_password=\"\", profile=\"\", scene_collection=\"\"):", 
    "async def create_instance(self, instance_id, name, owner_id=None, display=0, websocket_port=4455, ws_password=\"\", profile=\"\", scene_collection=\"\", connection_id=\"\", platform=\"\"):"
)

content = content.replace(
    "(instance_id, name, owner_id, display, websocket_port, ws_password, profile, scene_collection, now, now),",
    "(instance_id, name, owner_id, display, websocket_port, ws_password, profile, scene_collection, connection_id, platform, now, now),"
)

content = content.replace(
    "INSERT INTO instances (instance_id, name, owner_id, status, display, websocket_port, ws_password, profile, scene_collection, created_at, updated_at) VALUES (?, ?, ?, 'STANDBY', ?, ?, ?, ?, ?, ?, ?)",
    "INSERT INTO instances (instance_id, name, owner_id, status, display, websocket_port, ws_password, profile, scene_collection, connection_id, platform, created_at, updated_at) VALUES (?, ?, ?, 'STANDBY', ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

with open(r'e:\GitHub\J5-OBS\instance-manager\database.py', 'w', encoding='utf-8') as f:
    f.write(content)
