import os
import time
import hmac
import json
from functools import wraps
from aiohttp import web
import json
import functools
custom_dumps = functools.partial(json.dumps, default=str)



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

            return web.json_response(dumps=custom_dumps, data={"error": "Unauthorized"}, status=401)
        return wrapper
    return decorator


def require_admin(handler):
    @wraps(handler)
    async def wrapper(request):
        if request["user"]["role"] != "admin":
            return web.json_response(dumps=custom_dumps, data={"error": "Forbidden"}, status=403)
        return await handler(request)
    return wrapper


def create_api_app(manager):
    app = web.Application(middlewares=[], client_max_size=1048576)
    limiter = RateLimiter(manager.config.get()["security"]["rate_limit_per_minute"])

    @web.middleware
    async def rate_limit(request, handler):
        key = f"{request.remote or 'x'}:{request.path}"
        if not limiter.check(key):
            return web.json_response(dumps=custom_dumps, data={"error": "Rate limit exceeded"}, status=429)
        return await handler(request)

    app.middlewares.append(rate_limit)
    auth = require_auth(manager)

    async def login(request):
        data = await request.json()
        import hashlib
        username = data.get("username", "")
        password = data.get("password", "")
        if not username or not password:
            return web.json_response(dumps=custom_dumps, data={"error": "Username and password required"}, status=400)
        
        user = await manager.db.get_user_by_username(username)
        if not user:
            return web.json_response(dumps=custom_dumps, data={"error": "Invalid credentials"}, status=401)
            
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if not hmac.compare_digest(user["password_hash"], pw_hash):
            return web.json_response(dumps=custom_dumps, data={"error": "Invalid credentials"}, status=401)
            
        import secrets
        token = secrets.token_hex(32)
        await manager.db.create_session(token, user["id"])
        
        # We can also set a secure cookie if they requested it, but we'll stick to returning it for now.
        return web.json_response(dumps=custom_dumps, data={"token": token, "user": {"id": user["id"], "username": user["username"], "role": user["role"]}})

    @auth
    async def check_auth_status(request):
        return web.json_response(dumps=custom_dumps, data={"user": {"id": request["user"]["id"], "role": request["user"]["role"]}})


    # --- Internal RTMP Hooks ---
    async def internal_on_publish(request):
        data = await request.post()
        connection_id = data.get("name")
        if not connection_id:
            return web.Response(status=400)
            
        manager.logger.info(f"Stream ingest connected: {connection_id}")
        instances = await manager.db.get_all_instances()
        target_inst = next((i for i in instances if i.get("connection_id") == connection_id), None)
        if not target_inst:
            manager.logger.warning(f"Rejecting unknown stream key: {connection_id}")
            return web.Response(status=404)
            
        inst_id = target_inst["instance_id"]
        if not manager.process_manager.is_running(inst_id):
            manager.logger.info(f"Auto-starting instance {inst_id} due to incoming stream")
            import asyncio
            asyncio.create_task(manager.start_instance(inst_id))
            
        return web.Response(status=200)

    async def internal_on_publish_done(request):
        data = await request.post()
        connection_id = data.get("name")
        if not connection_id:
            return web.Response(status=400)
            
        manager.logger.info(f"Stream ingest disconnected: {connection_id}")
        instances = await manager.db.get_all_instances()
        target_inst = next((i for i in instances if i.get("connection_id") == connection_id), None)
        if not target_inst:
            return web.Response(status=404)
            
        inst_id = target_inst["instance_id"]
        if manager.process_manager.is_running(inst_id) and target_inst.get("auto_stop", True):
            manager.logger.info(f"Auto-stopping instance {inst_id} due to stream disconnect")
            import asyncio
            asyncio.create_task(manager.stop_instance(inst_id))
            
        return web.Response(status=200)

    @auth
    @require_admin
    async def list_users(request):
        users = await manager.db.get_all_users()
        return web.json_response(dumps=custom_dumps, data={"users": users})

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
            return web.json_response(dumps=custom_dumps, data=user)
        except Exception as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=400)

    @auth
    @require_admin
    async def delete_user(request):
        await manager.db.delete_user(request.match_info["id"])
        return web.json_response(dumps=custom_dumps, data={"ok": True})

    @auth
    async def list_instances(request):
        if request["user"]["role"] != "admin":
            instances = await manager.db.get_instances_by_owner(request["user"]["id"])
        else:
            instances = await manager.db.get_all_instances()
        return web.json_response(dumps=custom_dumps, data={"instances": instances})

    @auth
    @require_admin
    async def create_instance(request):
        data = await request.json()
        name = data.get("name", "").strip()
        if not name:
            return web.json_response(dumps=custom_dumps, data={"error": "Name required"}, status=400)
        try:
            inst = await manager.create_instance(name, template=data.get("template"), owner_id=data.get("owner_id"))
            return web.json_response(dumps=custom_dumps, data=inst, status=201)
        except RuntimeError as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=400)

    async def _check_access(request, instance_id):
        inst = await manager.db.get_instance(instance_id)
        if not inst: return None
        if request["user"]["role"] != "admin" and inst["owner_id"] != request["user"]["id"]:
            return None
        return inst

    @auth
    async def get_instance(request):
        inst = await _check_access(request, request.match_info["id"])
        return web.json_response(dumps=custom_dumps, data=inst) if inst else web.json_response(dumps=custom_dumps, data={"error": "Not found"}, status=404)

    @auth
    @require_admin
    async def delete_instance(request):
        try:
            await manager.delete_instance(request.match_info["id"])
            return web.json_response(dumps=custom_dumps, data={"ok": True})
        except ValueError as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=404)

    @auth
    async def start_instance(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response(dumps=custom_dumps, data={"error": "Not found or Forbidden"}, status=403)
        try:
            res = await manager.start_instance(request.match_info["id"])
            await manager.db.log_audit_event(request["user"]["id"], "START_INSTANCE", request.match_info["id"])
            return web.json_response(dumps=custom_dumps, data=res)
        except ValueError as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=404)
        except Exception as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=500)

    @auth
    async def stop_instance(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response(dumps=custom_dumps, data={"error": "Not found or Forbidden"}, status=403)
        try:
            res = await manager.stop_instance(request.match_info["id"])
            await manager.db.log_audit_event(request["user"]["id"], "STOP_INSTANCE", request.match_info["id"])
            return web.json_response(dumps=custom_dumps, data=res)
        except ValueError as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=404)

    @auth
    async def restart_instance(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response(dumps=custom_dumps, data={"error": "Not found or Forbidden"}, status=403)
        try:
            return web.json_response(dumps=custom_dumps, data=await manager.restart_instance(request.match_info["id"]))
        except ValueError as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=404)

    @auth
    async def get_stats(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response(dumps=custom_dumps, data={"error": "Not found or Forbidden"}, status=403)
        s = await manager.health_manager.get_stats(request.match_info["id"])
        return web.json_response(dumps=custom_dumps, data=s) if s else web.json_response(dumps=custom_dumps, data={"error": "Not found"}, status=404)

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
        return web.json_response(dumps=custom_dumps, data={"instances": stats})

    @auth
    async def update_config(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response(dumps=custom_dumps, data={"error": "Not found or Forbidden"}, status=403)
        data = await request.json()
        allowed = {"name", "rtmp_url", "rtmp_key", "profile", "scene_collection", "auto_stop"}
        if request["user"]["role"] == "admin":
            allowed.add("owner_id")
        updates = {k: v for k, v in data.items() if k in allowed}
        if updates:
            await manager.db.update_instance(request.match_info["id"], **updates)
        return web.json_response(dumps=custom_dumps, data=await manager.db.get_instance(request.match_info["id"]))


    @auth
    @require_admin
    async def get_audit_logs(request):
        logs = await manager.db.get_audit_logs()
        return web.json_response(dumps=custom_dumps, data={"audit_logs": logs})

    @auth
    async def update_connection(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.json_response(dumps=custom_dumps, data={"error": "Not found or Forbidden"}, status=403)
        data = await request.json()
        import secrets
        
        updates = {}
        if "platform" in data:
            updates["platform"] = data["platform"]
        if "rtmp_key" in data:
            updates["rtmp_key"] = data["rtmp_key"]
        if "auto_stop" in data:
            updates["auto_stop"] = data["auto_stop"]
            
        # Optional custom RTMP
        if "rtmp_url" in data:
            updates["rtmp_url"] = data["rtmp_url"]
        else:
            # Generate automatically based on platform if needed, or leave empty if it's twitch, wait OBS needs full URL if it's custom.
            # But we are using service.json type "rtmp_custom". So rtmp_url is required.
            pass
            
        # Generate connection ID if it doesn't exist
        inst = await manager.db.get_instance(request.match_info["id"])
        if not inst.get("connection_id"):
            updates["connection_id"] = f"j5_{request['user']['username']}_{secrets.token_hex(4)}"

        if updates:
            await manager.db.update_instance(request.match_info["id"], **updates)
            await manager.db.log_audit_event(request["user"]["id"], "UPDATE_CONNECTION", request.match_info["id"], updates)

        return web.json_response(dumps=custom_dumps, data=await manager.db.get_instance(request.match_info["id"]))

    @auth
    async def manager_status(request):
        instances = await manager.db.get_all_instances()
        active = sum(1 for i in instances if i["status"] in ("ONLINE", "STREAMING"))
        return web.json_response(dumps=custom_dumps, data={
            "manager": "running",
            "total": len(instances),
            "active": active,
            "standby": len(instances) - active,
            "user": request["user"]
        })

    @auth
    async def list_templates(request):
        return web.json_response(dumps=custom_dumps, data={"templates": list(manager._load_templates().values())})
        
    @auth
    async def update_me(request):
        data = await request.json()
        updates = {}
        if data.get("password"):
            import hashlib
            updates["password_hash"] = hashlib.sha256(data["password"].encode()).hexdigest()
        if updates:
            try:
                await manager.db.update_user(request["user"]["id"], **updates)
            except Exception as e:
                return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=400)
        return web.json_response(dumps=custom_dumps, data={"ok": True})


    # --- Global Branding ---
    async def get_active_branding(request):
        try:
            active = await manager.db.get_active_branding()
            if not active:
                return web.json_response(dumps=custom_dumps, data={"error": "No active branding"}, status=404)
            import json
            if isinstance(active["config_json"], str):
                active["config_json"] = json.loads(active["config_json"])
            # Format datetime
            active["published_at"] = active["published_at"].isoformat()
            return web.json_response(dumps=custom_dumps, data=active)
        except Exception as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=500)


    @auth
    @require_admin
    async def upload_branding_logo(request):
        try:
            import base64
            import uuid
            import os
            
            data = await request.json()
            filename = data.get("filename", "logo.png")
            image_data = data.get("image_data", "")
            
            if not image_data:
                return web.json_response(dumps=custom_dumps, data={"error": "No image data provided"}, status=400)
                
            if "," in image_data:
                header, b64_data = image_data.split(",", 1)
            else:
                b64_data = image_data
                
            asset_id = str(uuid.uuid4())
            safe_filename = f"{asset_id}_{filename}"
            
            assets_dir = os.path.join(manager.base_dir, "j5-obs", "branding_assets")
            os.makedirs(assets_dir, exist_ok=True)
            
            file_path = os.path.join(assets_dir, safe_filename)
            
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
                
            await manager.db.save_asset(asset_id, "image", safe_filename, request["user"]["id"])
            
            return web.json_response(dumps=custom_dumps, data={"ok": True, "asset_id": asset_id, "filename": safe_filename})
        except Exception as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=500)

    @auth
    @require_admin
    async def publish_branding(request):
        data = await request.json()
        version_id = data.get("id")
        version_tag = data.get("version_tag")
        config_json = data.get("config_json")
        signature = data.get("signature", "")
        
        if not all([version_id, version_tag, config_json]):
            return web.json_response(dumps=custom_dumps, data={"error": "Missing required fields"}, status=400)
            
        try:
            await manager.db.publish_branding(version_id, version_tag, config_json, signature)
            await manager.db.log_audit_event(request["user"]["id"], "BRANDING_PUBLISHED", version_tag)
            return web.json_response(dumps=custom_dumps, data={"ok": True})
        except Exception as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=500)

    @auth
    @require_admin
    async def get_all_branding_versions(request):
        try:
            versions = await manager.db.get_all_branding_versions()
            for v in versions:
                v["published_at"] = v["published_at"].isoformat()
            return web.json_response(dumps=custom_dumps, data={"versions": versions})
        except Exception as e:
            return web.json_response(dumps=custom_dumps, data={"error": str(e)}, status=500)
    app.router.add_post("/api/auth/login", login)
    app.router.add_get("/api/status", manager_status)
    app.router.add_post("/api/internal/on_publish", internal_on_publish)
    app.router.add_post("/api/internal/on_publish_done", internal_on_publish_done)

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
    app.router.add_get("/api/audit", get_audit_logs)
    app.router.add_patch("/api/instances/{id}/connection", update_connection)
    app.router.add_get("/api/instances/{id}/stats", get_stats)
    app.router.add_get("/api/instances/{id}/log", get_obs_log)
    app.router.add_get("/api/stats", get_all_stats)
    app.router.add_patch("/api/instances/{id}", update_config)
    app.router.add_get("/api/templates", list_templates)

    @auth
    async def get_obs_log(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.Response(status=403)
            
        inst_id = request.match_info["id"]
        log_path = os.path.join(manager.base_dir, "instances", inst_id, "logs", "obs.log")
        if not os.path.exists(log_path):
            return web.Response(status=404, text="Log not found")
            
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Return last 100 lines
        return web.Response(text="".join(lines[-100:]))


    @auth
    async def vnc_proxy(request):
        if not await _check_access(request, request.match_info["id"]):
            return web.Response(status=403)
        
        inst_id = request.match_info["id"]
        display_num = manager.display_manager.get_display(inst_id)
        if not display_num or not manager.process_manager.is_running(inst_id):
            return web.Response(status=404, text="Instance not running or no display")
            
        # x11vnc should be listening on 5900 + display_num
        vnc_port = 5900 + display_num
        
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        import asyncio
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', vnc_port)
        except Exception as e:
            manager.logger.error(f"VNC Connection failed: {e}")
            await ws.close()
            return ws
            
        async def downstream():
            try:
                while True:
                    data = await reader.read(4096)
                    if not data:
                        break
                    await ws.send_bytes(data)
            except Exception:
                pass
            finally:
                await ws.close()
                writer.close()
                
        async def upstream():
            try:
                async for msg in ws:
                    if msg.type == web.WSMsgType.BINARY:
                        writer.write(msg.data)
                        await writer.drain()
            except Exception:
                pass
            finally:
                writer.close()
                
        await asyncio.gather(downstream(), upstream())
        return ws


    app.router.add_get("/api/branding/active", get_active_branding)
    app.router.add_post("/api/admin/branding", publish_branding)
    app.router.add_post("/api/admin/branding/upload", upload_branding_logo)
    app.router.add_get("/api/admin/branding/versions", get_all_branding_versions)
    app.router.add_get("/api/instances/{id}/vnc", vnc_proxy)

    panel_dir = os.path.join(manager.base_dir, "panel")
    if os.path.exists(panel_dir):
        async def _panel(r): return web.FileResponse(os.path.join(panel_dir, "index.html"))
        app.router.add_get("/", _panel)
        app.router.add_get("/panel", _panel)
        app.router.add_static("/panel", panel_dir)

    return app

