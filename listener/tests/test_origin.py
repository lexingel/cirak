import asyncio, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import websockets
from main import SERVE_KW


def test_browser_origin_rejected_local_app_allowed():
    async def go():
        async def h(ws, *_):
            await ws.send("hi")
        async with websockets.serve(h, "127.0.0.1", 47699, **SERVE_KW):
            async with websockets.connect("ws://127.0.0.1:47699") as ws:
                assert await ws.recv() == "hi"
            try:
                async with websockets.connect("ws://127.0.0.1:47699", origin="http://evil.example"):
                    return False
            except Exception:
                return True
    assert asyncio.run(go())
