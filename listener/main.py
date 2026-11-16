"""Runs the listener: mic -> Whisper -> question gate -> websocket to the Godot app."""
import asyncio
import json
import os
import queue
import sys
import threading
from pathlib import Path

from paths import DATA

# pythonw has no console: send errors to a file (errors only, never what the user said).
# Per-user folder, not next to the code: an install under Program Files can't write there.
if sys.stderr is None:
    DATA.mkdir(parents=True, exist_ok=True)
    sys.stderr = sys.stdout = open(DATA / "listener.log", "a", buffering=1, encoding="utf-8")

import websockets

import apps
import asker
import assistants
import commands
import keys
import media
import mic_guard
import screen
from hearing import HOTWORDS, Hearing, input_mics, transcribe
from listener_core import Listener

PORT = 47613
IDLE_EXIT = 10  # seconds without the app -> quit, so no orphan mic stays open
# Browsers always send an Origin header; the Godot app sends none. Only Origin-less clients may connect.
SERVE_KW = {"origins": [None]}


def quit_cleanly(hearing, exit=os._exit):
    """Close the mic stream properly, then exit. A hard kill mid-stream once took a USB audio
    interface (and the USB controller it sat on) down with it."""
    try:
        if hearing:
            hearing.close()
    except Exception as e:
        print("listener: closing mic:", e, file=sys.stderr)
    exit(0)


def make_actions(speaker_busy, spawn, send=lambda m: None):
    """What each spoken command does. Every fn(arg, lang, say) returns the bubble text."""
    def do_media(action, lang, say):
        return commands.reply(lang, media.run(action, speaker_busy()))

    def do_open(spoken, lang, say):
        target = apps.find(spoken, apps.load())
        if not target:
            return commands.reply(lang, "no_app", spoken.split("'")[0].capitalize())
        try:
            apps.launch(target)
        except OSError as e:  # gone from Windows' app list, or a wrong path in apps.json
            print("listener: open", target, e, file=sys.stderr)
            return commands.reply(lang, "cant_open", target)
        return commands.reply(lang, "opening", target)

    def do_ask(text, lang, say):
        def later():  # 5-20 s: off the worker thread so listening goes on
            answer = assistants.ask_claude(text, lang)
            say(commands.reply(lang, "online", answer) if answer else commands.reply(lang, "no_claude"))
        spawn(later)
        return commands.reply(lang, "asking", text)

    def do_task(text, lang, say):
        return commands.reply(lang, "task" if assistants.open_claude_task(text) else "no_claude")

    def do_hide(_, lang, say):  # "Çırak, saklan": an hour out of sight, "geri gel" brings it back
        send({"type": "hide", "seconds": 3600})
        return ""

    def do_show(_, lang, say):
        send({"type": "show"})
        return commands.reply(lang, "back")

    def do_breakdown(task, lang, say):
        def later():  # the local model needs a few seconds for five lines
            steps = asker.breakdown(task, lang)
            say("\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1)) if steps else commands.reply(lang, "no_brain"))
        spawn(later)
        return commands.reply(lang, "breaking", task)

    return {"media": do_media, "open": do_open, "ask_claude": do_ask, "claude_task": do_task,
            "hide": do_hide, "show": do_show, "breakdown": do_breakdown}


def run_job(fn, args) -> None:
    """One worker job. args is a tuple, so None (a cancelled command clip) is passed on, not dropped."""
    try:
        fn(*args)
    except Exception as e:
        print("listener:", e, file=sys.stderr)


def open_hearing(make):
    """The mic, or None if there is none (unplugged, no device): typing still works, no crash loop."""
    try:
        return make()
    except Exception as e:
        print("listener: no mic:", e, file=sys.stderr)
        return None


async def run():
    loop = asyncio.get_running_loop()
    clients: set = set()
    work: queue.Queue = queue.Queue()

    def send(msg: dict):
        data = json.dumps(msg, ensure_ascii=False)
        for ws in list(clients):
            # result is dropped on purpose: a send to a closing app is not worth a log line
            asyncio.run_coroutine_threadsafe(ws.send(data), loop).add_done_callback(lambda f: f.exception())

    core = Listener(send=send, transcribe=transcribe, ask=asker.ask,
                    call_busy=lambda: mic_guard.mic_user(mic_guard.read_mic_entries(), mic_guard.own_exes()),
                    speaker_busy=mic_guard.speaker_busy,
                    actions=make_actions(mic_guard.speaker_busy,
                                         lambda fn: threading.Thread(target=fn, daemon=True).start(),
                                         lambda m: send(m)),
                    transcribe_cmd=lambda a, lang: transcribe(a, lang, HOTWORDS))
    core.mic_on = False  # the mic stays shut until the app sends its saved setting (it does on connect)

    # Transcribing and asking are slow; one worker thread keeps them off the audio callback.
    def worker():
        while True:
            run_job(*work.get())

    threading.Thread(target=worker, daemon=True).start()
    def bg(fn):  # slow start-up jobs: never ahead of what the user types or says
        threading.Thread(target=fn, daemon=True).start()

    bg(apps.index)  # PowerShell, up to 20 s: now, not when the first "open" waits on it
    # state: None until Ollama was tried; mic: None until the privacy switches were read
    warm = {"state": None, "at": 0, "whisper": False, "lang": False, "app_mic": True, "pulling": False, "mic": None, "full": None, "no_mic": False}

    def brain_msg():
        return {"type": "brain", "state": warm["state"], "model": asker.LOCAL_MODEL}

    def warm_model(force=False):  # load the local model now, not on the first question; retried while Ollama boots
        state = asker.brain_state()
        if state == "ok" and asker.ask_local("warming up", "en") is None:
            state = "no_ollama"  # listed but not answering
        if state != warm["state"] or force:
            warm["state"] = state
            send(brain_msg())  # the menu offers Ollama / the model download, ticks the model

    def pick_model(name):  # menu: "Question model"; the user saw its size, so a missing one downloads now
        if asker.set_model(name):
            warm_model(force=True)
            if warm["state"] == "no_model":
                pull_model()

    def check_mic():  # Windows' microphone privacy switch: off = only silence, so say why
        blocked = not mic_guard.mic_allowed()
        if blocked != warm["mic"]:
            warm["mic"] = blocked
            send({"type": "mic_blocked", "blocked": blocked})

    def pull_model():  # menu: "download the question model"; asked for by the user, ~1 GB
        if warm["pulling"]:
            return
        warm["pulling"] = True
        core.say(commands.reply(core.lang, "pulling", 0))
        ok = asker.pull(lambda pct: core.say(commands.reply(core.lang, "pulling", pct)))
        warm["pulling"] = False
        core.say(commands.reply(core.lang, "pulled" if ok else "pull_failed"))
        if ok:
            warm_model()

    def warm_whisper():  # after the app sent its language: the first-run bubbles must reach it, in its words
        fresh = not any((DATA / "models").glob("models--Systran--faster-whisper-small/snapshots/*/model.bin"))
        core.warm(__import__("numpy").zeros(16000, "float32"), fresh)

    bg(warm_model)
    work.put((check_mic, ()))

    def make_hearing():
        return open_hearing(lambda: Hearing(on_start=lambda: work.put((core.speech_start, ())),
                                            on_end=lambda audio: work.put((core.speech_end, (audio,))),
                                            device=core.device, ptt=lambda: keys.key_down(core.ptt_vk),
                                            on_ptt_start=lambda: work.put((core.ptt_start, ())),
                                            on_ptt_end=lambda audio: work.put((core.ptt_end, (audio,))),
                                            chord=lambda: keys.other_key_down(core.ptt_vk)))

    def pick_key():
        vk = keys.wait_for_key()
        if vk is None:
            core.say(commands.reply(core.lang, "ptt_same"))
            return
        core.ptt_vk, name = vk, keys.key_name(vk)
        send({"type": "ptt_key", "vk": vk, "name": name})
        core.say(commands.reply(core.lang, "ptt_set", name))

    hearing = make_hearing()
    device = core.device
    mic_running = False  # the loop below starts it once listening is wanted

    async def handler(ws, *_):
        clients.add(ws)
        try:
            import sounddevice as sd
            # ponytail: list read at listener start; a mic plugged in later shows after an app restart
            await ws.send(json.dumps({"type": "mics", "list": input_mics(sd.query_devices())}, ensure_ascii=False))
        except Exception as e:
            print("listener: mic list:", e, file=sys.stderr)
        if warm["state"] is not None:
            await ws.send(json.dumps(brain_msg()))
        if warm["mic"] is not None:
            await ws.send(json.dumps({"type": "mic_blocked", "blocked": warm["mic"]}))
        await ws.send(json.dumps({"type": "fullscreen", "rect": warm["full"]}))
        await ws.send(json.dumps({"type": "no_mic", "none": hearing is None}))
        for m in core.hello():
            await ws.send(json.dumps(m, ensure_ascii=False))
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                if isinstance(msg, dict) and msg.get("type") == "bye":  # the app is closing
                    quit_cleanly(hearing)
                if isinstance(msg, dict) and msg.get("type") == "edit_apps":  # menu: "App list..."
                    work.put((apps.edit, ()))
                    continue
                if isinstance(msg, dict) and msg.get("type") == "pull_model":  # minutes: own thread
                    threading.Thread(target=pull_model, daemon=True).start()
                    continue
                if isinstance(msg, dict) and msg.get("type") == "model":  # may download: own thread
                    threading.Thread(target=pick_model, args=(str(msg.get("name", "")),), daemon=True).start()
                    continue
                if isinstance(msg, dict) and msg.get("type") == "pick_ptt_key":  # menu: "Command key..."
                    threading.Thread(target=pick_key, daemon=True).start()  # waits up to 10 s for a key
                    continue
                work.put((core.on_client, (msg,)))
                if isinstance(msg, dict) and msg.get("type") == "mic":
                    warm["app_mic"] = bool(msg.get("on"))
                if isinstance(msg, dict) and msg.get("type") == "lang":
                    warm["lang"] = True
                # Whisper after the app's language (its bubbles speak it), and only once the mic is on:
                # someone who only types never downloads ~460 MB or holds ~300 MB for it
                if warm["lang"] and warm["app_mic"] and not warm["whisper"]:
                    warm["whisper"] = True
                    bg(warm_whisper)  # first run downloads ~460 MB: typing works meanwhile
        except websockets.ConnectionClosed:
            pass  # the app closing without a goodbye is normal, not a log entry
        finally:
            clients.discard(ws)

    async with websockets.serve(handler, "127.0.0.1", PORT, **SERVE_KW):
        idle = 0
        while True:
            await asyncio.sleep(1)
            work.put((core.tick, ()))
            warm["at"] += 1
            if warm["state"] not in (None, "ok") and not warm["pulling"] and warm["at"] % 60 == 0:  # Ollama installed later
                bg(warm_model)
            if warm["at"] % 2 == 0:  # a game or video went fullscreen: the app steps aside on that monitor
                try:
                    full = screen.fullscreen_rect()
                except Exception as e:
                    print("listener: fullscreen check:", e, file=sys.stderr)
                    full = None
                if full != warm["full"]:
                    warm["full"] = full
                    send({"type": "fullscreen", "rect": full})
            if warm["at"] % 10 == 0:  # switched in Settings while running
                work.put((check_mic, ()))
            want = core.listening
            if core.device != device:  # the user picked another mic in the menu
                device = core.device
                if hearing:
                    hearing.close()
                hearing, mic_running = make_hearing(), False
            if hearing and want != mic_running:
                try:
                    hearing.start() if want else hearing.stop()
                    mic_running = want
                except Exception as e:  # device vanished: carry on without the mic
                    print("listener: mic lost:", e, file=sys.stderr)
                    hearing = None
            if hearing is None and warm["at"] % 30 == 0:  # plugged back in? try again now and then
                # ponytail: PortAudio's device list is read once; a mic first plugged in after start needs an app restart
                hearing, mic_running = make_hearing(), False
            if (hearing is None) != warm["no_mic"]:
                warm["no_mic"] = hearing is None
                send({"type": "no_mic", "none": warm["no_mic"]})  # red dot + a menu line, not a silent green
            idle = 0 if clients else idle + 1
            if idle >= IDLE_EXIT:
                quit_cleanly(hearing)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except OSError as e:
        if getattr(e, "winerror", None) != 10048:
            raise
        print("listener: already running (port", PORT, "in use)", file=sys.stderr)  # the app talks to that one
