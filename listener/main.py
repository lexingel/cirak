"""Runs the listener: mic -> Whisper -> question gate -> websocket to the Godot app."""
import asyncio
import json
import os
import queue
import sys
import threading

import websockets

import mic_guard
from asker import ask, ask_local
from hearing import Hearing, transcribe
from listener_core import Listener

PORT = 47613
IDLE_EXIT = 10  # seconds without the app -> quit, so no orphan mic stays open
# Browsers always send an Origin header; the Godot app sends none. Only Origin-less clients may connect.
SERVE_KW = {"origins": [None]}


async def run():
    loop = asyncio.get_running_loop()
    clients: set = set()
    work: queue.Queue = queue.Queue()

    def send(msg: dict):
        data = json.dumps(msg, ensure_ascii=False)
        for ws in list(clients):
            loop.call_soon_threadsafe(asyncio.ensure_future, ws.send(data))

    core = Listener(send=send, transcribe=transcribe, ask=ask,
                    call_busy=lambda: mic_guard.mic_in_use_by_other(mic_guard.read_mic_entries(), mic_guard.own_exes()),
                    speaker_busy=mic_guard.speaker_busy)

    # Transcribing and asking are slow; one worker thread keeps them off the audio callback.
    def worker():
        while True:
            fn, arg = work.get()
            try:
                fn(arg) if arg is not None else fn()
            except Exception as e:
                print("listener:", e, file=sys.stderr)

    threading.Thread(target=worker, daemon=True).start()
    work.put((lambda: transcribe(__import__("numpy").zeros(16000, "float32")), None))  # warm the model
    work.put((lambda: ask_local("warming up", "en"), None))  # load the local model now, not on the first question
    hearing = Hearing(on_start=lambda: work.put((core.speech_start, None)),
                      on_end=lambda audio: work.put((core.speech_end, audio)))
    hearing.start()
    mic_running = True

    async def handler(ws, *_):
        clients.add(ws)
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                work.put((core.on_client, msg))
        finally:
            clients.discard(ws)

    async with websockets.serve(handler, "127.0.0.1", PORT, **SERVE_KW):
        idle = 0
        while True:
            await asyncio.sleep(1)
            work.put((core.tick, None))
            want = core.listening
            if want != mic_running:
                hearing.start() if want else hearing.stop()
                mic_running = want
            idle = 0 if clients else idle + 1
            if idle >= IDLE_EXIT:
                hearing.stop()
                os._exit(0)


if __name__ == "__main__":
    asyncio.run(run())
