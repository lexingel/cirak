"""Mic capture, a simple speech detector, and local Whisper. Audio never leaves this machine."""
import numpy as np

RATE = 16000
BLOCK = 480  # 30 ms
START_BLOCKS = 9  # ~270 ms of sustained sound before it counts as speech (key clicks don't)
SILENCE_END = 1.5  # seconds of quiet that ends an utterance
MAX_SECONDS = 30  # steady noise (fan, hum) never ends on its own; cut it here
PTT_MAX = 15  # seconds; a push-to-talk key stuck down still ends
HOTWORDS = "Çırak, Claude"  # spelling help, push-to-talk only (app names here pushed Turkish into English)


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


def input_mics(devices) -> list[str]:
    """Mics Windows has enabled, once each (MME list: it resamples to 16 kHz for us)."""
    return [d["name"] for d in devices if d["hostapi"] == 0 and d["max_input_channels"] > 0
            and not d["name"].startswith("Microsoft Sound Mapper")]


def device_index(devices, name: str):
    """Index of the chosen mic, or None (= Windows default) if it's gone or none was chosen."""
    for i, d in enumerate(devices):
        if name and d["hostapi"] == 0 and d["max_input_channels"] > 0 and d["name"] == name:
            return i
    return None


class Loudness:
    """Is this block louder than the room? Tracks the noise floor so a fan or hum stops counting as speech.

    The floor drops fast on quiet blocks and creeps up slowly (~30 s) under steady sound; talking
    has gaps, so it never pulls the floor up to speech level.
    """
    RISE = 0.001  # per 30 ms block
    FALL = 0.1

    def __init__(self, threshold: float = 0.015):
        self.threshold = threshold
        self.floor = threshold / 3

    def __call__(self, rms: float) -> bool:
        rate = self.FALL if rms < self.floor else self.RISE
        self.floor += rate * (rms - self.floor)
        return rms > max(self.threshold, 3 * self.floor)


class Hearing:
    # ponytail: energy VAD + noise floor, swap for silero if noisy rooms still misfire
    def __init__(self, on_start, on_end, threshold: float = 0.015, device: str = "",
                 ptt=None, on_ptt_start=None, on_ptt_end=None):
        import sounddevice as sd
        self.loud = Loudness(threshold)
        self.detector = Detector(on_start, on_end)
        self.ptt = PushToTalk(ptt, on_ptt_start, on_ptt_end) if ptt else None
        self._stream = sd.InputStream(device=device_index(sd.query_devices(), device),
                                      samplerate=RATE, channels=1, blocksize=BLOCK,
                                      dtype="float32", callback=self._cb)

    def start(self):
        self._stream.start()

    def stop(self):
        self._stream.stop()
        self.detector.reset()

    def close(self):
        self._stream.close()
        self.detector.reset()

    def _cb(self, data, frames, t, status):
        block = data[:, 0].copy()
        if self.ptt and self.ptt.feed(block):
            self.detector.reset()  # held key: this is a command, not narration
            return
        self.detector.feed(block, self.loud(float(np.sqrt(np.mean(block ** 2)))))


class PushToTalk:
    """While `held()` is true every block is kept, whatever its loudness (music may be playing);
    on release the whole clip goes to on_end. Pure logic, fed one block at a time."""

    def __init__(self, held, on_start, on_end):
        self.held, self.on_start, self.on_end = held, on_start, on_end
        self._chunks: list = []

    def feed(self, block) -> bool:
        """True if the block was taken (key held, or just released)."""
        if self.held() and len(self._chunks) * BLOCK / RATE < PTT_MAX:
            if not self._chunks:
                self.on_start()
            self._chunks.append(block)
            return True
        if self._chunks:
            audio, self._chunks = np.concatenate(self._chunks), []
            self.on_end(audio)
            return True
        return False


_model = None


def _load(device: str):
    from faster_whisper import WhisperModel
    from paths import DATA
    # per-user model folder: first run downloads ~460 MB there, the install folder can stay read-only
    return WhisperModel("small", device=device, compute_type="float16" if device == "cuda" else "int8",
                        download_root=str(DATA / "models"))


def keep(segs) -> str:
    """Drop segments Whisper itself thinks are not speech (where hallucinations come from)."""
    return " ".join(s.text.strip() for s in segs if s.no_speech_prob < 0.6 and s.avg_logprob > -1.0)


def _run(audio, lang, hotwords=None):
    segs, _ = _model.transcribe(audio, language=lang, vad_filter=True, hotwords=hotwords)
    return keep(segs)


def transcribe(audio, lang: str = "en", hotwords=None) -> str:
    global _model
    if _model is None:
        try:
            _model = _load("cuda")
        except Exception:
            _model = _load("cpu")
    try:
        return _run(audio, lang, hotwords)
    except Exception as e:
        # The GPU model can load and still fail on first use (a CUDA DLL missing): go CPU for good.
        if getattr(_model, "_cpu", False):
            raise
        print("listener: GPU transcribe failed, using CPU:", e, file=__import__("sys").stderr)
        _model = _load("cpu")
        _model._cpu = True
        return _run(audio, lang, hotwords)


if __name__ == "__main__":
    # Mic level meter: python hearing.py  -> 10 s of RMS readings (quiet / typing / talking)
    import time
    import sounddevice as sd
    loud = Loudness()

    def show(data, frames, t, status):
        rms = float(np.sqrt(np.mean(data[:, 0] ** 2)))
        is_loud = loud(rms)
        print(f"rms {rms:.4f}  floor {loud.floor:.4f}  {'LOUD' if is_loud else ''}")

    with sd.InputStream(samplerate=RATE, channels=1, blocksize=BLOCK * 10, dtype="float32", callback=show):
        time.sleep(10)
