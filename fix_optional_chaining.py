filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('user?.username?.charAt', '(user && user.username) ? user.username.charAt')
content = content.replace('user?.username', 'user ? user.username : ""')
content = content.replace('user?.role', 'user ? user.role : ""')
content = content.replace('activeInstance?.name', 'activeInstance ? activeInstance.name : ""')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
