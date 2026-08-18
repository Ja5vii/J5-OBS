import os

filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

upload_func = '''
@auth
@require_admin
async def upload_branding_logo(request):
    try:
        import base64
        import uuid
        import os
        
        data = await request.json()
        filename = data.get("filename", "logo.png")
        image_data = data.get("image_data", "")
        
        if not image_data:
            return web.json_response({"error": "No image data provided"}, status=400)
            
        if "," in image_data:
            header, b64_data = image_data.split(",", 1)
        else:
            b64_data = image_data
            
        asset_id = str(uuid.uuid4())
        safe_filename = f"{asset_id}_{filename}"
        
        assets_dir = os.path.join(manager.base_dir, "j5-obs", "branding_assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        file_path = os.path.join(assets_dir, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(b64_data))
            
        await manager.db.save_asset(asset_id, "image", safe_filename, request["user"]["id"])
        
        return web.json_response({"ok": True, "asset_id": asset_id, "filename": safe_filename})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
'''

content = content.replace('@auth\n@require_admin\nasync def publish_branding(request):', upload_func + '\n@auth\n@require_admin\nasync def publish_branding(request):')
content = content.replace('app.router.add_post("/api/admin/branding", publish_branding)', 'app.router.add_post("/api/admin/branding", publish_branding)\n    app.router.add_post("/api/admin/branding/upload", upload_branding_logo)')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
