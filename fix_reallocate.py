filepath = r'e:\GitHub\J5-OBS\instance-manager\main.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

restore_code = """        await self.db.initialize()
        await self.port_manager.initialize()
        await self.display_manager.initialize()
        
        # Restore allocations from database
        instances = await self.db.get_all_instances()
        for inst in instances:
            iid = inst["instance_id"]
            if inst.get("websocket_port"):
                self.port_manager._allocated[iid] = inst["websocket_port"]
            if inst.get("display") is not None:
                self.display_manager._allocated[iid] = inst["display"]
                
        self.process_manager.initialize()"""

content = content.replace("""        await self.db.initialize()
        await self.port_manager.initialize()
        await self.display_manager.initialize()
        self.process_manager.initialize()""", restore_code)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
