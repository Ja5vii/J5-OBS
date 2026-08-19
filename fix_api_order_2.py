import re

filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

log_def_pattern = r'    @auth\n    async def get_obs_log\(request\):[\s\S]*?return web\.Response\(text="\.join\(lines\[-100:\]\)\)'
match = re.search(log_def_pattern, content)
if match:
    log_func = match.group(0)
    content = content.replace(log_func + "\n", "")
    
    # Insert it before get_stats
    stats_def_pattern = r'    @auth\n    async def get_stats\(request\):'
    content = content.replace('    @auth\n    async def get_stats(request):', log_func + '\n\n    @auth\n    async def get_stats(request):')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Could not find log def")
