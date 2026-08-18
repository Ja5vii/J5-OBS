import os
import aiosqlite
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
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
    profile TEXT,
    scene_collection TEXT,
    restart_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(id)
);
"""


class Database:
    def __init__(self, base_dir):
        self.db_path = os.path.join(base_dir, "j5-obs", "database", "instances.db")
        self._db = None

    async def initialize(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()
        await self._seed_admin()

    async def _seed_admin(self):
        import hashlib
        import os
        cursor = await self._db.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'")
        row = await cursor.fetchone()
        if row and row['c'] == 0:
            default_password = os.environ.get("J5_MANAGER_TOKEN", "admin")
            pw_hash = hashlib.sha256(default_password.encode()).hexdigest()
            now = datetime.now(timezone.utc).isoformat()
            await self._db.execute(
                "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("u-admin", "admin", pw_hash, "admin", now)
            )
            await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()

    async def create_user(self, user_id, username, password_hash, role="user"):
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, password_hash, role, now)
        )
        await self._db.commit()
        return await self.get_user(user_id)

    async def get_user(self, user_id):
        cursor = await self._db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_username(self, username):
        cursor = await self._db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_user_by_token(self, token):
        cursor = await self._db.execute("SELECT * FROM users WHERE token = ?", (token,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_users(self):
        cursor = await self._db.execute("SELECT id, username, role, created_at FROM users ORDER BY username")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def update_user(self, user_id, **kwargs):
        if not kwargs: return
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [user_id]
        await self._db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        await self._db.commit()

    async def delete_user(self, user_id):
        await self._db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await self._db.execute("UPDATE instances SET owner_id = NULL WHERE owner_id = ?", (user_id,))
        await self._db.commit()

    async def create_instance(self, instance_id, name, owner_id=None, display=0, websocket_port=4455, ws_password="", profile="", scene_collection=""):
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO instances (instance_id, name, owner_id, status, display, websocket_port, ws_password, profile, scene_collection, created_at, updated_at) VALUES (?, ?, ?, 'STANDBY', ?, ?, ?, ?, ?, ?, ?)",
            (instance_id, name, owner_id, display, websocket_port, ws_password, profile, scene_collection, now, now),
        )
        await self._db.commit()

    async def get_instance(self, instance_id):
        cursor = await self._db.execute("SELECT * FROM instances WHERE instance_id = ?", (instance_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_instances(self):
        cursor = await self._db.execute("SELECT * FROM instances ORDER BY instance_id")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_instances_by_owner(self, owner_id):
        cursor = await self._db.execute("SELECT * FROM instances WHERE owner_id = ? ORDER BY instance_id", (owner_id,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def update_instance(self, instance_id, **kwargs):
        kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [instance_id]
        await self._db.execute(f"UPDATE instances SET {set_clause} WHERE instance_id = ?", values)
        await self._db.commit()

    async def delete_instance(self, instance_id):
        await self._db.execute("DELETE FROM instances WHERE instance_id = ?", (instance_id,))
        await self._db.commit()
