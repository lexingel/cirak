import media


def test_toggle_only_when_it_changes_something():
    assert media.plan("pause", playing=True) == "toggle"
    assert media.plan("pause", playing=False) == "nothing_playing"
    assert media.plan("play", playing=False) == "toggle"
    assert media.plan("play", playing=True) == "already"


def test_skip_and_volume():
    assert media.plan("next", True) == "next" and media.plan("prev", False) == "prev"
    assert media.plan("up", True) == media.plan("mute", False) == "volume"
