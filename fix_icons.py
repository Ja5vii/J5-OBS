import re

filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '<i :data-lucide="showLoginPassword ? \'eye\' : \'eye-off\'" class="w-5 h-5"></i>',
    '<i v-if="showLoginPassword" data-lucide="eye" class="w-5 h-5"></i><i v-else data-lucide="eye-off" class="w-5 h-5"></i>'
)

content = content.replace(
    '<i :data-lucide="showCreatePassword ? \'eye\' : \'eye-off\'" class="w-5 h-5"></i>',
    '<i v-if="showCreatePassword" data-lucide="eye" class="w-5 h-5"></i><i v-else data-lucide="eye-off" class="w-5 h-5"></i>'
)

content = content.replace(
    '<i :data-lucide="showKey ? \'eye\' : \'eye-off\'" class="w-4 h-4"></i>',
    '<i v-if="showKey" data-lucide="eye" class="w-4 h-4"></i><i v-else data-lucide="eye-off" class="w-4 h-4"></i>'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
