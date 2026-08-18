filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# SVGs inline para ojo abierto y cerrado
eye_open = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>'
eye_off = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
eye_open_sm = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>'
eye_off_sm = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'

# Reemplazar el de Login
old_login = '<span v-if="showLoginPassword" key="eye1"><i data-lucide="eye" class="w-5 h-5"></i></span><span v-else key="eye-off1"><i data-lucide="eye-off" class="w-5 h-5"></i></span>'
new_login = f'<span v-if="showLoginPassword">{eye_open}</span><span v-else>{eye_off}</span>'
content = content.replace(old_login, new_login)

# Reemplazar el de Crear Usuario
old_create = '<span v-if="showCreatePassword" key="eye2"><i data-lucide="eye" class="w-5 h-5"></i></span><span v-else key="eye-off2"><i data-lucide="eye-off" class="w-5 h-5"></i></span>'
new_create = f'<span v-if="showCreatePassword">{eye_open}</span><span v-else>{eye_off}</span>'
content = content.replace(old_create, new_create)

# Reemplazar el de Stream Key (mas pequeno)
old_key = '<span v-if="showKey" key="eye3"><i data-lucide="eye" class="w-4 h-4"></i></span><span v-else key="eye-off3"><i data-lucide="eye-off" class="w-4 h-4"></i></span>'
new_key = f'<span v-if="showKey">{eye_open_sm}</span><span v-else>{eye_off_sm}</span>'
content = content.replace(old_key, new_key)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
