import re

filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('this.(() =>', 'this.$nextTick(() =>')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
