import random, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from asker import ask, FALLBACK

NO_LOCAL = lambda ctx, lang: None


class Boom:
    class messages:
        @staticmethod
        def create(**k):
            raise RuntimeError("offline")


class Fake:
    def __init__(self, text):
        self.text, self.calls = text, []

    @property
    def messages(self):
        outer = self

        class M:
            @staticmethod
            def create(**k):
                outer.calls.append(k)
                return type("R", (), {"content": [type("C", (), {"text": outer.text})()]})()
        return M


def test_local_model_reply_is_used():
    q = ask("aligning menu buttons", lang="en", local=lambda c, l: "Which button bugs you most?")
    assert q == "Which button bugs you most?"


def test_local_fails_no_key_falls_back_in_language(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ask("x", lang="en", local=NO_LOCAL, rng=random.Random(1)) in FALLBACK["en"]
    assert ask("x", lang="tr", local=NO_LOCAL, rng=random.Random(1)) in FALLBACK["tr"]


def test_haiku_used_when_given_and_thinking_off():
    f = Fake("Hangi buton en çok canını sıkıyor?")
    assert ask("buton hizası", lang="tr", local=NO_LOCAL, client=f) == "Hangi buton en çok canını sıkıyor?"
    assert f.calls[0]["model"] == "claude-haiku-5-5"
    assert f.calls[0]["thinking"] == {"type": "disabled"}


def test_haiku_error_falls_back():
    assert ask("x", lang="en", local=NO_LOCAL, client=Boom(), rng=random.Random(1)) in FALLBACK["en"]


def test_too_long_or_empty_falls_back():
    assert ask("x", lang="en", local=lambda c, l: " ".join(["word"] * 20)) in FALLBACK["en"]
    assert ask("x", lang="en", local=lambda c, l: "   ") in FALLBACK["en"]


def test_reply_quotes_and_prefix_stripped():
    assert ask("x", lang="en", local=lambda c, l: 'Question: "What comes next?"') == "What comes next?"


def test_fallback_lists_shape():
    for lang in ("en", "tr"):
        assert len(FALLBACK[lang]) == 18 and all(len(q.split()) <= 15 for q in FALLBACK[lang])
