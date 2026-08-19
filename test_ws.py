import asyncio
import websockets
import json

async def test():
    try:
        # Pterodactyl container localhost
        uri = "ws://127.0.0.1:4455"
        async with websockets.connect(uri) as ws:
            print("Connected to WebSocket!")
            # Request StartStream
            req = {
                "op": 6,
                "d": {
                    "requestType": "StartStream",
                    "requestId": "1"
                }
            }
            await ws.send(json.dumps(req))
            resp = await ws.recv()
            print("Response:", resp)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
