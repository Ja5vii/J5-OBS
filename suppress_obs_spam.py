filepath = r'e:\GitHub\J5-OBS\instance-manager\health_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_code = """import socket
import obsws_python as obsws
def _fetch_obs_stats(port, password):
    # Check if port is open to avoid obsws_python traceback spam
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)
        if s.connect_ex(('127.0.0.1', port)) != 0:
            return {"obs_error": "Connection refused"}
    
    import logging
    logging.getLogger("obsws_python").setLevel(logging.CRITICAL)
    
    try:"""

content = content.replace("""import obsws_python as obsws
def _fetch_obs_stats(port, password):
    try:""", new_code)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
