import random
from asker import ask, FALLBACK

NO_LOCAL = lambda ctx, lang: None


def test_local_model_reply_is_used():
    q = ask("aligning menu buttons", lang="en", local=lambda c, l: "Which button bugs you most?")
    assert q == "Which button bugs you most?"


def test_local_fails_falls_back_in_language():
    assert ask("x", lang="en", local=NO_LOCAL, rng=random.Random(1)) in FALLBACK["en"]
    assert ask("x", lang="tr", local=NO_LOCAL, rng=random.Random(1)) in FALLBACK["tr"]


def test_narration_never_goes_online_even_with_a_key(monkeypatch):
    # README promise: only "ask/tell Claude" leave the PC; a dev key in the environment changes nothing
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    assert ask("x", lang="en", local=NO_LOCAL, rng=random.Random(1)) in FALLBACK["en"]


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
    _fake_open(monkeypatch, b'{"models": [{"name": "%s"}]}' % asker.LOCAL_MODEL.encode())  # whichever this PC uses
    assert asker.brain_state() == "ok"


def test_default_model_has_a_free_licence():
    import asker
    assert asker.DEFAULT_MODEL == "qwen2.5:1.5b"  # Apache 2.0; 3b is research-only


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


def test_model_file_overrides_the_default(tmp_path):
    import asker
    f = tmp_path / "model.txt"
    assert asker.model_name(f) == "qwen2.5:1.5b"
    f.write_text(" qwen2.5:3b\n", encoding="utf-8")
    assert asker.model_name(f) == "qwen2.5:3b"


def test_picking_a_model_saves_it_and_only_known_ones(tmp_path):
    import asker
    f = tmp_path / "model.txt"
    old = asker.LOCAL_MODEL
    try:
        assert asker.set_model("qwen2.5:7b", f) is True
        assert asker.LOCAL_MODEL == "qwen2.5:7b" and asker.model_name(f) == "qwen2.5:7b"
        assert asker.set_model("evil; rm -rf", f) is False and asker.LOCAL_MODEL == "qwen2.5:7b"
    finally:
        asker.LOCAL_MODEL = old
    assert set(asker.MODELS) == {"qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b"}


def test_breakdown_parses_numbered_steps():
    from asker import breakdown
    reply = "Sure!\n1. Clear the counter\n2) Put dishes in the sink\n- Wipe the table\n3. Sweep\n4. Mop\n5. Rest\n6. Extra"
    assert breakdown("kitchen", "en", local=lambda s, u: reply) == [
        "Clear the counter", "Put dishes in the sink", "Wipe the table", "Sweep", "Mop"]


def test_breakdown_without_model_or_with_junk_is_none():
    from asker import breakdown
    assert breakdown("kitchen", "en", local=lambda s, u: None) is None
    assert breakdown("kitchen", "en", local=lambda s, u: "I can't help with that.") is None


def test_breakdown_that_copies_the_example_is_none():
    from asker import breakdown, STEPS
    assert breakdown("mutfağı toplamak", "tr", local=lambda s, u: STEPS["tr"][1][1]) is None


def test_mod_questions(tmp_path):
    from asker import mod_questions
    d = tmp_path / "questions" / "tr"
    d.mkdir(parents=True)
    (d / "benim.txt").write_text("# yorum\nKahven bitti mi?\n\n  Bugün hangi şarkı?  \n", encoding="utf-8")
    assert mod_questions("tr", tmp_path) == ["Kahven bitti mi?", "Bugün hangi şarkı?"]
    assert mod_questions("en", tmp_path) == []


def test_mod_questions_mix_in(monkeypatch):
    import asker
    monkeypatch.setattr(asker, "mod_questions", lambda lang, root=None: ["Mine?"])
    rng = random.Random(1)
    got = [ask("ctx", "en", local=lambda c, l: "Model question?", rng=rng) for _ in range(300)]
    assert 60 < got.count("Mine?") < 140 and got.count("Model question?") > 150
