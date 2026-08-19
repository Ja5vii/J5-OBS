filepath = r'e:\GitHub\J5-OBS\instance-manager\process_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'env = os.environ.copy()',
    'env = os.environ.copy()\n        env["LIBGL_ALWAYS_SOFTWARE"] = "1"\n        env["GALLIUM_DRIVER"] = "llvmpipe"'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
