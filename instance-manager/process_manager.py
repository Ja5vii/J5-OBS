import os
import sys
import asyncio
import subprocess
import json
import signal


class ProcessManager:
    __slots__ = ("manager", "config", "logger", "_processes", "_pulse_processes", "_is_unix")

    def __init__(self, manager, config, logger):
        self.manager = manager
        self.config = config
        self.logger = logger
        self._processes = {}
        self._pulse_processes = {}
        self._is_unix = sys.platform != "win32"

    def initialize(self):
        pass

    def _dir(self, instance_id):
        return os.path.join(self.manager.base_dir, "instances", instance_id)

    def _ensure_dirs(self, instance_id):
        base = self._dir(instance_id)
        for d in ("config", "profiles", "scenes", "logs", "cache", "runtime"):
            os.makedirs(os.path.join(base, d), exist_ok=True)

    def _start_pulseaudio(self, instance_id, inst_dir):
        runtime_dir = os.path.join(inst_dir, "runtime")
        log_dir = os.path.join(inst_dir, "logs")
        pa_config = os.path.join(runtime_dir, "pulse.pa")
        socket_path = os.path.join(runtime_dir, "pulse-socket")
        pid_file = os.path.join(runtime_dir, "pulse.pid")

        with open(pa_config, "w") as f:
            f.write(f"load-module module-native-protocol-unix auth-anonymous=1 socket={socket_path}\n")
            f.write("load-module module-always-sink\n")
            f.write("load-module module-null-sink sink_name=Virtual_Sink sink_properties=device.description=Virtual_Sink\n")
            f.write("load-module module-null-sink sink_name=Virtual_Mic sink_properties=device.description=Virtual_Mic\n")

        log_fh = open(os.path.join(log_dir, "pulse.log"), "a")
        cmd = [
            "pulseaudio",
            "--daemonize=false",
            "--exit-idle-time=-1",
            "-n",
            "-F", pa_config,
            "-p", runtime_dir,
            f"--pid-file={pid_file}"
        ]
        proc = subprocess.Popen(cmd, stdout=log_fh, stderr=log_fh, cwd=inst_dir)
        self._pulse_processes[instance_id] = {"process": proc, "log_file": log_fh, "socket": socket_path}
        return socket_path

    def _stop_pulseaudio(self, instance_id):
        pi = self._pulse_processes.pop(instance_id, None)
        if pi:
            proc = pi["process"]
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            pi["log_file"].close()


    async def start_instance(self, instance_id):

        # [J5 GLOBAL BRANDING] Tamper Protection Check
        try:
            branding = await self.manager.db.get_active_branding()
            if not branding:
                self.logger.error(f"TAMPER DETECTED: No mandatory branding configured for {instance_id}")
                await self.manager.db.log_audit_event("SYSTEM", "BRANDING_TAMPER_DETECTED", instance_id)
                await self.manager.db.update_instance(instance_id, status="ERROR")
                raise ValueError("J5 OBS branding package unavailable. Please try again.")
            
            # Here we would normally verify the signature hash
            # If invalid: raise ValueError("Invalid branding signature")
            
            # Export branding config to a JSON file for the internal OBS websocket client to inject
            inst_dir = self._dir(instance_id)
            import json
            import os
            self._ensure_dirs(instance_id)
            with open(os.path.join(inst_dir, "j5_branding.json"), "w", encoding="utf-8") as bf:
                if isinstance(branding["config_json"], str):
                    json.dump(json.loads(branding["config_json"]), bf)
                else:
                    json.dump(branding["config_json"], bf)
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Branding validation failed: {e}")
            await self.manager.db.update_instance(instance_id, status="ERROR")
            raise ValueError("J5 OBS branding package validation failed.")
        inst = await self.manager.db.get_instance(instance_id)
        if not inst:
            raise ValueError(f"Instance {instance_id} not found")
        await self.manager.db.update_instance(instance_id, status="STARTING")
        self.logger.info(f"Starting {instance_id}...")
        self._ensure_dirs(instance_id)
        inst_dir = self._dir(instance_id)
        config_dir = os.path.join(inst_dir, "config")
        profile_dir = os.path.join(inst_dir, "profiles")
        scene_dir = os.path.join(inst_dir, "scenes")
        log_dir = os.path.join(inst_dir, "logs")
        self._write_obs_config(instance_id, profile_dir, scene_dir, inst)
        self.manager.display_manager.start_xvfb(instance_id)
        display_env = self.manager.display_manager.get_display_env(instance_id)
        pulse_socket = None
        if self._is_unix:
            pulse_socket = self._start_pulseaudio(instance_id, inst_dir)
        await asyncio.sleep(0.5)
        profile_name = inst.get("profile", "default") or "default"
        obs_cmd = [
            "obs",
            "--startintrouhiding",
            "--multiplatform",
            "--portable",
            "--profile", os.path.join(profile_dir, profile_name),
            "--collection", inst.get("scene_collection", "Main"),
            "--scene", "Main",
            "--startstreaming",
        ]
        env = os.environ.copy()
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env["GALLIUM_DRIVER"] = "llvmpipe"
        env.update(display_env)
        if pulse_socket:
            env["PULSE_SERVER"] = f"unix:{pulse_socket}"
        env["OBS_WEBSOCKET_ENABLE"] = "true"
        env["OBS_WEBSOCKET_PORT"] = str(inst["websocket_port"])
        env["OBS_WEBSOCKET_SERVER_PASSWORD"] = inst.get("ws_password", "")
        env["OBS_WEBSOCKET_AUTO_START"] = "true"
        env["OBS_STUDIO_DISABLE_SOURCE_CHROME"] = "1"
        env["OBS_DISABLE_PLUGINS"] = "1"
        log_fh = open(os.path.join(log_dir, "obs.log"), "a")
        popen_kw = {"stdout": log_fh, "stderr": log_fh, "env": env, "cwd": inst_dir}
        if self._is_unix:
            popen_kw["preexec_fn"] = os.setsid
        try:
            proc = subprocess.Popen(obs_cmd, **popen_kw)
        except Exception as e:
            log_fh.close()
            await self.manager.db.update_instance(instance_id, status="ERROR")
            raise RuntimeError(f"Failed to start OBS: {e}")
        self._processes[instance_id] = {"process": proc, "log_file": log_fh}
        await self.manager.db.update_instance(instance_id, pid=proc.pid, status="ONLINE")
        self.logger.info(f"{instance_id} started (PID: {proc.pid})")

    async def stop_instance(self, instance_id):
        inst = await self.manager.db.get_instance(instance_id)
        if not inst:
            return
        await self.manager.db.update_instance(instance_id, status="STOPPING")
        self.logger.info(f"Stopping {instance_id}...")
        proc_info = self._processes.pop(instance_id, None)
        if proc_info:
            proc = proc_info["process"]
            if proc.poll() is None:
                if self._is_unix:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except (ProcessLookupError, PermissionError):
                        proc.terminate()
                else:
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if self._is_unix:
                        try:
                            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                        except (ProcessLookupError, PermissionError):
                            proc.kill()
                    else:
                        proc.kill()
            proc_info["log_file"].close()
        self.manager.display_manager.stop_xvfb(instance_id)
        if self._is_unix:
            self._stop_pulseaudio(instance_id)
        await self.manager.db.update_instance(instance_id, pid=None, status="STANDBY", restart_count=0)
        self.logger.info(f"{instance_id} stopped")

    def is_running(self, instance_id):
        pi = self._processes.get(instance_id)
        return pi is not None and pi["process"].poll() is None

    def get_pid(self, instance_id):
        pi = self._processes.get(instance_id)
        return pi["process"].pid if pi else None

    def _write_obs_config(self, instance_id, profile_dir, scene_dir, inst_data):
        profile_name = inst_data.get("profile", "default") or "default"
        scene_collection = inst_data.get("scene_collection", "Main")
        profile_path = os.path.join(profile_dir, profile_name)
        os.makedirs(profile_path, exist_ok=True)
        basic_ini = os.path.join(profile_path, "basic.ini")
        if not os.path.exists(basic_ini):
            with open(basic_ini, "w") as f:
                f.write(f"[General]\nName={instance_id}\n[Output]\nFilenameFormatting=%CCYY-%MM-%DD %hh-%mm-%ss\n")
        
        rtmp_url = inst_data.get("rtmp_url")
        rtmp_key = inst_data.get("rtmp_key")
        if rtmp_url and rtmp_key:
            service_json = os.path.join(profile_path, "service.json")
            with open(service_json, "w") as f:
                json.dump({
                    "settings": {
                        "key": rtmp_key,
                        "server": rtmp_url,
                        "service": "Custom"
                    },
                    "type": "rtmp_custom"
                }, f)

        connection_id = inst_data.get("connection_id")

        scene_col_path = os.path.join(scene_dir, f"{scene_collection}.json")
        if not os.path.exists(scene_col_path):
            scene_data = {
                "current_program_scene": "Main",
                "current_scene": "Main",
                "name": scene_collection,
                "sources": [
                    {
                        "id": "scene",
                        "name": "Main",
                        "settings": {
                            "items": []
                        }
                    }
                ]
            }
            if connection_id:
                scene_data["sources"][0]["settings"]["items"].append({
                    "name": "J5_Ingest",
                    "visible": True
                })
                scene_data["sources"].append({
                    "id": "ffmpeg_source",
                    "name": "J5_Ingest",
                    "settings": {
                        "input": f"rtmp://127.0.0.1:1935/live/{connection_id}",
                        "is_local_file": False,
                        "hw_decode": True,
                        "clear_on_media_end": True
                    }
                })
                
            with open(scene_col_path, "w") as f:
                json.dump(scene_data, f, indent=2)

