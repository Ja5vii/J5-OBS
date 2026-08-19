filepath = r'e:\GitHub\J5-OBS\instance-manager\api.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

middleware = """@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status == 404 and response.content_type != 'application/json':
            return web.json_response({"error": "Not Found"}, status=404)
        return response
    except web.HTTPException as ex:
        if ex.status == 404:
            return web.json_response({"error": "Route not found"}, status=404)
        raise
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"API Error: {err}")
        return web.json_response({"error": f"Internal Server Error: {str(e)}"}, status=500)

"""

if "def error_middleware" not in content:
    content = content.replace("def create_api_app(manager):", middleware + "def create_api_app(manager):")
    content = content.replace("app = web.Application()", "app = web.Application(middlewares=[error_middleware])")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added middleware")
else:
    print("Middleware already added")
