# coding=utf-8
import os
filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add to desktop sidebar
target_desktop = """<button v-if="user.role === 'admin'" @click="adminTab = 'users'" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors', adminTab === 'users' ? 'bg-indigo-600/20 text-indigo-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200']">
                        <i data-lucide="users" class="w-5 h-5"></i> <span class="font-medium">Usuarios</span>
                    </button>"""
replacement_desktop = target_desktop + """\n                    <button @click="adminTab = 'profile'" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors', adminTab === 'profile' ? 'bg-indigo-600/20 text-indigo-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200']">
                        <i data-lucide="user-cog" class="w-5 h-5"></i> <span class="font-medium">Mi Perfil</span>
                    </button>"""
content = content.replace(target_desktop, replacement_desktop)

# Add to mobile bottom bar
target_mobile = """<button v-if="user.role === 'admin'" @click="adminTab = 'users'" :class="['p-3 rounded-xl flex flex-col items-center gap-1 transition-colors', adminTab === 'users' ? 'text-indigo-400' : 'text-slate-500']">
                    <i data-lucide="users" class="w-5 h-5"></i>
                    <span class="text-[10px] font-medium">Usuarios</span>
                </button>"""
replacement_mobile = target_mobile + """\n                <button @click="adminTab = 'profile'" :class="['p-3 rounded-xl flex flex-col items-center gap-1 transition-colors', adminTab === 'profile' ? 'text-indigo-400' : 'text-slate-500']">
                    <i data-lucide="user-cog" class="w-5 h-5"></i>
                    <span class="text-[10px] font-medium">Perfil</span>
                </button>"""
content = content.replace(target_mobile, replacement_mobile)

# Add the Profile view
target_view = """<div v-if="adminTab === 'instances'">"""
profile_view = """<div v-if="adminTab === 'profile'" class="animate-fade-in max-w-lg mx-auto mt-10">
                    <div class="glass p-6 rounded-2xl border border-slate-800/50">
                        <div class="flex items-center gap-4 mb-6">
                            <div class="w-12 h-12 rounded-full bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold text-xl">
                                {{ (user && user.username) ? user.username.charAt(0).toUpperCase() : "" }}
                            </div>
                            <div>
                                <h2 class="text-xl font-bold text-white">{{ user ? user.username : "" }}</h2>
                                <p class="text-sm text-slate-400 capitalize">{{ user ? user.role : "" }}</p>
                            </div>
                        </div>
                        
                        <div class="space-y-4">
                            <h3 class="font-medium text-slate-300">Cambiar Contrasena</h3>
                            <input v-model="profileForm.password" type="password" class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500" placeholder="Nueva Contrasena">
                            <button @click="updateProfile" class="w-full mobile-btn mobile-btn-primary">Guardar Cambios</button>
                        </div>
                    </div>
                </div>\n                """
content = content.replace(target_view, profile_view + target_view)

# Add JS logic
target_js = """const userForm = ref({ username: '', password: '', role: 'user' });"""
replacement_js = target_js + """\n                const profileForm = ref({ password: '' });\n                const updateProfile = async () => {\n                    try {\n                        if(!profileForm.value.password) throw new Error('Escribe la nueva contrasena');\n                        const res = await fetch('/api/users/me', { method: 'POST', headers: headers(), body: JSON.stringify(profileForm.value) });\n                        const data = await res.json();\n                        if(!res.ok) throw new Error(data.error || 'Error cambiando contrasena');\n                        profileForm.value.password = '';\n                        Toast.fire({ icon: 'success', title: 'Contrasena actualizada' });\n                    } catch (e) { Toast.fire({ icon: 'error', title: e.message }); }\n                };"""
content = content.replace(target_js, replacement_js)

target_export = """userForm,"""
replacement_export = target_export + """ profileForm, updateProfile,"""
content = content.replace(target_export, replacement_export)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
