import re

filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace showLoginPassword
content = content.replace(
    '<i v-if="showLoginPassword" data-lucide="eye" class="w-5 h-5"></i><i v-else data-lucide="eye-off" class="w-5 h-5"></i>',
    '<span v-if="showLoginPassword" key="eye1"><i data-lucide="eye" class="w-5 h-5"></i></span><span v-else key="eye-off1"><i data-lucide="eye-off" class="w-5 h-5"></i></span>'
)

# Replace showCreatePassword
content = content.replace(
    '<i v-if="showCreatePassword" data-lucide="eye" class="w-5 h-5"></i><i v-else data-lucide="eye-off" class="w-5 h-5"></i>',
    '<span v-if="showCreatePassword" key="eye2"><i data-lucide="eye" class="w-5 h-5"></i></span><span v-else key="eye-off2"><i data-lucide="eye-off" class="w-5 h-5"></i></span>'
)

# Replace showKey
content = content.replace(
    '<i v-if="showKey" data-lucide="eye" class="w-4 h-4"></i><i v-else data-lucide="eye-off" class="w-4 h-4"></i>',
    '<span v-if="showKey" key="eye3"><i data-lucide="eye" class="w-4 h-4"></i></span><span v-else key="eye-off3"><i data-lucide="eye-off" class="w-4 h-4"></i></span>'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
