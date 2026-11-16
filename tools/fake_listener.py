"""Fake listener: shows listening -> nod -> question -> paused without a mic.

Run (app closed first, so the real listener isn't holding the port):
    listener/.venv/Scripts/python tools/fake_listener.py
then open the app. It connects on its own and the scene repeats every 30 s.
Right-click during "paused" to see the reason line in the menu.
"""
import asyncio
import json

import websockets

SCENE = [  # (seconds after connect, message)
    (2, {"type": "speech_start"}),
    (5, {"type": "speech_end"}),
    (7, {"type": "question", "text": "What comes after this part?"}),
    (15, {"type": "paused", "who": "Discord.exe"}),
    (25, {"type": "resumed"}),
]


async def handler(ws, *_):
    print("app connected")
    try:
        while True:
            t0 = asyncio.get_running_loop().time()
            for at, msg in SCENE:
                await asyncio.sleep(max(0, t0 + at - asyncio.get_running_loop().time()))
                print("->", msg)
                await ws.send(json.dumps(msg))
            await asyncio.sleep(max(0, t0 + 30 - asyncio.get_running_loop().time()))
    except websockets.ConnectionClosed:
        print("app gone")


async def main():
    async with websockets.serve(handler, "127.0.0.1", 47613):
        print("fake listener on 47613, open the app")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
