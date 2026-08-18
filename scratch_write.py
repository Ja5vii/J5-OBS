# -*- coding: utf-8 -*-
import os

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J5 OBS Manager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = { darkMode: 'class', theme: { extend: { colors: { dark: '#0f172a', darker: '#0b1120', card: '#1e293b', primary: '#6366f1', primaryHover: '#4f46e5', success: '#10b981', danger: '#ef4444', warning: '#f59e0b' } } } }
    </script>
    <style>
        body { background-color: #0b1120; color: #f8fafc; font-family: 'Inter', system-ui, sans-serif; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .slide-fade-enter-active { transition: all 0.3s ease-out; }
        .slide-fade-leave-active { transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1); }
        .slide-fade-enter-from, .slide-fade-leave-to { transform: translateY(-20px); opacity: 0; }
        [v-cloak] { display: none; }
    </style>
</head>
<body class="antialiased min-h-screen flex flex-col">
    <div id="app" v-cloak class="flex-1 flex flex-col h-full">
        <!-- LOGIN SCREEN -->
        <div v-if="!authenticated" class="flex-1 flex items-center justify-center p-4">
            <div class="glass rounded-2xl p-8 w-full max-w-md shadow-2xl">
                <div class="text-center mb-8">
                    <div class="w-20 h-20 bg-primary/20 text-primary rounded-full flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-video text-3xl"></i></div>
                    <h1 class="text-3xl font-bold text-white tracking-tight">J5 OBS</h1>
                </div>
                <form @submit.prevent="login" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-2">Usuario / Token</label>
                        <input v-model="loginForm.username" type="text" class="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition" placeholder="admin">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-2">Password</label>
                        <input v-model="loginForm.password" type="password" class="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition" placeholder="******">
                    </div>
                    <button type="submit" :disabled="loading" class="w-full bg-primary hover:bg-primaryHover text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-primary/30 mt-4"><i v-if="loading" class="fa-solid fa-circle-notch fa-spin mr-2"></i><span>Conectar</span></button>
                    <p v-if="error" class="text-danger text-sm text-center font-medium bg-danger/10 py-2 rounded-lg mt-4"><i class="fa-solid fa-triangle-exclamation mr-1"></i> {{ error }}</p>
                </form>
            </div>
        </div>

        <!-- DASHBOARD -->
        <div v-else class="flex-1 flex flex-col">
            <header class="glass sticky top-0 z-40 border-b border-slate-700">
                <div class="max-w-7xl mx-auto px-4 flex justify-between items-center h-16">
                    <div class="flex items-center space-x-3">
                        <div class="w-8 h-8 bg-primary text-white rounded-lg flex items-center justify-center"><i class="fa-solid fa-video text-sm"></i></div>
                        <h1 class="text-xl font-bold tracking-tight">J5 OBS <span class="text-primary">Manager</span></h1>
                    </div>
                    <div class="flex items-center space-x-2 sm:space-x-4">
                        <button v-if="user.role === 'admin'" @click="tab = 'users'" :class="tab==='users'?'text-primary':'text-slate-400'" class="hover:text-white transition w-10 h-10 flex items-center justify-center" title="Usuarios"><i class="fa-solid fa-users"></i></button>
                        <button @click="tab = 'instances'" :class="tab==='instances'?'text-primary':'text-slate-400'" class="hover:text-white transition w-10 h-10 flex items-center justify-center" title="Instancias"><i class="fa-solid fa-server"></i></button>
                        <button @click="showProfileModal = true" class="text-slate-400 hover:text-white transition w-10 h-10 rounded-full hover:bg-slate-800 flex items-center justify-center" title="Mi Perfil"><i class="fa-solid fa-user-circle"></i></button>
                        <button @click="logout" class="text-slate-400 hover:text-danger transition w-10 h-10 rounded-full hover:bg-slate-800 flex items-center justify-center" title="Cerrar sesion"><i class="fa-solid fa-arrow-right-from-bracket"></i></button>
                    </div>
                </div>
            </header>

            <main class="flex-1 max-w-7xl w-full mx-auto px-4 py-8">
                <!-- Tab: Instances -->
                <div v-if="tab === 'instances'">
                    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
                        <div>
                            <h2 class="text-2xl font-bold text-white">Instancias</h2>
                            <p class="text-slate-400 text-sm mt-1">Gestiona tus instancias de OBS.</p>
                        </div>
                        <button v-if="user.role === 'admin'" @click="showCreateModal = true" class="bg-primary hover:bg-primaryHover text-white px-5 py-2.5 rounded-xl font-medium shadow-lg transition flex items-center gap-2"><i class="fa-solid fa-plus"></i> Nueva Instancia</button>
                    </div>

                    <div v-if="instances.length === 0 && !loading" class="text-center py-20 glass rounded-2xl border border-slate-700/50 border-dashed">
                        <h3 class="text-xl font-medium text-white mb-2">No tienes instancias</h3>
                        <p class="text-slate-400">Pide a un administrador que te asigne una instancia o creala si eres admin.</p>
                    </div>

                    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <div v-for="inst in instances" :key="inst.instance_id" class="glass rounded-2xl overflow-hidden shadow-lg flex flex-col">
                            <div class="p-5 border-b border-slate-700/50 flex justify-between items-start bg-slate-800/30">
                                <div>
                                    <h3 class="font-bold text-lg text-white">{{ inst.name }}</h3>
                                    <p class="text-xs text-slate-500 mt-1 uppercase">{{ inst.instance_id }} <span v-if="user.role==='admin' && inst.owner_id">- User: {{inst.owner_id}}</span></p>
                                </div>
                                <span :class="statusBadgeClass(inst.status)" class="px-3 py-1 text-xs font-bold rounded-full uppercase">{{ inst.status }}</span>
                            </div>
                            <div class="p-5 flex-1 bg-slate-900/40">
                                <div class="grid grid-cols-2 gap-4">
                                    <div class="bg-slate-800/60 rounded-xl p-3"><p class="text-xs text-slate-400">CPU</p><p class="text-lg font-bold" :class="cpuColor(inst.instance_id)">{{ getStat(inst.instance_id, 'cpu_percent') }}%</p></div>
                                    <div class="bg-slate-800/60 rounded-xl p-3"><p class="text-xs text-slate-400">RAM</p><p class="text-lg font-bold" :class="ramColor(inst.instance_id)">{{ getStat(inst.instance_id, 'ram_mb') }} MB</p></div>
                                    <div class="bg-slate-800/60 rounded-xl p-3"><p class="text-xs text-slate-400">WS Port</p><p class="text-sm font-semibold text-primary">{{ inst.websocket_port || '-' }}</p></div>
                                    <div class="bg-slate-800/60 rounded-xl p-3"><p class="text-xs text-slate-400">Display</p><p class="text-sm font-semibold text-success">{{ inst.display ? ':'+inst.display : '-' }}</p></div>
                                </div>
                            </div>
                            <div class="p-4 border-t border-slate-700/50 bg-slate-800/20 flex flex-wrap gap-2 justify-end">
                                <template v-if="['ONLINE', 'STREAMING', 'STARTING'].includes(inst.status)">
                                    <button @click="executeAction(inst.instance_id, 'stop')" class="flex-1 bg-danger/20 text-danger hover:bg-danger/30 border border-danger/30 px-3 py-2 rounded-lg text-sm transition font-medium"><i class="fa-solid fa-stop"></i> Stop</button>
                                    <button @click="executeAction(inst.instance_id, 'restart')" class="flex-1 bg-warning/20 text-warning hover:bg-warning/30 border border-warning/30 px-3 py-2 rounded-lg text-sm transition font-medium"><i class="fa-solid fa-rotate-right"></i> Restart</button>
                                </template>
                                <template v-else>
                                    <button @click="executeAction(inst.instance_id, 'start')" class="flex-1 bg-success/20 text-success hover:bg-success/30 border border-success/30 px-3 py-2 rounded-lg text-sm transition font-medium"><i class="fa-solid fa-play"></i> Start</button>
                                </template>
                                <button @click="openSettings(inst)" class="w-10 bg-slate-700 hover:bg-slate-600 border border-slate-600 text-white rounded-lg"><i class="fa-solid fa-gear"></i></button>
                                <button v-if="user.role === 'admin'" @click="deleteInstance(inst.instance_id)" class="w-10 bg-slate-700 hover:bg-danger/80 border border-slate-600 hover:border-danger text-slate-300 hover:text-white rounded-lg"><i class="fa-solid fa-trash"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Tab: Users -->
                <div v-if="tab === 'users' && user.role === 'admin'">
                    <div class="flex justify-between items-center mb-8">
                        <h2 class="text-2xl font-bold text-white">Usuarios</h2>
                        <button @click="showUserModal = true" class="bg-primary px-5 py-2.5 rounded-xl font-medium text-white shadow-lg"><i class="fa-solid fa-user-plus"></i> Nuevo</button>
                    </div>
                    <div class="glass rounded-2xl p-4">
                        <table class="w-full text-left">
                            <thead><tr class="text-slate-400 border-b border-slate-700"><th class="pb-2 px-2">ID</th><th class="pb-2 px-2">Username</th><th class="pb-2 px-2">Role</th><th class="pb-2 text-right px-2">Actions</th></tr></thead>
                            <tbody>
                                <tr v-for="u in usersList" :key="u.id" class="border-b border-slate-800 hover:bg-slate-800/30 transition">
                                    <td class="py-4 px-2 text-sm font-mono text-slate-500">{{u.id}}</td>
                                    <td class="py-4 px-2 text-white font-medium">{{u.username}}</td>
                                    <td class="py-4 px-2"><span class="px-2 py-1 text-xs rounded-lg font-medium" :class="u.role==='admin'?'bg-primary/20 text-primary border border-primary/30':'bg-slate-700 text-slate-300 border border-slate-600'">{{u.role.toUpperCase()}}</span></td>
                                    <td class="py-4 px-2 text-right">
                                        <button v-if="u.id !== user.id && u.id !== 'admin-env'" @click="deleteUser(u.id)" class="text-danger hover:text-white bg-danger/10 hover:bg-danger rounded-lg p-2 transition w-9 h-9"><i class="fa-solid fa-trash"></i></button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>

        <!-- Create Instance Modal -->
        <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div class="glass border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
                <div class="p-6 border-b border-slate-700"><h2 class="text-xl font-bold text-white flex items-center gap-2"><i class="fa-solid fa-plus-circle text-primary"></i> Nueva Instancia</h2></div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Nombre</label>
                        <input v-model="form.name" type="text" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary focus:ring-1 focus:ring-primary" placeholder="Ej: Stream Secundario">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Template</label>
                        <select v-model="form.template" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary focus:ring-1 focus:ring-primary">
                            <option value="">Sin Template (Predeterminado)</option>
                            <option v-for="tpl in templates" :key="tpl.name" :value="tpl.name">{{ tpl.name }}</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Asignar Dueno (Usuario)</label>
                        <select v-model="form.owner_id" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary focus:ring-1 focus:ring-primary">
                            <option value="">Sin Dueno (Admin general)</option>
                            <option v-for="u in usersList" :key="u.id" :value="u.id">{{ u.username }}</option>
                        </select>
                    </div>
                </div>
                <div class="p-5 flex justify-end gap-3 bg-slate-800/30 border-t border-slate-700"><button @click="showCreateModal=false" class="px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition">Cancelar</button><button @click="createInstance" class="px-5 py-2.5 bg-primary hover:bg-primaryHover text-white rounded-xl shadow-lg transition">Crear Instancia</button></div>
            </div>
        </div>

        <!-- Create User Modal -->
        <div v-if="showUserModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div class="glass border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
                <div class="p-6 border-b border-slate-700"><h2 class="text-xl font-bold text-white flex items-center gap-2"><i class="fa-solid fa-user-plus text-primary"></i> Nuevo Usuario</h2></div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Username</label>
                        <input v-model="userForm.username" type="text" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary" placeholder="usuario123">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Password</label>
                        <input v-model="userForm.password" type="password" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary" placeholder="******">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Rol</label>
                        <select v-model="userForm.role" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary">
                            <option value="user">User</option><option value="admin">Admin</option>
                        </select>
                    </div>
                </div>
                <div class="p-5 flex justify-end gap-3 bg-slate-800/30 border-t border-slate-700"><button @click="showUserModal=false" class="px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition">Cancelar</button><button @click="createUser" class="px-5 py-2.5 bg-primary hover:bg-primaryHover text-white rounded-xl shadow-lg transition">Guardar Usuario</button></div>
            </div>
        </div>

        <!-- Settings Modal -->
        <div v-if="showSettingsModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div class="glass border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
                <div class="p-6 border-b border-slate-700"><h2 class="text-xl font-bold text-white flex items-center gap-2"><i class="fa-solid fa-sliders text-primary"></i> Configurar OBS</h2></div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">RTMP URL</label>
                        <input v-model="settingsForm.rtmp_url" type="text" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white font-mono text-sm outline-none focus:border-primary" placeholder="rtmp://live.twitch.tv/app">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Stream Key</label>
                        <input v-model="settingsForm.rtmp_key" type="password" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white font-mono text-sm outline-none focus:border-primary" placeholder="live_XXXXXXXX">
                    </div>
                    <div v-if="user.role === 'admin'">
                        <label class="block text-sm font-medium text-slate-300 mb-1">Dueno de Instancia</label>
                        <select v-model="settingsForm.owner_id" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary">
                            <option value="">Sin Dueno (Admin)</option>
                            <option v-for="u in usersList" :key="u.id" :value="u.id">{{ u.username }}</option>
                        </select>
                    </div>
                </div>
                <div class="p-5 flex justify-end gap-3 bg-slate-800/30 border-t border-slate-700"><button @click="showSettingsModal=false" class="px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition">Cancelar</button><button @click="saveSettings" class="px-5 py-2.5 bg-primary hover:bg-primaryHover text-white rounded-xl shadow-lg transition">Guardar Cambios</button></div>
            </div>
        </div>

        <!-- Profile Modal -->
        <div v-if="showProfileModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div class="glass border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
                <div class="p-6 border-b border-slate-700"><h2 class="text-xl font-bold text-white flex items-center gap-2"><i class="fa-solid fa-user-pen text-primary"></i> Mi Perfil</h2></div>
                <div class="p-6 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Username</label>
                        <input v-model="profileForm.username" type="text" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary" placeholder="Nuevo Username">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-300 mb-1">Password</label>
                        <input v-model="profileForm.password" type="password" class="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-white outline-none focus:border-primary" placeholder="Nueva (opcional)">
                    </div>
                </div>
                <div class="p-5 flex justify-end gap-3 bg-slate-800/30 border-t border-slate-700"><button @click="showProfileModal=false" class="px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition">Cancelar</button><button @click="updateProfile" class="px-5 py-2.5 bg-primary hover:bg-primaryHover text-white rounded-xl shadow-lg transition">Actualizar Perfil</button></div>
            </div>
        </div>

    </div>

    <script>
        const { createApp, ref, onMounted, onUnmounted, computed } = Vue;
        createApp({
            setup() {
                const authenticated = ref(false);
                const token = ref('');
                const loading = ref(false);
                const error = ref('');
                const user = ref({ id: '', role: 'user', username: '' });
                const loginForm = ref({ username: '', password: '' });
                const tab = ref('instances');

                const instances = ref([]);
                const stats = ref({});
                const templates = ref([]);
                const usersList = ref([]);
                
                const showCreateModal = ref(false);
                const form = ref({ name: '', template: '', owner_id: '' });
                
                const showUserModal = ref(false);
                const userForm = ref({ username: '', password: '', role: 'user' });

                const showSettingsModal = ref(false);
                const activeInstance = ref(null);
                const settingsForm = ref({ rtmp_url: '', rtmp_key: '', owner_id: '' });

                const showProfileModal = ref(false);
                const profileForm = ref({ username: '', password: '' });

                let pollInterval = null;

                const headers = () => ({ 'Content-Type': 'application/json', 'Authorization': `Bearer ${token.value}` });

                const login = async () => {
                    loading.value = true; error.value = '';
                    try {
                        let res;
                        if(token.value && !loginForm.value.username) {
                            res = await fetch('/api/status', { headers: headers() });
                            const data = await res.json();
                            if (!res.ok) throw new Error(data.error || 'Credenciales invalidas');
                            user.value = data.user;
                        } else {
                            if(loginForm.value.username === '' && loginForm.value.password !== '') {
                                token.value = loginForm.value.password;
                                res = await fetch('/api/status', { headers: headers() });
                            } else {
                                res = await fetch('/api/auth/login', { method: 'POST', body: JSON.stringify(loginForm.value), headers: {'Content-Type': 'application/json'} });
                            }
                            const data = await res.json();
                            if (!res.ok) throw new Error(data.error || 'Credenciales invalidas');
                            if (data.token) token.value = data.token;
                            if (data.user) user.value = data.user;
                        }
                        
                        authenticated.value = true;
                        localStorage.setItem('j5_token', token.value);
                        fetchData();
                        if(user.value.role === 'admin') fetchUsers();
                        pollInterval = setInterval(fetchData, 5000);
                    } catch (e) { error.value = e.message; token.value = ''; localStorage.removeItem('j5_token'); } finally { loading.value = false; }
                };

                const logout = () => { authenticated.value = false; token.value = ''; localStorage.removeItem('j5_token'); if (pollInterval) clearInterval(pollInterval); };

                const fetchData = async () => {
                    if (!authenticated.value) return;
                    try {
                        const [iR, sR] = await Promise.all([fetch('/api/instances', { headers: headers() }), fetch('/api/stats', { headers: headers() })]);
                        if (iR.ok) instances.value = (await iR.json()).instances || [];
                        else if (iR.status === 401) return logout();
                        if (sR.ok) {
                            const newStats = {}; (await sR.json()).instances.forEach(s => newStats[s.instance_id] = s); stats.value = newStats;
                        }
                    } catch(e) {}
                };

                const fetchUsers = async () => {
                    if(user.value.role !== 'admin') return;
                    try { const res = await fetch('/api/users', { headers: headers() }); if (res.ok) usersList.value = (await res.json()).users || []; } catch(e){}
                };

                const createInstance = async () => {
                    try {
                        const body = { name: form.value.name, template: form.value.template };
                        if(form.value.owner_id) body.owner_id = form.value.owner_id;
                        const res = await fetch('/api/instances', { method: 'POST', headers: headers(), body: JSON.stringify(body) });
                        if (!res.ok) throw new Error((await res.json()).error);
                        showCreateModal.value = false; form.value = { name: '', template: '', owner_id: '' }; fetchData();
                    } catch (e) { alert(e.message); }
                };

                const createUser = async () => {
                    try {
                        const res = await fetch('/api/users', { method: 'POST', headers: headers(), body: JSON.stringify(userForm.value) });
                        if (!res.ok) throw new Error((await res.json()).error);
                        showUserModal.value = false; userForm.value = { username: '', password: '', role: 'user' }; fetchUsers();
                    } catch (e) { alert(e.message); }
                };

                const deleteUser = async (id) => {
                    if(!confirm('Eliminar usuario y desvincular sus instancias?')) return;
                    await fetch(`/api/users/${id}`, { method: 'DELETE', headers: headers() });
                    fetchUsers(); fetchData();
                };

                const executeAction = async (id, action) => {
                    await fetch(`/api/instances/${id}/${action}`, { method: 'POST', headers: headers() });
                    fetchData();
                };

                const deleteInstance = async (id) => {
                    if(!confirm('Eliminar instancia por completo?')) return;
                    await fetch(`/api/instances/${id}`, { method: 'DELETE', headers: headers() });
                    fetchData();
                };

                const openSettings = (inst) => { activeInstance.value = inst; settingsForm.value = { rtmp_url: inst.rtmp_url||'', rtmp_key: inst.rtmp_key||'', owner_id: inst.owner_id||'' }; showSettingsModal.value = true; };
                const saveSettings = async () => {
                    const body = { rtmp_url: settingsForm.value.rtmp_url, rtmp_key: settingsForm.value.rtmp_key };
                    if(user.value.role === 'admin' && settingsForm.value.owner_id !== undefined) body.owner_id = settingsForm.value.owner_id || null;
                    await fetch(`/api/instances/${activeInstance.value.instance_id}`, { method: 'PATCH', headers: headers(), body: JSON.stringify(body) });
                    showSettingsModal.value = false; fetchData();
                };

                const updateProfile = async () => {
                    try {
                        const res = await fetch('/api/users/me', { method: 'PUT', headers: headers(), body: JSON.stringify(profileForm.value) });
                        if (!res.ok) throw new Error((await res.json()).error);
                        showProfileModal.value = false; profileForm.value = { username: '', password: '' };
                        alert("Perfil actualizado. Por favor, inicia sesion de nuevo."); logout();
                    } catch (e) { alert(e.message); }
                };

                const getStat = (id, key) => { const s = stats.value[id]; return s ? (key==='cpu_percent'?s[key].toFixed(1):Math.round(s[key])) : '0.0'; };
                const statusBadgeClass = (s) => s==='ONLINE'?'bg-success/20 text-success border border-success/30':(s==='STREAMING'?'bg-primary/20 text-primary border border-primary/30':(s==='STANDBY'?'bg-slate-700/50 text-slate-400 border border-slate-600':'bg-danger/20 text-danger border border-danger/30'));
                const cpuColor = (id) => { const v = parseFloat(getStat(id, 'cpu_percent')); return v>80?'text-danger':(v>60?'text-warning':'text-slate-200'); };
                const ramColor = (id) => { const v = parseFloat(getStat(id, 'ram_mb')); return v>2000?'text-danger':(v>1500?'text-warning':'text-slate-200'); };
                const activeCount = computed(() => instances.value.filter(i => ['ONLINE', 'STREAMING'].includes(i.status)).length);

                onMounted(() => { const t = localStorage.getItem('j5_token'); if (t) { token.value = t; login(); } });
                onUnmounted(() => { if (pollInterval) clearInterval(pollInterval); });

                return {
                    authenticated, token, loading, error, user, loginForm, tab,
                    instances, stats, templates, usersList, activeCount,
                    showCreateModal, form, createInstance,
                    showUserModal, userForm, createUser, deleteUser,
                    showSettingsModal, activeInstance, settingsForm, openSettings, saveSettings,
                    showProfileModal, profileForm, updateProfile,
                    executeAction, deleteInstance, getStat, statusBadgeClass, cpuColor, ramColor,
                    login, logout, fetchData
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
"""
with open("e:\\GitHub\\J5-OBS\\panel\\index.html", "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)
