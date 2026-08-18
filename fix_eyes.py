import re

filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace: showLoginPassword ? 'eye-off' : 'eye'
# With: showLoginPassword ? 'eye' : 'eye-off'
content = content.replace("showLoginPassword ? 'eye-off' : 'eye'", "showLoginPassword ? 'eye' : 'eye-off'")

# Replace: showCreatePassword ? 'eye-off' : 'eye'
# With: showCreatePassword ? 'eye' : 'eye-off'
content = content.replace("showCreatePassword ? 'eye-off' : 'eye'", "showCreatePassword ? 'eye' : 'eye-off'")

# Replace: showKey ? 'eye-off' : 'eye'
# With: showKey ? 'eye' : 'eye-off'
content = content.replace("showKey ? 'eye-off' : 'eye'", "showKey ? 'eye' : 'eye-off'")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
