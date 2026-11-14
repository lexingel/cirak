"""Decides when the apprentice may ask a question. Never when the user is silent."""

HALLUCINATIONS = ("altyazı m.k", "izlediğiniz için teşekkür", "abone olmayı unutmayın")
MIN_UTTERANCE_WORDS = 3  # "hmm", "tamam", "Teşekkürler." on noise never count, even added up
LEVELS = {"low": 600, "mid": 300, "high": 120}
WINDOW = 180  # seconds of narration kept


class QuestionGate:
    def __init__(self, min_interval: float = 300, min_words: int = 8):
        self.min_interval = min_interval
        self.min_words = min_words
        self._buf: list[tuple[float, str]] = []
        self._last_asked = float("-inf")

    def add_text(self, text: str, now: float) -> None:
        text = text.strip()
        if len(text.split()) < MIN_UTTERANCE_WORDS or any(h in text.lower() for h in HALLUCINATIONS):
            return
        self._buf.append((now, text))
        self._trim(now)

    def _trim(self, now: float) -> None:
        self._buf = [(t, s) for t, s in self._buf if now - t <= WINDOW]

    def should_ask(self, now: float) -> bool:
        self._trim(now)
        words = sum(len(s.split()) for _, s in self._buf)
        return words >= self.min_words and now - self._last_asked >= self.min_interval

    def context(self) -> str:
        return " ".join(s for _, s in self._buf)

    def mark_asked(self, now: float) -> None:
        self._buf.clear()
        self._last_asked = now

    def pause(self) -> None:
        self._buf.clear()

    def set_level(self, level: str) -> None:
        self.min_interval = LEVELS.get(level, self.min_interval)
