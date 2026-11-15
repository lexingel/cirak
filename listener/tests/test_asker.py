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


def test_local_request_keeps_model_loaded(monkeypatch):
    import asker, io, json as j
    sent = {}

    def fake_urlopen(req, timeout):
        sent.update(j.loads(req.data))
        return io.BytesIO(b'{"message": {"content": "What next?"}}')
    monkeypatch.setattr(asker.urllib.request, "urlopen", fake_urlopen)
    assert asker.ask_local("x", "en") == "What next?"
    assert sent["keep_alive"] == asker.KEEP_ALIVE  # questions come minutes apart; default 5m unload = 30s cold load


def test_reply_that_is_not_a_question_is_dropped():
    import asker
    assert asker._clean("You should take a break and drink water.") is None
    assert asker._clean("Which color is winning so far?") == "Which color is winning so far?"


def test_prompt_keeps_the_potion_out_of_the_users_work():
    import asker
    assert "never ask about potions" in asker.SYSTEM["en"]


def _fake_open(monkeypatch, reply):
    import asker, io
    def fake(req, timeout=None):
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(reply)
    monkeypatch.setattr(asker.urllib.request, "urlopen", fake)


def test_brain_state_tells_missing_ollama_from_missing_model(monkeypatch):
    import asker
    _fake_open(monkeypatch, OSError("refused"))
    assert asker.brain_state() == "no_ollama"
    _fake_open(monkeypatch, b'{"models": [{"name": "llama3.2:3b"}]}')
    assert asker.brain_state() == "no_model"
    _fake_open(monkeypatch, b'{"models": [{"name": "%s"}]}' % asker.LOCAL_MODEL.encode())
    assert asker.brain_state() == "ok"


def test_default_model_has_a_free_licence():
    import asker
    assert asker.LOCAL_MODEL == "qwen2.5:1.5b" or "CIRAK_MODEL" in __import__("os").environ  # Apache 2.0; 3b is research-only


def test_pull_reports_progress_in_quarters(monkeypatch):
    import asker
    lines = b"\n".join([b'{"status":"pulling manifest"}', b'{"status":"downloading","total":100,"completed":30}',
                        b'{"status":"downloading","total":100,"completed":31}',
                        b'{"status":"downloading","total":100,"completed":80}', b'{"status":"success"}'])
    _fake_open(monkeypatch, lines)
    seen = []
    assert asker.pull(seen.append) is True
    assert seen == [25, 75]
    _fake_open(monkeypatch, OSError("no network"))
    assert asker.pull(seen.append) is False
