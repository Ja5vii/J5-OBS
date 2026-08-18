import re

filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add user info above logout in desktop sidebar
user_info = '''
                <div class="p-4 border-t border-slate-800 flex items-center gap-3">
                    <div class="w-8 h-8 rounded bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                        {{ user?.username?.charAt(0).toUpperCase() }}
                    </div>
                    <div class="flex-1 overflow-hidden">
                        <p class="text-sm font-bold truncate">{{ user?.username }}</p>
                        <p class="text-xs text-slate-500 truncate capitalize">{{ user?.role }}</p>
                    </div>
                </div>
                <div class="p-4 pt-0">
                    <button @click="logout" class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors">
                        <i data-lucide="log-out" class="w-4 h-4"></i> Cerrar Sesion
                    </button>
                </div>
'''
content = re.sub(r'<div class="p-4 border-t border-slate-800">\s*<button @click="logout"[^>]+>.*?<\/button>\s*<\/div>', user_info, content, flags=re.DOTALL)

# 2. Fix the eye icon in login screen
login_password = '''
                    <div class="relative">
                        <input v-model="loginForm.password" :type="showLoginPassword ? 'text' : 'password'" required class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500 transition-colors" placeholder="Contrasena">
                        <button type="button" @click="showLoginPassword = !showLoginPassword" class="absolute right-3 top-3.5 text-slate-400 hover:text-white">
                            <i :data-lucide="showLoginPassword ? 'eye-off' : 'eye'" class="w-5 h-5"></i>
                        </button>
                    </div>
'''
content = re.sub(r'<div>\s*<input v-model="loginForm\.password"[^>]+placeholder="Contrasena">\s*<\/div>', login_password, content)

# 3. Fix the eye icon in user creation modal
create_user_password = '''
                        <div class="relative">
                            <input v-model="userForm.password" :type="showCreatePassword ? 'text' : 'password'" required class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500" placeholder="Contrasena">
                            <button type="button" @click="showCreatePassword = !showCreatePassword" class="absolute right-3 top-3.5 text-slate-400 hover:text-white">
                                <i :data-lucide="showCreatePassword ? 'eye-off' : 'eye'" class="w-5 h-5"></i>
                            </button>
                        </div>
'''
content = re.sub(r'<input v-model="userForm\.password" type="password"[^>]+placeholder="Contrasena">', create_user_password, content)

# 4. Add the Vue variables and updated() hook
# Find: const showKey = ref(false);
# Add: const showLoginPassword = ref(false); const showCreatePassword = ref(false);
content = content.replace('const showKey = ref(false);', 'const showKey = ref(false);\n                const showLoginPassword = ref(false);\n                const showCreatePassword = ref(false);')

# Find: return {
# Add variables to return
content = content.replace('return {', 'return {\n                    showLoginPassword, showCreatePassword,')

# Add updated() hook to Vue app
# Find: setup() {
# It's inside createApp({ setup() { ... } })
# We want to add updated() { this.(() => { if(window.lucide) lucide.createIcons(); }); }, right before setup()
content = content.replace('setup() {', 'updated() { this.(() => { if(window.lucide) lucide.createIcons(); }); },\n            setup() {')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
