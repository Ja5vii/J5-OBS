filepath = r'e:\GitHub\J5-OBS\panel\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update platform URL map in JS
old_urls = """const PLATFORM_URLS = {
                    Twitch: 'rtmp://live.twitch.tv/app/',
                    YouTube: 'rtmp://a.rtmp.youtube.com/live2/',
                    Kick: 'rtmp://fa723fc1b171.global-contribute.live-video.net/app/'
                };"""

new_urls = """const PLATFORM_URLS = {
                    Twitch: 'rtmps://ingest.global-contribute.live-video.net/app/',
                    TwitchES: 'rtmps://mad02.contribute.live-video.net/app/',
                    YouTube: 'rtmps://a.rtmp.youtube.com/live2/',
                    Kick: 'rtmps://fa723fc1b171.global-contribute.live-video.net/app/'
                };"""

content = content.replace(old_urls, new_urls)

# 2. Update the platform select options to add Twitch ES
old_options = """                            <option value="Twitch">Twitch</option>
                            <option value="YouTube">YouTube</option>
                            <option value="Kick">Kick</option>
                            <option value="Custom">Custom RTMP</option>"""

new_options = """                            <option value="Twitch">Twitch (Global)</option>
                            <option value="TwitchES">Twitch (Espana)</option>
                            <option value="YouTube">YouTube</option>
                            <option value="Kick">Kick</option>
                            <option value="Custom">Custom RTMP</option>"""

content = content.replace(old_options, new_options)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
