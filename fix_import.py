filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the local import
content = content.replace("        import asyncio\n        asyncio.create_task", "        asyncio.create_task")

# Make sure asyncio is at the top
if "import asyncio" not in content[:500]:
    content = "import asyncio\n" + content

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed asyncio import")
