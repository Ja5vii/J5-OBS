filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'const getMoblinLink = (id) => \'moblin://?\' + encodeURIComponent(JSON.stringify({ streams: [{ name: "J5-OBS", url: "rtmp://" + window.location.hostname + ":1935/live/" + id }] }));',
    'const getMoblinLink = (id) => \'moblin://?\' + JSON.stringify({ streams: [{ name: "J5-OBS", url: "rtmp://" + window.location.hostname + ":1935/live/" + id }] });'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
