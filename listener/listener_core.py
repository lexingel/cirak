"""Listener logic, free of audio and network so it can be tested."""
import time

from gate import QuestionGate


class Listener:
    def __init__(self, send, transcribe, ask, call_busy, speaker_busy, clock=time.monotonic):
        self.send, self.transcribe, self.ask = send, transcribe, ask
        self.call_busy, self.speaker_busy, self.clock = call_busy, speaker_busy, clock
        self.gate = QuestionGate()
        self.mic_on = True
        self.paused = False

    @property
    def listening(self) -> bool:
        return self.mic_on and not self.paused

    def tick(self) -> None:
        busy = self.call_busy()
        if busy and not self.paused:
            self.paused = True
            self.gate.pause()
            self.send({"type": "paused", "reason": "call"})
        elif not busy and self.paused:
            self.paused = False
            self.send({"type": "resumed"})

    def speech_start(self) -> None:
        if self.listening:
            self.send({"type": "speech_start"})

    def speech_end(self, audio) -> None:
        if not self.listening:
            return
        if self.speaker_busy():  # probably a video or music, not the user
            self.send({"type": "speech_end"})
            return
        text = self.transcribe(audio)
        self.send({"type": "speech_end"})
        self._narrate(text)

    def _narrate(self, text: str) -> None:
        now = self.clock()
        self.gate.add_text(text, now)
        if self.gate.should_ask(now):
            q = self.ask(self.gate.context())
            self.gate.mark_asked(now)
            self.send({"type": "question", "text": q})

    def on_client(self, msg: dict) -> None:
        t = msg.get("type")
        if t == "typed" and str(msg.get("text", "")).strip():
            self._narrate(str(msg["text"]))
        elif t == "mic":
            self.mic_on = bool(msg.get("on"))
        elif t == "frequency":
            self.gate.set_level(str(msg.get("level")))
