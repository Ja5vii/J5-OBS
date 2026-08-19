filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

log_start = -1
log_end = -1
for i, line in enumerate(lines):
    if 'async def get_obs_log(request):' in line:
        log_start = i - 1
    if log_start != -1 and 'return web.Response(text="".join(lines[-100:]))' in line:
        log_end = i + 1
        break

if log_start != -1 and log_end != -1:
    log_func = lines[log_start:log_end]
    del lines[log_start:log_end]
    
    # Insert before get_stats
    stats_start = -1
    for i, line in enumerate(lines):
        if 'async def get_stats(request):' in line:
            stats_start = i - 1
            break
            
    if stats_start != -1:
        lines = lines[:stats_start] + log_func + ['\n'] + lines[stats_start:]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("".join(lines))
        print("Fixed!")
    else:
        print("No get_stats")
else:
    print(f"No get_obs_log start={log_start} end={log_end}")
