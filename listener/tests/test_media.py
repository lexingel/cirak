import media


def test_pause_and_play_always_press_and_say_what_the_meter_saw(monkeypatch):
    pressed = []
    monkeypatch.setattr(media, "press", pressed.append)
    assert media.plan("pause", playing=False) == media.plan("play", playing=True) == "toggle"
    assert media.run("pause", playing=True) == "pause"  # was playing: now paused
    assert media.run("pause", playing=False) == "play"  # quiet passage? the key still goes
    assert media.run("play", playing=False) == "play"
    assert pressed == [media.KEYS["toggle"]] * 3


def test_skip_and_volume():
    assert media.plan("next", True) == "next" and media.plan("prev", False) == "prev"
    assert media.plan("up", True) == media.plan("mute", False) == "volume"
