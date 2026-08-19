from aiohttp import web
import asyncio

async def _panel(r): return web.Response(text="Panel")

app = web.Application()
app.router.add_get("/", _panel)
app.router.add_get("/panel", _panel)
app.router.add_static("/panel", ".")

print("Static added successfully without ValueError")
