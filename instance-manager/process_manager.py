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
        profile_dir = os.path.join(inst_dir, "config", "obs-studio", "basic", "profiles")
        scene_dir = os.path.join(inst_dir, "config", "obs-studio", "basic", "scenes")
        log_dir = os.path.join(inst_dir, "logs")
        global_dir = os.path.join(inst_dir, "config", "obs-studio")
        os.makedirs(global_dir, exist_ok=True)
        with open(os.path.join(global_dir, "global.ini"), "w") as f:
            f.write(f"[OBSWebSocket]\nServerPort={inst.get('websocket_port')}\nServerPassword={inst.get('ws_password', '')}\nServerEnabled=true\n")
