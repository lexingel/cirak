"""Mic capture, a simple speech detector, and local Whisper. Audio never leaves this machine."""
import numpy as np
import sounddevice as sd

RATE = 16000
BLOCK = 480  # 30 ms
SILENCE_END = 1.5  # seconds of quiet that ends an utterance


class Hearing:
    # ponytail: energy VAD, swap for silero if noisy rooms misfire
    def __init__(self, on_start, on_end, threshold: float = 0.015):
        self.on_start, self.on_end, self.threshold = on_start, on_end, threshold
        self._chunks, self._quiet, self._talking = [], 0.0, False
        self._stream = sd.InputStream(samplerate=RATE, channels=1, blocksize=BLOCK,
                                      dtype="float32", callback=self._cb)

    def start(self):
        self._stream.start()

    def stop(self):
        self._stream.stop()
        self._chunks, self._talking = [], False

    def _cb(self, data, frames, t, status):
        block = data[:, 0].copy()
        loud = float(np.sqrt(np.mean(block ** 2))) > self.threshold
        if loud and not self._talking:
            self._talking, self._chunks = True, []
            self.on_start()
        if self._talking:
            self._chunks.append(block)
            self._quiet = 0.0 if loud else self._quiet + BLOCK / RATE
            if self._quiet >= SILENCE_END:
                self._talking = False
                self.on_end(np.concatenate(self._chunks))


_model = None


def transcribe(audio) -> str:
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        try:
            _model = WhisperModel("small", device="cuda", compute_type="float16")
        except Exception:
            _model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _model.transcribe(audio, language="tr", vad_filter=True)
    return " ".join(s.text.strip() for s in segs)
