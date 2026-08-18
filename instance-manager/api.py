import os
import time
import hmac
import json
from functools import wraps
from aiohttp import web


class RateLimiter:
    __slots__ = ("max_per_minute", "_requests")

    def __init__(self, max_per_minute=120):
        self.max_per_minute = max_per_minute
        self._requests = {}

    def check(self, key):
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []
        bucket = self._requests[key]
        cutoff = now - 60
        if bucket and bucket[0] < cutoff:
            bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= self.max_per_minute:
            return False
        bucket.append(now)
        return True


def require_auth(manager):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(request):
            provided = request.headers.get("Authorization", "")
            if provided.startswith("Bearer "):
                provided = provided[7:]
            else:
                provided = request.headers.get("X-Auth-Token", "")
            
            env_token = manager.config.get()["manager"]["token"]
            
            if env_token and hmac.compare_digest(provided, env_token):
                request["user"] = {"id": "admin-env", "role": "admin"}
                return await handler(request)
            
            db_user = await manager.db.get_user_by_token(provided)
            if db_user:
                request["user"] = db_user
                return await handler(request)

            return web.json_response({"error": "Unauthorized"}, status=401)
        return wrapper
    return decorator


def require_admin(handler):
    @wraps(handler)
    async def wrapper(request):
        if request["user"]["role"] != "admin":
            return web.json_response({"error": "Forbidden"}, status=403)
        return await handler(request)
    return wrapper


def create_api_app(manager):
    app = web.Application(middlewares=[], client_max_size=1048576)
    limiter = RateLimiter(manager.config.get()["security"]["rate_limit_per_minute"])

    @web.middleware
    async def rate_limit(request, handler):
        key = f"{request.remote or 'x'}:{request.path}"
        if not limiter.check(key):
            return web.json_response({"error": "Rate limit exceeded"}, status=429)
        return await handler(request)

    app.middlewares.append(rate_limit)
    auth = require_auth(manager)

    async def login(request):
        data = await request.json()
        import hashlib
        username = data.get("username", "")
        password = data.get("password", "")
        if not username or not password:
            return web.json_response({"error": "Username and password required"}, status=400)
        
        user = await manager.db.get_user_by_username(username)
        if not user:
            return web.json_response({"error": "Invalid credentials"}, status=401)
            
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if not hmac.compare_digest(user["password_hash"], pw_hash):
            return web.json_response({"error": "Invalid credentials"}, status=401)
            
        import secrets
        token = secrets.token_hex(32)
        await manager.db.update_user(user["id"], token=token)
        return web.json_response({"token": token, "user": {"id": user["id"], "username": user["username"], "role": user["role"]}})

    @auth
    async def check_auth_status(request):
        return web.json_response({"user": {"id": request["user"]["id"], "role": request["user"]["role"]}})

    @auth
    @require_admin
    async def list_users(request):
        users = await manager.db.get_all_users()
        return web.json_response({"users": users})

    @auth
    @require_admin
    async def create_user(request):
        data = await request.json()
        import hashlib, uuid
        pw_hash = hashlib.sha256(data["password"].encode()).hexdigest()
        uid = f"u-{uuid.uuid4().hex[:8]}"
        try:
            user = await manager.db.create_user(uid, data["username"], pw_hash, data.get("role", "user"))
            user.pop("password_hash", None)
            user.pop("token", None)
            return web.json_response(user)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    @auth
    @require_admin
    async def delete_user(request):
        await manager.db.delete_user(request.match_info["id"])
        return web.json_response({"ok": True})

    @auth
    async def list_instances(request):
        if request["user"]["role"] != "admin":
            instances = await manager.db.get_instances_by_owner(request["user"]["id"])
        else:
            instances = await manager.db.get_all_instances()
        return web.json_response({"instances": instances})

    @auth
    @require_admin
    async def create_instance(request):
        data = await request.json()
        name = data.get("name", "").strip()
        if not name:
            return web.json_response({"error": "Name required"}, status=400)
        try:
            inst = await manager.create_instance(name, template=data.get("template"), owner_id=data.get("owner_id"))
            return web.json_response(inst, status=201)
        except RuntimeError as e:
            return web.json_response({"error": str(e)}, status=400)

    async def _check_access(request, instance_id):
        inst = await manager.db.get_instance(instance_id)
        if not inst: return None
        if request["user"]["role"] != "admin" and inst["owner_id"] != request["user"]["id"]:
            return None
        return inst

    @auth
    async def get_instance(request):
        inst = await _check_access(request, request.match_info["id"])
        return web.json_response(inst) if inst else web.json_response({"error": "Not found"}, status=404)

    @auth
    @require_admin
    async def delete_instance(request):
        try:
            await manager.delete_instance(request.match_info["id"])
            return web.json_response({"ok": True})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    @auth
    async def start_instance(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response({"error": "Not found or Forbidden"}, status=403)
        try:
            return web.json_response(await manager.start_instance(request.match_info["id"]))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @auth
    async def stop_instance(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response({"error": "Not found or Forbidden"}, status=403)
        try:
            return web.json_response(await manager.stop_instance(request.match_info["id"]))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    @auth
    async def restart_instance(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response({"error": "Not found or Forbidden"}, status=403)
        try:
            return web.json_response(await manager.restart_instance(request.match_info["id"]))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    @auth
    async def get_stats(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response({"error": "Not found or Forbidden"}, status=403)
        s = await manager.health_manager.get_stats(request.match_info["id"])
        return web.json_response(s) if s else web.json_response({"error": "Not found"}, status=404)

    @auth
    async def get_all_stats(request):
        if request["user"]["role"] != "admin":
            instances = await manager.db.get_instances_by_owner(request["user"]["id"])
        else:
            instances = await manager.db.get_all_instances()
        stats = []
        for inst in instances:
            s = await manager.health_manager.get_stats(inst["instance_id"])
            if s:
                stats.append(s)
        return web.json_response({"instances": stats})

    @auth
    async def update_config(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response({"error": "Not found or Forbidden"}, status=403)
        data = await request.json()
        allowed = {"name", "rtmp_url", "rtmp_key", "profile", "scene_collection"}
        if request["user"]["role"] == "admin":
            allowed.add("owner_id")
        updates = {k: v for k, v in data.items() if k in allowed}
        if updates:
            await manager.db.update_instance(request.match_info["id"], **updates)
        return web.json_response(await manager.db.get_instance(request.match_info["id"]))

    @auth
    async def manager_status(request):
        instances = await manager.db.get_all_instances()
        active = sum(1 for i in instances if i["status"] in ("ONLINE", "STREAMING"))
        return web.json_response({
            "manager": "running",
            "total": len(instances),
            "active": active,
            "standby": len(instances) - active,
            "user": request["user"]
        })

    @auth
    async def list_templates(request):
        return web.json_response({"templates": list(manager._load_templates().values())})
        
    @auth
    async def update_me(request):
        data = await request.json()
        updates = {}
        if data.get("username"): updates["username"] = data["username"]
        if data.get("password"):
            import hashlib
            updates["password_hash"] = hashlib.sha256(data["password"].encode()).hexdigest()
        if updates:
            try:
                await manager.db.update_user(request["user"]["id"], **updates)
            except Exception as e:
                return web.json_response({"error": str(e)}, status=400)
        return web.json_response({"ok": True})

    app.router.add_post("/api/auth/login", login)
    app.router.add_get("/api/status", manager_status)
    app.router.add_get("/api/users", list_users)
    app.router.add_post("/api/users", create_user)
    app.router.add_delete("/api/users/{id}", delete_user)
    app.router.add_put("/api/users/me", update_me)
    
    app.router.add_get("/api/instances", list_instances)
    app.router.add_post("/api/instances", create_instance)
    app.router.add_get("/api/instances/{id}", get_instance)
    app.router.add_delete("/api/instances/{id}", delete_instance)
    app.router.add_post("/api/instances/{id}/start", start_instance)
    app.router.add_post("/api/instances/{id}/stop", stop_instance)
    app.router.add_post("/api/instances/{id}/restart", restart_instance)
    app.router.add_get("/api/instances/{id}/stats", get_stats)
    app.router.add_get("/api/stats", get_all_stats)
    app.router.add_patch("/api/instances/{id}", update_config)
    app.router.add_get("/api/templates", list_templates)

    panel = os.path.join(manager.base_dir, "panel", "index.html")
    if os.path.exists(panel):
        async def _panel(r): return web.FileResponse(panel)
        app.router.add_get("/", _panel)
        app.router.add_get("/panel", _panel)

    return app
