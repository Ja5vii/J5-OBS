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

CREATE TABLE IF NOT EXISTS platforms (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rtmp_url VARCHAR(255) NOT NULL
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
    auto_stop BOOLEAN DEFAULT true,
    restart_count INTEGER DEFAULT 0,
    platform VARCHAR(255),
    rtmp_url VARCHAR(255),
    rtmp_key VARCHAR(255),
    connection_id VARCHAR(255),
    twitch_channel VARCHAR(255),
    public_enabled BOOLEAN DEFAULT false,
    public_channel_name VARCHAR(255),
    public_category VARCHAR(255),
    public_stream_title VARCHAR(255),
    featured BOOLEAN DEFAULT false,
    stream_active BOOLEAN DEFAULT false,
    stream_mode VARCHAR(20) DEFAULT 'relay',
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

CREATE TABLE IF NOT EXISTS connections (
    connection_id VARCHAR(255) PRIMARY KEY,
    instance_id VARCHAR(255) NOT NULL UNIQUE,
    ingest_url VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'DISCONNECTED',
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
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

CREATE TABLE IF NOT EXISTS branding_versions (
    id VARCHAR(255) PRIMARY KEY,
    version_tag VARCHAR(50) NOT NULL,
    config_json JSONB NOT NULL,
    signature VARCHAR(255),
    is_active BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS branding_assets (
    id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    url VARCHAR(500),
    checksum VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL
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
                try: await conn.execute("ALTER TABLE instances ADD COLUMN platform VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN rtmp_url VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN rtmp_key VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN connection_id VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN auto_stop BOOLEAN DEFAULT true;")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN twitch_channel VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN public_enabled BOOLEAN DEFAULT false;")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN public_channel_name VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN public_category VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN public_stream_title VARCHAR(255);")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN featured BOOLEAN DEFAULT false;")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN stream_active BOOLEAN DEFAULT false;")
                except Exception: pass
                try: await conn.execute("ALTER TABLE instances ADD COLUMN stream_mode VARCHAR(20) DEFAULT 'relay';")
                except Exception: pass
                await self._seed_platforms(conn)
                await self._seed_roles_and_admin(conn)
                # Reset all instances to STANDBY on boot since processes are dead
                await conn.execute("UPDATE instances SET status = 'STANDBY', pid = NULL")
        except Exception as e:
            print(f"Failed to initialize PostgreSQL: {e}")
            raise

    async def _seed_platforms(self, conn):
        platforms = [
            ("Twitch",   "Twitch (Global)", "rtmps://ingest.global-contribute.live-video.net/app/"),
            ("TwitchES", "Twitch (Espana)",  "rtmps://mad02.contribute.live-video.net/app/"),
            ("YouTube",  "YouTube",          "rtmps://a.rtmp.youtube.com/live2/"),
            ("Kick",     "Kick",             "rtmps://fa723fc1b171.global-contribute.live-video.net/app"),
            ("Custom",   "Custom RTMP",      ""),
        ]
        for pid, pname, purl in platforms:
            await conn.execute(
                "INSERT INTO platforms (id, name, rtmp_url) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                pid, pname, purl
            )

    async def _seed_roles_and_admin(self, conn):
        import hashlib
        await conn.execute("INSERT INTO roles (id, name) VALUES ('admin', 'Administrator') ON CONFLICT DO NOTHING")
        await conn.execute("INSERT INTO roles (id, name) VALUES ('user', 'User') ON CONFLICT DO NOTHING")
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
                SELECT i.*, o.user_id as owner_id, c.connection_id, cred.custom_rtmp_url as rtmp_url, cred.encrypted_stream_key as rtmp_key, cred.platform_id as platform
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
                SELECT i.*, o.user_id as owner_id, c.connection_id, cred.custom_rtmp_url as rtmp_url, cred.encrypted_stream_key as rtmp_key, cred.platform_id as platform
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
        # Note: twitch_channel stays in kwargs so it directly updates instances.twitch_channel
        
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

    # --- Public Stream Hub ---
    async def get_public_live_streams(self, platform=None, category=None, search=None):
        async with self.pool.acquire() as conn:
            q = """SELECT i.*, u.username as owner_username
                   FROM instances i
                   LEFT JOIN instance_owners io ON i.instance_id = io.instance_id
                   LEFT JOIN users u ON io.user_id = u.id
                   WHERE i.public_enabled = true AND i.stream_active = true"""
            params = []
            if platform:
                params.append(platform)
                q += f" AND i.platform = ${len(params)}"
            if category:
                params.append(f'%{category}%')
                q += f" AND i.public_category ILIKE ${len(params)}"
            if search:
                params.append(f'%{search}%')
                q += f" AND (i.public_channel_name ILIKE ${len(params)} OR i.name ILIKE ${len(params)})"
            q += " ORDER BY i.featured DESC, i.updated_at DESC"
            rows = await conn.fetch(q, *params)
            return [dict(r) for r in rows]

    async def get_public_channel(self, channel_name):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM instances WHERE LOWER(public_channel_name) = LOWER($1) AND public_enabled = true",
                channel_name
            )
            return dict(row) if row else None

    async def update_instance_public(self, instance_id, **fields):
        allowed = {'public_enabled', 'public_channel_name', 'public_category', 'public_stream_title', 'featured', 'stream_mode', 'stream_active'}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        updates['updated_at'] = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            set_clause = ', '.join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
            values = list(updates.values())
            await conn.execute(
                f"UPDATE instances SET {set_clause} WHERE instance_id = $1",
                instance_id, *values
            )


    async def get_active_branding(self):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM branding_versions WHERE is_active = true ORDER BY published_at DESC LIMIT 1")
            return dict(row) if row else None

    async def publish_branding(self, version_id, version_tag, config_json, signature):
        now = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Set all existing to inactive
                await conn.execute("UPDATE branding_versions SET is_active = false")
                # Insert the new active one
                import json
                await conn.execute(
                    "INSERT INTO branding_versions (id, version_tag, config_json, signature, is_active, published_at) VALUES ($1, $2, $3, $4, true, $5)",
                    version_id, version_tag, json.dumps(config_json), signature, now
                )

    async def get_all_branding_versions(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, version_tag, signature, is_active, published_at FROM branding_versions ORDER BY published_at DESC")
            return [dict(r) for r in rows]

    async def save_asset(self, asset_id, filename, url, checksum):
        now = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO branding_assets (id, filename, url, checksum, uploaded_at) VALUES ($1, $2, $3, $4, $5)",
                asset_id, filename, url, checksum, now
            )
            
    async def get_all_assets(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM branding_assets ORDER BY uploaded_at DESC")
            return [dict(r) for r in rows]
