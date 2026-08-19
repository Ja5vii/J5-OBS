filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

log_func_start = -1
log_func_end = -1
for i, line in enumerate(lines):
    if 'async def get_obs_log(request):' in line:
        log_func_start = i - 1 # Include @auth
    if log_func_start != -1 and i > log_func_start and 'return web.Response(text="".join(lines[-100:]))' in line:
        log_func_end = i + 1
        break

if log_func_start != -1 and log_func_end != -1:
    log_func_lines = lines[log_func_start:log_func_end]
    del lines[log_func_start:log_func_end]
    
    # Insert it before the app.router.add_get lines
    insert_idx = -1
    for i, line in enumerate(lines):
        if 'app.router.add_post("/api/login"' in line:
            insert_idx = i
            break
            
    if insert_idx != -1:
        lines = lines[:insert_idx] + log_func_lines + ['\n'] + lines[insert_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write("".join(lines))
print("Done!")
