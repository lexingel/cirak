"""Mic capture, a simple speech detector, and local Whisper. Audio never leaves this machine."""
import numpy as np

RATE = 16000
BLOCK = 480  # 30 ms
START_BLOCKS = 9  # ~270 ms of sustained sound before it counts as speech (key clicks don't)
SILENCE_END = 1.5  # seconds of quiet that ends an utterance
MAX_SECONDS = 30  # steady noise (fan, hum) never ends on its own; cut it here


class Detector:
    """Energy-based speech start/end. Pure logic, fed one block at a time."""

    def __init__(self, on_start, on_end):
        self.on_start, self.on_end = on_start, on_end
        self._pending: list = []
        self._chunks: list = []
        self._quiet = 0.0
        self.talking = False

    def reset(self):
        self._pending, self._chunks, self._quiet, self.talking = [], [], 0.0, False

    def feed(self, block, loud: bool) -> None:
        if not self.talking:
            if not loud:
                self._pending = []
                return
            self._pending.append(block)
            if len(self._pending) >= START_BLOCKS:
                self.talking, self._chunks, self._pending, self._quiet = True, self._pending, [], 0.0
                self.on_start()
            return
        self._chunks.append(block)
        self._quiet = 0.0 if loud else self._quiet + BLOCK / RATE
        if self._quiet >= SILENCE_END or len(self._chunks) * BLOCK / RATE >= MAX_SECONDS:
            audio = np.concatenate(self._chunks)
            self.reset()
            self.on_end(audio)


class Hearing:
    # ponytail: energy VAD, swap for silero if noisy rooms misfire
    def __init__(self, on_start, on_end, threshold: float = 0.015):
        import sounddevice as sd
        self.threshold = threshold
        self.detector = Detector(on_start, on_end)
        self._stream = sd.InputStream(samplerate=RATE, channels=1, blocksize=BLOCK,
                                      dtype="float32", callback=self._cb)

    def start(self):
        self._stream.start()

    def stop(self):
        self._stream.stop()
        self.detector.reset()

    def _cb(self, data, frames, t, status):
        block = data[:, 0].copy()
        self.detector.feed(block, float(np.sqrt(np.mean(block ** 2))) > self.threshold)


_model = None


def transcribe(audio, lang: str = "en") -> str:
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        try:
            _model = WhisperModel("small", device="cuda", compute_type="float16")
        except Exception:
            _model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _model.transcribe(audio, language=lang, vad_filter=True)
    # Drop segments Whisper itself thinks are not speech (where hallucinations come from).
    return " ".join(s.text.strip() for s in segs if s.no_speech_prob < 0.6 and s.avg_logprob > -1.0)
