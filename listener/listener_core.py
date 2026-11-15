"""Listener logic, free of audio and network so it can be tested."""
import collections
import random
import time

import commands
from gate import QuestionGate, worth_keeping


class Listener:
    def __init__(self, send, transcribe, ask, call_busy, speaker_busy, clock=time.monotonic,
                 actions=None, transcribe_cmd=None):
        self.send, self.transcribe, self.ask = send, transcribe, ask
        self.call_busy, self.speaker_busy, self.clock = call_busy, speaker_busy, clock
        # intent -> fn(arg, lang, say) returning the bubble text (or None if it says it later itself)
        self.actions = actions or {}
        self.transcribe_cmd = transcribe_cmd or transcribe
        self.gate = QuestionGate()
        self.mic_on = True
        self.paused = False
        self._heard = False
        self._told_no_model = False
        self.lang = "en"
        self.device = ""  # chosen mic name, "" = Windows default
        self.ptt_vk = 0xA3  # push-to-talk key (Windows key code), Right Ctrl until the app sends its own
        self.recent = collections.deque(maxlen=10)  # "where was I": RAM only, gone when the listener exits
        self._openings = collections.deque(maxlen=3)  # the last three "let's start" openings, not repeated

    @property
    def listening(self) -> bool:
        return self.mic_on and not self.paused

    def tick(self) -> None:
        busy = self.call_busy()
        if busy and not self.paused:
            self.paused = True
            self.gate.pause()
            msg = {"type": "paused", "reason": "call"}
            if isinstance(busy, str):
                msg["who"] = busy  # shown in the right-click menu, so a silent apprentice has a reason
            self.send(msg)
        elif not busy and self.paused:
            self.paused = False
            self.send({"type": "resumed"})

    def speech_start(self) -> None:
        # Speaker playing -> probably a video or music, not the user: don't even look up.
        self._heard = self.listening and not self.speaker_busy()
        if self._heard:
            self.send({"type": "speech_start"})

    def speech_end(self, audio) -> None:
        if not (self.listening and self._heard) or self.speaker_busy():
            if self._heard:
                self.send({"type": "speech_end"})
            self._heard = False
            return
        self._heard = False
        text = self._hear(self.transcribe, audio)
        if text is None:
            self.send({"type": "speech_end"})
            return
        if self._command(text):
            return
        if not self._narrate(text):  # a question goes straight from listening to asking
            self.send({"type": "speech_end"})

    def ptt_start(self) -> None:
        if self.listening:
            self.send({"type": "speech_start"})

    def ptt_end(self, audio) -> None:
        """Push-to-talk released: what was said is a command, even over music (no speaker gate)."""
        if not self.listening:
            return
        text = None if audio is None else self._hear(self.transcribe_cmd, audio)  # None: cancelled
        if not (text or "").strip():
            self.send({"type": "speech_end"})
            return
        self._command(text, ptt=True)

    def _hear(self, fn, audio):
        """Transcribed text, or None if Whisper failed (then the apprentice must leave LISTENING)."""
        try:
            return fn(audio, self.lang)
        except Exception as e:
            print("listener: transcribe failed:", e, file=__import__("sys").stderr)
            if not self._told_no_model:  # once: no model (offline first start), no DLL, ...
                self._told_no_model = True
                self.say(commands.reply(self.lang, "no_model"))
            return None

    def warm(self, silence, fresh: bool) -> None:
        """Loads Whisper now, not on the first sentence. fresh: the model isn't downloaded yet."""
        if fresh:
            self.say(commands.reply(self.lang, "downloading"))
        if self._hear(self.transcribe, silence) is not None and fresh:
            self.say(commands.reply(self.lang, "ready"))

    def say(self, text: str) -> None:
        self.send({"type": "say", "text": text})

    def _command(self, text: str, ptt: bool = False) -> bool:
        """Runs it if it's a command; returns whether it was one (then it is never narration)."""
        cmd = commands.parse(text, ptt)
        if cmd is None:
            return False
        intent, arg = cmd
        if intent == "start":
            self._open_session()
            return True
        if intent == "recall":
            last = list(self.recent)[-2:]
            self.say(commands.reply(self.lang, "recall", " … ".join(last)) if last else commands.reply(self.lang, "recall_none"))
            return True
        act = self.actions.get(intent)
        try:
            msg = act(arg, self.lang, self.say) if act else commands.reply(self.lang, "unknown")
        except Exception as e:
            print("listener: command", intent, "failed:", e, file=__import__("sys").stderr)
            msg = commands.reply(self.lang, "unknown")
        if msg:
            self.say(msg)
        return True

    def _open_session(self) -> None:
        """The user said "let's start": one opening question, never one of the last three."""
        q = random.choice([o for o in commands.OPENINGS[self.lang] if o not in self._openings])
        self._openings.append(q)
        self.gate.mark_asked(self.clock())  # no regular question right on top of it
        self.send({"type": "question", "text": q})

    def _narrate(self, text: str) -> bool:
        """Adds what the user said; asks if it's time. Returns whether a question went out."""
        now = self.clock()
        if worth_keeping(text):
            self.recent.append(text.strip())
        self.gate.add_text(text, now)
        if self.gate.should_ask(now):
            q = self.ask(self.gate.context(), self.lang)
            self.gate.mark_asked(now)
            self.send({"type": "question", "text": q})
            return True
        return False

    def on_client(self, msg: dict) -> None:
        t = msg.get("type")
        if t == "typed" and str(msg.get("text", "")).strip():
            if not self._command(str(msg["text"])):
                self._narrate(str(msg["text"]))
        elif t == "mic":
            self.mic_on = bool(msg.get("on"))
        elif t == "lang" and msg.get("lang") in ("en", "tr"):
            self.lang = msg["lang"]
        elif t == "ptt_key" and isinstance(msg.get("vk"), int) and 0 < msg["vk"] < 0xFF and msg["vk"] != 0x1B:
            self.ptt_vk = msg["vk"]
        elif t == "mic_device":
            self.device = str(msg.get("name", ""))
        elif t == "frequency":
            self.gate.set_level(str(msg.get("level")))
