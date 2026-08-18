import asyncio


class PortManager:
    def __init__(self, config):
        self.config = config
        self._allocated = {}

    async def initialize(self):
        self._allocated.clear()

    def allocate(self, instance_id):
        cfg = self.config.get()
        base = cfg["ports"]["websocket_base"]
        max_instances = cfg["resources"]["max_instances"]
        used_ports = set(self._allocated.values())
        for i in range(max_instances):
            port = base + i
            if port not in used_ports:
                self._allocated[instance_id] = port
                return port
        raise RuntimeError("No available WebSocket ports")

    def release(self, instance_id):
        self._allocated.pop(instance_id, None)

    def get_port(self, instance_id):
        return self._allocated.get(instance_id)

    def get_all(self):
        return dict(self._allocated)
