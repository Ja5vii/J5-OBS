import sys

with open('e:\\GitHub\\J5-OBS\\instance-manager\\process_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

insert_idx = 0
for i, line in enumerate(lines):
    if line.strip().startswith('async def start_instance('):
        insert_idx = i + 1
        break

code = '''
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
'''

lines.insert(insert_idx, code)

with open('e:\\GitHub\\J5-OBS\\instance-manager\\process_manager.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
