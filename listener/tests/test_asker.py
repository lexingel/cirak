import random, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from asker import ask, FALLBACK


class Boom:
    class messages:
        @staticmethod
        def create(**k):
            raise RuntimeError("offline")


class Fake:
    def __init__(self, text):
        self.text = text

    @property
    def messages(self):
        t = self.text

        class M:
            @staticmethod
            def create(**k):
                assert k["model"] == "claude-haiku-5-5"
                return type("R", (), {"content": [type("C", (), {"text": t})()]})()
        return M


def test_uses_model_reply():
    assert ask("buton hizası", client=Fake("Hangi buton en çok canını sıkıyor?")) == "Hangi buton en çok canını sıkıyor?"


def test_falls_back_on_error():
    assert ask("x", client=Boom(), rng=random.Random(1)) in FALLBACK


def test_falls_back_on_too_long():
    assert ask("x", client=Fake(" ".join(["kelime"] * 20))) in FALLBACK


def test_falls_back_on_empty():
    assert ask("x", client=Fake("   ")) in FALLBACK


def test_fallback_list_shape():
    assert len(FALLBACK) == 18 and all(len(q.split()) <= 15 for q in FALLBACK)
