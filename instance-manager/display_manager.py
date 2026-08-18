import subprocess


class DisplayManager:
    def __init__(self, config):
        self.config = config
        self._allocated = {}
        self._xvfb_processes = {}

    async def initialize(self):
        self._allocated.clear()

    def allocate(self, instance_id):
        cfg = self.config.get()
        base = cfg["displays"]["base"]
        used = set(self._allocated.values())
        for i in range(cfg["resources"]["max_instances"]):
            display_num = base + i + 1
            if display_num not in used:
                self._allocated[instance_id] = display_num
                return display_num
        raise RuntimeError("No available display numbers")

    def release(self, instance_id):
        self.stop_xvfb(instance_id)
        self._allocated.pop(instance_id, None)

    def get_display(self, instance_id):
        return self._allocated.get(instance_id)

    def start_xvfb(self, instance_id):
        display_num = self._allocated.get(instance_id)
        if display_num is None:
            raise ValueError(f"No display allocated for {instance_id}")
        if instance_id in self._xvfb_processes:
            return
        cfg = self.config.get()
        resolution = cfg["displays"]["resolution"]
        depth = cfg["displays"]["depth"]
        display_str = f":{display_num}"
        proc = subprocess.Popen(
            ["Xvfb", display_str, "-screen", "0", f"{resolution}x{depth}", "-ac", "+extension", "GLX", "+render", "-noreset"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._xvfb_processes[instance_id] = proc

    def stop_xvfb(self, instance_id):
        proc = self._xvfb_processes.pop(instance_id, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def get_display_env(self, instance_id):
        display_num = self._allocated.get(instance_id)
        if display_num is None:
            return {}
        return {"DISPLAY": f":{display_num}"}
