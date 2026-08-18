import sys

with open('e:\\GitHub\\J5-OBS\\panel\\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add to sidebar menu
sidebar_btn = '''
                    <button v-if="user.role === 'admin'" @click="adminTab = 'branding'" :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors', adminTab === 'branding' ? 'bg-indigo-600/20 text-indigo-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200']">
                        <i data-lucide="shield-check" class="w-5 h-5"></i> Global Branding
                    </button>'''

html = html.replace('<button v-if="user.role === \\'admin\\'" @click="adminTab = \\'users\\'"', sidebar_btn + '\n                    <button v-if="user.role === \\'admin\\'" @click="adminTab = \\'users\\'"')

# Add branding tab view
branding_view = '''
                <!-- VISTA: BRANDING (ADMIN) -->
                <div v-if="adminTab === 'branding' && user.role === 'admin'" class="max-w-5xl mx-auto">
                    <div class="flex justify-between items-center mb-6">
                        <div>
                            <h2 class="text-2xl font-bold">J5 Global Branding</h2>
                            <p class="text-slate-400 text-sm mt-1">Control maestro de diseno para todos los servidores (Nodos)</p>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <!-- Branding Form -->
                        <div class="lg:col-span-2 glass-card rounded-2xl p-6">
                            <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                                <i data-lucide="shield-check" class="w-5 h-5 text-indigo-400"></i>
                                Assets Obligatorios (Capa 100)
                            </h3>
                            
                            <div class="space-y-4">
                                <div class="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                                    <div class="flex justify-between items-center mb-2">
                                        <label class="font-bold">Watermark Position</label>
                                        <span class="text-xs px-2 py-1 bg-rose-500/20 text-rose-400 rounded">Protected</span>
                                    </div>
                                    <select class="w-full px-4 py-2 bg-slate-800 rounded-lg text-white outline-none border border-slate-600 focus:border-indigo-500">
                                        <option>RIGHT EDGE</option>
                                        <option>LEFT EDGE</option>
                                        <option>TOP RIGHT</option>
                                        <option>TOP LEFT</option>
                                    </select>
                                </div>

                                <div class="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                                    <div class="flex justify-between items-center mb-2">
                                        <label class="font-bold">Watermark Opacity</label>
                                        <span class="text-xs px-2 py-1 bg-rose-500/20 text-rose-400 rounded">Protected</span>
                                    </div>
                                    <input type="range" min="0" max="100" value="80" class="w-full accent-indigo-500">
                                </div>
                                
                                <div class="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                                    <div class="flex justify-between items-center mb-2">
                                        <label class="font-bold">Chat Overlay Style</label>
                                        <span class="text-xs px-2 py-1 bg-rose-500/20 text-rose-400 rounded">Protected</span>
                                    </div>
                                    <select class="w-full px-4 py-2 bg-slate-800 rounded-lg text-white outline-none border border-slate-600 focus:border-indigo-500">
                                        <option>J5 Default (Transparent)</option>
                                        <option>J5 Dark Box</option>
                                        <option>J5 Neon</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="mt-6 flex gap-4">
                                <button @click="publishBranding" class="flex-1 mobile-btn mobile-btn-primary">
                                    <i data-lucide="upload-cloud" class="w-5 h-5"></i> Publish Version
                                </button>
                                <button class="px-6 mobile-btn bg-slate-700 hover:bg-slate-600 text-white">
                                    <i data-lucide="eye" class="w-5 h-5"></i> Preview
                                </button>
                            </div>
                        </div>
                        
                        <!-- Deployment Status -->
                        <div class="space-y-6">
                            <div class="glass-card rounded-2xl p-6">
                                <h3 class="text-lg font-bold mb-4">Deployment Status</h3>
                                <div class="space-y-3">
                                    <div class="flex justify-between items-center p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                                        <span class="text-emerald-400 font-medium">Global Status</span>
                                        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> ACTIVE</span>
                                    </div>
                                    <div class="flex justify-between items-center p-3 bg-slate-900/50 rounded-xl">
                                        <span class="text-slate-400">Current Version</span>
                                        <span class="font-mono text-indigo-400">v2.4.1</span>
                                    </div>
                                    <div class="flex justify-between items-center p-3 bg-slate-900/50 rounded-xl">
                                        <span class="text-slate-400">Active Instances</span>
                                        <span class="font-bold">{{ instances.length }}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="glass-card rounded-2xl p-6">
                                <h3 class="text-lg font-bold mb-4">Security</h3>
                                <p class="text-sm text-slate-400 mb-4">
                                    Los nodos validan el paquete de branding usando firmas de hash SHA-256 antes de inyectarlo en la capa 100 (OBS).
                                </p>
                                <div class="p-3 bg-slate-900/80 rounded-lg text-xs font-mono text-slate-500 break-all border border-slate-800">
                                    SHA256: 8f4e3c1b2a9d...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
'''

html = html.replace('<!-- VISTA: USUARIOS -->', branding_view + '\\n\\n                <!-- VISTA: USUARIOS -->')

# Add publish method to vue
vue_method = '''
                const publishBranding = async () => {
                    Toast.fire({ icon: 'info', title: 'Generando paquete firmado...' });
                    try {
                        const payload = {
                            id: 'v2.4.1-' + Date.now(),
                            version_tag: 'v2.4.1',
                            config_json: { watermark: { opacity: 80, pos: 'RIGHT_EDGE' }, chat: { style: 'default' } },
                            signature: '8f4e3c1b2a9d'
                        };
                        const res = await fetch('/api/admin/branding', { method: 'POST', headers: headers(), body: JSON.stringify(payload) });
                        if(!res.ok) throw new Error('Error al publicar branding');
                        Toast.fire({ icon: 'success', title: 'Branding v2.4.1 Publicado Globalmente' });
                    } catch (e) { Toast.fire({ icon: 'error', title: e.message }); }
                };
'''

html = html.replace('const createUser = async () => {', vue_method + '\\n                const createUser = async () => {')
html = html.replace('deleteUser,\\n', 'deleteUser, publishBranding,\\n')


with open('e:\\GitHub\\J5-OBS\\panel\\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
