import os
import sys
import json
import asyncio
import asyncpg
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    token VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS instances (
    instance_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'STANDBY',
    pid INTEGER,
    display INTEGER,
    websocket_port INTEGER,
    ws_password VARCHAR(255),
    profile VARCHAR(255),
    scene_collection VARCHAR(255),
    restart_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS instance_owners (
    user_id VARCHAR(255) NOT NULL,
    instance_id VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id, instance_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS platforms (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rtmp_url VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS credentials (
    id SERIAL PRIMARY KEY,
    instance_id VARCHAR(255) NOT NULL,
    platform_id VARCHAR(255),
    encrypted_stream_key TEXT NOT NULL,
    custom_rtmp_url VARCHAR(255),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms(id)
);

CREATE TABLE IF NOT EXISTS connections (
    connection_id VARCHAR(255) PRIMARY KEY,
    instance_id VARCHAR(255) NOT NULL UNIQUE,
    ingest_url VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'DISCONNECTED',
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS streams (
    id SERIAL PRIMARY KEY,
    instance_id VARCHAR(255) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    target VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
"""

class Database:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.pool = None
        self.host = os.environ.get("J5_DB_HOST", "localhost")
        self.port = int(os.environ.get("J5_DB_PORT", 5432))
        self.user = os.environ.get("J5_DB_USER", "postgres")
        self.password = os.environ.get("J5_DB_PASS", "postgres")
        self.database = os.environ.get("J5_DB_NAME", "j5obs")

    async def initialize(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=2,
                max_size=10
            )
            async with self.pool.acquire() as conn:
                await conn.execute(SCHEMA)
                await self._seed_roles_and_admin(conn)
        except Exception as e:
            print(f"Failed to initialize PostgreSQL: {e}")
            raise

    async def _seed_roles_and_admin(self, conn):
        import hashlib
        # Roles
        await conn.execute("INSERT INTO roles (id, name) VALUES ('admin', 'Administrator') ON CONFLICT DO NOTHING")
        await conn.execute("INSERT INTO roles (id, name) VALUES ('user', 'User') ON CONFLICT DO NOTHING")
        
        # Admin
        val = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role_id = 'admin'")
        if val == 0:
            default_password = os.environ.get("J5_MANAGER_TOKEN", "admin")
            pw_hash = hashlib.sha256(default_password.encode()).hexdigest()
            now = datetime.now(timezone.utc)
            await conn.execute(
                "INSERT INTO users (id, username, password_hash, role_id, created_at) VALUES ($1, $2, $3, $4, $5)",
                "u-admin", "admin", pw_hash, "admin", now
            )

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def log_audit_event(self, actor_id, action, target=None, metadata=None):
        now = datetime.now(timezone.utc)
        meta_str = json.dumps(metadata) if metadata else None
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO audit_logs (actor_id, action, target, metadata, created_at) VALUES ($1, $2, $3, $4, $5)",
                actor_id, action, target, meta_str, now
            )

    async def get_audit_logs(self, limit=100):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM audit_logs ORDER BY id DESC LIMIT $1", limit)
            return [dict(r) for r in rows]

    # --- Users & Sessions ---
    async def create_user(self, user_id, username, password_hash, role="user"):
        now = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, username, password_hash, role_id, created_at) VALUES ($1, $2, $3, $4, $5)",
                user_id, username, password_hash, role, now
            )
        return await self.get_user(user_id)

    async def get_user(self, user_id):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT id, username, password_hash, role_id as role, created_at FROM users WHERE id = $1", user_id)
            return dict(row) if row else None

    async def get_user_by_username(self, username):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT id, username, password_hash, role_id as role, created_at FROM users WHERE username = $1", username)
            return dict(row) if row else None

    async def create_session(self, token, user_id, expires_in_days=30):
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=expires_in_days)
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES ($1, $2, $3, $4)", token, user_id, now, expires)

    async def get_user_by_token(self, token):
        now = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT u.id, u.username, u.password_hash, u.role_id as role
                FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.token = $1 AND s.expires_at > $2
            """, token, now)
            return dict(row) if row else None

    async def revoke_sessions(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM sessions WHERE user_id = $1", user_id)

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, username, role_id as role, created_at FROM users ORDER BY username")
            return [dict(r) for r in rows]

    async def update_user(self, user_id, **kwargs):
        if not kwargs: return
        set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(kwargs.keys()))
        values = list(kwargs.values())
        values.append(user_id)
        async with self.pool.acquire() as conn:
            await conn.execute(f"UPDATE users SET {set_clause} WHERE id = ${len(values)}", *values)

    async def delete_user(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)

    # --- Instances & Ownership & Credentials ---
    async def create_instance(self, instance_id, name, owner_id=None, display=0, websocket_port=4455, ws_password="", profile="", scene_collection="", connection_id="", platform=""):
        now = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO instances (instance_id, name, status, display, websocket_port, ws_password, profile, scene_collection, created_at, updated_at) VALUES ($1, $2, 'STANDBY', $3, $4, $5, $6, $7, $8, $9)",
                    instance_id, name, display, websocket_port, ws_password, profile, scene_collection, now, now
                )
                if owner_id and owner_id.strip():
                    await conn.execute("INSERT INTO instance_owners (user_id, instance_id) VALUES ($1, $2)", owner_id, instance_id)
                if connection_id:
                    await conn.execute("INSERT INTO connections (connection_id, instance_id, ingest_url) VALUES ($1, $2, $3)", connection_id, instance_id, "rtmp://ingest.ja5vii.com/live")

    async def get_instance(self, instance_id):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT i.*, o.user_id as owner_id, c.connection_id, cred.custom_rtmp_url as rtmp_url, cred.encrypted_stream_key as rtmp_key, cred.platform_id as platform
                FROM instances i
                LEFT JOIN instance_owners o ON i.instance_id = o.instance_id
                LEFT JOIN connections c ON i.instance_id = c.instance_id
                LEFT JOIN credentials cred ON i.instance_id = cred.instance_id
                WHERE i.instance_id = $1
            """, instance_id)
            if row:
                d = dict(row)
                if d.get("rtmp_key"):
                    # Decrypt logic should be here, but for now we just return it
                    pass
                return d
            return None

    async def get_all_instances(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT i.*, o.user_id as owner_id, c.connection_id, cred.custom_rtmp_url as rtmp_url, cred.platform_id as platform
                FROM instances i
                LEFT JOIN instance_owners o ON i.instance_id = o.instance_id
                LEFT JOIN connections c ON i.instance_id = c.instance_id
                LEFT JOIN credentials cred ON i.instance_id = cred.instance_id
                ORDER BY i.instance_id
            """)
            return [dict(r) for r in rows]

    async def get_instances_by_owner(self, owner_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT i.*, o.user_id as owner_id, c.connection_id, cred.custom_rtmp_url as rtmp_url, cred.platform_id as platform
                FROM instances i
                JOIN instance_owners o ON i.instance_id = o.instance_id
                LEFT JOIN connections c ON i.instance_id = c.instance_id
                LEFT JOIN credentials cred ON i.instance_id = cred.instance_id
                WHERE o.user_id = $1
                ORDER BY i.instance_id
            """, owner_id)
            return [dict(r) for r in rows]

    async def update_instance(self, instance_id, **kwargs):
        # Handle relation updates (owner_id, connection_id, platform, rtmp_url, rtmp_key) separately
        owner_id = kwargs.pop("owner_id", None)
        connection_id = kwargs.pop("connection_id", None)
        platform = kwargs.pop("platform", None)
        rtmp_url = kwargs.pop("rtmp_url", None)
        rtmp_key = kwargs.pop("rtmp_key", None)
        
        now = datetime.now(timezone.utc)
        kwargs["updated_at"] = now
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                if kwargs:
                    set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(kwargs.keys()))
                    values = list(kwargs.values())
                    values.append(instance_id)
                    await conn.execute(f"UPDATE instances SET {set_clause} WHERE instance_id = ${len(values)}", *values)
                
                if owner_id is not None:
                    await conn.execute("DELETE FROM instance_owners WHERE instance_id = $1", instance_id)
                    if owner_id and owner_id.strip():
                        await conn.execute("INSERT INTO instance_owners (user_id, instance_id) VALUES ($1, $2)", owner_id, instance_id)
                        
                if connection_id is not None:
                    await conn.execute("INSERT INTO connections (connection_id, instance_id, ingest_url) VALUES ($1, $2, 'rtmp://ingest.ja5vii.com/live') ON CONFLICT (instance_id) DO UPDATE SET connection_id = $1", connection_id, instance_id)
                    
                if rtmp_key is not None or rtmp_url is not None or platform is not None:
                    # Upsert credentials
                    curr = await conn.fetchrow("SELECT * FROM credentials WHERE instance_id = $1", instance_id)
                    curr_platform = platform if platform is not None else (curr["platform_id"] if curr else "Custom")
                    curr_url = rtmp_url if rtmp_url is not None else (curr["custom_rtmp_url"] if curr else "")
                    curr_key = rtmp_key if rtmp_key is not None else (curr["encrypted_stream_key"] if curr else "")
                    
                    if curr:
                        await conn.execute("UPDATE credentials SET platform_id = $1, custom_rtmp_url = $2, encrypted_stream_key = $3 WHERE instance_id = $4", curr_platform, curr_url, curr_key, instance_id)
                    else:
                        await conn.execute("INSERT INTO credentials (instance_id, platform_id, custom_rtmp_url, encrypted_stream_key) VALUES ($1, $2, $3, $4)", instance_id, curr_platform, curr_url, curr_key)

    async def delete_instance(self, instance_id):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM instances WHERE instance_id = $1", instance_id)

