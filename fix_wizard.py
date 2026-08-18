filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace wizard modal HTML with smart version that hides URL for known platforms
old_wizard_html = '''                          <select v-model="wizardForm.platform" class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500">
                            <option value="Twitch">Twitch</option>
                            <option value="YouTube">YouTube</option>
                            <option value="Kick">Kick</option>
                            <option value="Custom">Custom RTMP</option>
                          </select>
                          <input v-model="wizardForm.rtmp_url" type="text" class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500" placeholder="URL del Servidor (RTMP)">
                          <input v-model="wizardForm.rtmp_key" type="password" class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500" placeholder="Clave de Transmision">
                          <button @click="saveWizard" class="w-full mobile-btn mobile-btn-primary mt-2">Guardar Destino</button>'''

new_wizard_html = '''                          <select v-model="wizardForm.platform" @change="onPlatformChange" class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500">
                            <option value="Twitch">Twitch</option>
                            <option value="YouTube">YouTube</option>
                            <option value="Kick">Kick</option>
                            <option value="Custom">Custom RTMP</option>
                          </select>
                          <div v-if="wizardForm.platform === 'Custom'" class="space-y-2">
                              <input v-model="wizardForm.rtmp_url" type="text" class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500" placeholder="rtmp://tu-servidor/live">
                          </div>
                          <div v-else class="p-3 bg-slate-900/50 rounded-xl border border-slate-700 flex items-center gap-2">
                              <span class="text-xs text-slate-500 flex-shrink-0">URL automatica:</span>
                              <code class="text-xs text-indigo-400 truncate">{{ platformRtmpUrl(wizardForm.platform) }}</code>
                          </div>
                          <div class="relative">
                              <input v-model="wizardForm.rtmp_key" type="password" class="w-full px-4 py-3 bg-slate-900/50 rounded-xl text-white outline-none border border-slate-700 focus:border-indigo-500 pr-12" placeholder="Pega aqui tu Stream Key">
                              <span class="absolute right-3 top-3 text-slate-500 text-xs">KEY</span>
                          </div>
                          <button @click="saveWizard" class="w-full mobile-btn mobile-btn-primary mt-2">Guardar Destino</button>'''

content = content.replace(old_wizard_html, new_wizard_html)

# 2. Add platformRtmpUrl helper and onPlatformChange to JS
platform_urls_js = '''
                const PLATFORM_URLS = {
                    Twitch: 'rtmp://live.twitch.tv/app/',
                    YouTube: 'rtmp://a.rtmp.youtube.com/live2/',
                    Kick: 'rtmp://fa723fc1b171.global-contribute.live-video.net/app/'
                };
                const platformRtmpUrl = (p) => PLATFORM_URLS[p] || '';
                const onPlatformChange = () => {
                    if(wizardForm.value.platform !== 'Custom') {
                        wizardForm.value.rtmp_url = PLATFORM_URLS[wizardForm.value.platform] || '';
                    }
                };
'''
content = content.replace(
    'const showWizard = (inst)',
    platform_urls_js + '\n                const showWizard = (inst)'
)

# 3. Add onPlatformChange and platformRtmpUrl to return
content = content.replace(
    'showWizardModal, wizardStep, wizardForm, showGuideModal, showKey, window,',
    'showWizardModal, wizardStep, wizardForm, showGuideModal, showKey, window, onPlatformChange, platformRtmpUrl,'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
