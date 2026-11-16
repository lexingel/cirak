import main


def test_hide_and_show_tell_the_app():
    sent = []
    acts = main.make_actions(lambda: False, lambda fn: fn(), sent.append)
    assert acts["hide"]("", "tr", None) == ""
    assert acts["show"]("", "tr", None) == "Buradayım"
    assert sent == [{"type": "hide", "seconds": 3600}, {"type": "show"}]


def test_claude_answer_is_marked_online(monkeypatch):
    said = []
    monkeypatch.setattr(main.assistants, "ask_claude", lambda t, lang: "42")
    main.make_actions(lambda: False, lambda fn: fn())["ask_claude"]("x", "en", said.append)
    assert said == ["42\n(Claude, online)"]


def test_breakdown_says_numbered_steps(monkeypatch):
    said = []
    monkeypatch.setattr(main.asker, "breakdown", lambda t, lang: ["Clear the counter", "Sweep"])
    first = main.make_actions(lambda: False, lambda fn: fn())["breakdown"]("kitchen", "en", said.append)
    assert "kitchen" in first
    assert said == ["1. Clear the counter\n2. Sweep"]


def test_breakdown_without_model_points_to_the_menu(monkeypatch):
    said = []
    monkeypatch.setattr(main.asker, "breakdown", lambda t, lang: None)
    main.make_actions(lambda: False, lambda fn: fn())["breakdown"]("mutfak", "tr", said.append)
    assert "Soru modeli" in said[0]
