filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix showWizard to auto-set URL from platform on open
old_show_wizard = "const showWizard = (inst) => { activeInstance.value = inst; wizardStep.value = 1; wizardForm.value = { platform: inst.platform||'Twitch', rtmp_url: inst.rtmp_url||'', rtmp_key: inst.rtmp_key||'' }; showWizardModal.value = true; };"

new_show_wizard = """const showWizard = (inst) => {
                    activeInstance.value = inst;
                    wizardStep.value = 1;
                    const plat = inst.platform || 'Twitch';
                    const autoUrl = PLATFORM_URLS[plat] || inst.rtmp_url || '';
                    wizardForm.value = { platform: plat, rtmp_url: autoUrl, rtmp_key: inst.rtmp_key || '' };
                    showWizardModal.value = true;
                };"""

content = content.replace(old_show_wizard, new_show_wizard)

# Fix onPlatformChange to always set URL from map when known platform selected
old_change = """const onPlatformChange = () => {
                    if(wizardForm.value.platform !== 'Custom') {
                        wizardForm.value.rtmp_url = PLATFORM_URLS[wizardForm.value.platform] || '';
                    }
                };"""

new_change = """const onPlatformChange = () => {
                    const p = wizardForm.value.platform;
                    wizardForm.value.rtmp_url = PLATFORM_URLS[p] || '';
                };"""

content = content.replace(old_change, new_change)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
