filepath = r'e:\GitHub\J5-OBS\instance-manager\database.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                await self._seed_roles_and_admin(conn)"""

replacement = """                await self._seed_roles_and_admin(conn)
                # Reset all instances to STANDBY on boot since processes are dead
                await conn.execute("UPDATE instances SET status = 'STANDBY', pid = NULL")"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added status reset")
else:
    print("Target not found")
