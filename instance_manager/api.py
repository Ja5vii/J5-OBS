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


def require_auth(config):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(request):
            token = config.get()["manager"]["token"]
            if not token:
                return await handler(request)
            provided = request.headers.get("Authorization", "")
            if provided.startswith("Bearer "):
                provided = provided[7:]
            else:
                provided = request.headers.get("X-Auth-Token", "")
            if not provided or not hmac.compare_digest(provided, token):
                return web.json_response({"error": "Unauthorized"}, status=401)
            return await handler(request)
        return wrapper
    return decorator


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
    auth = require_auth(manager.config)

    @auth
    async def list_instances(request):
        oid = request.query.get("owner_id")
        instances = await manager.db.get_instances_by_owner(oid) if oid else await manager.db.get_all_instances()
        return web.json_response({"instances": instances})

    @auth
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

    @auth
    async def get_instance(request):
        inst = await manager.db.get_instance(request.match_info["id"])
        return web.json_response(inst) if inst else web.json_response({"error": "Not found"}, status=404)

    @auth
    async def delete_instance(request):
        try:
            await manager.delete_instance(request.match_info["id"])
            return web.json_response({"ok": True})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    @auth
    async def start_instance(request):
        try:
            return web.json_response(await manager.start_instance(request.match_info["id"]))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    @auth
    async def stop_instance(request):
        try:
            return web.json_response(await manager.stop_instance(request.match_info["id"]))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    @auth
    async def restart_instance(request):
        try:
            return web.json_response(await manager.restart_instance(request.match_info["id"]))
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    @auth
    async def get_stats(request):
        s = await manager.health_manager.get_stats(request.match_info["id"])
        return web.json_response(s) if s else web.json_response({"error": "Not found"}, status=404)

    @auth
    async def get_all_stats(request):
        instances = await manager.db.get_all_instances()
        stats = []
        for inst in instances:
            s = await manager.health_manager.get_stats(inst["instance_id"])
            if s:
                stats.append(s)
        return web.json_response({"instances": stats})

    @auth
    async def update_config(request):
        inst = await manager.db.get_instance(request.match_info["id"])
        if not inst:
            return web.json_response({"error": "Not found"}, status=404)
        data = await request.json()
        allowed = {"name", "rtmp_url", "rtmp_key", "profile", "scene_collection", "owner_id"}
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
        })

    @auth
    async def list_templates(request):
        return web.json_response({"templates": list(manager._load_templates().values())})

    app.router.add_get("/api/status", manager_status)
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
