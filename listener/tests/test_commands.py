import commands as c


def test_narration_without_wake_word_is_not_a_command():
    assert c.parse("I'm fixing the menu buttons and trying new colors") is None
    assert c.parse("bugün çırak gibi çalışıyorum, durdur bakalım") is None


def test_push_to_talk_needs_no_wake_word():
    assert c.parse("next song", ptt=True) == ("media", "next")
    assert c.parse("şarkıyı geç", ptt=True) == ("media", "next")


def test_wake_word_variants_and_punctuation():
    for t in ("Çırak, duraklat.", "Cirak duraklat", "çırağım duraklat", "Hey çırak, duraklat!", "Apprentice, pause."):
        assert c.parse(t) == ("media", "pause"), t


def test_media_intents():
    cases = {
        "çırak sonraki şarkı": "next", "çırak bir önceki şarkıya geç": "prev", "çırak devam et": "play",
        "çırak müziği durdur": "pause", "çırak sesi aç": "up", "çırak sesi kıs": "down",
        "çırak sessize al": "mute", "apprentice skip": "next", "apprentice previous track": "prev",
        "apprentice resume": "play", "apprentice volume up": "up", "apprentice turn it down": "down",
        "apprentice mute": "mute",
    }
    for text, want in cases.items():
        assert c.parse(text) == ("media", want), text


def test_open_app():
    assert c.parse("Çırak, Spotify'ı aç") == ("open", "spotify'ı")
    assert c.parse("çırak discordu başlat") == ("open", "discordu")
    assert c.parse("apprentice open visual studio code") == ("open", "visual studio code")
    assert c.parse("sesi aç", ptt=True) == ("media", "up")  # volume, not an app called "ses"


def test_claude_only_the_part_after_the_command_leaves():
    assert c.parse("Çırak, Claude'a sor: hava nasıl?") == ("ask_claude", "hava nasıl?")
    assert c.parse("çırak klod a sor python'da liste nasıl sıralanır") == ("ask_claude", "python'da liste nasıl sıralanır")
    assert c.parse("apprentice ask claude what is a monad") == ("ask_claude", "what is a monad")
    assert c.parse("çırak claude'a iş ver: README dosyasını düzelt") == ("claude_task", "readme dosyasını düzelt")
    assert c.parse("apprentice tell claude to fix the tests") == ("claude_task", "fix the tests")


def test_wake_word_alone_or_gibberish_is_unknown():
    assert c.parse("Çırak!") == ("unknown", "")
    assert c.parse("çırak mavi kediler uçar") == ("unknown", "mavi kediler uçar")
    assert c.parse("hmm", ptt=True) == ("unknown", "hmm")


def test_reply_text_follows_language():
    assert c.reply("tr", "next") == "Sonraki şarkı"
    assert c.reply("en", "next") == "Next song"
    assert c.reply("xx", "next") == "Next song"


def test_whisper_spellings_heard_in_tests():
    assert c.parse("Claude Asor, Hüttponda liste nasıl sıralanır?", ptt=True)[0] == "ask_claude"
    assert c.parse("Cilau de Aşor, liste nasıl sıralanır", ptt=True)[0] == "unknown"  # too mangled; fine
    assert c.parse("Çırak, sesi kız.") == ("media", "down")


def test_wake_word_is_a_word_not_a_prefix():
    assert c.parse("çıraklık dönemimde böyle yapardık") is None
    assert c.parse("Chirac, duraklat") == ("media", "pause")  # Whisper's usual spelling


def test_unmute():
    for t in ("sesi geri aç", "sessizden çık", "unmute"):
        assert c.parse(t, ptt=True) == ("media", "unmute"), t


def test_hide_and_show():
    for t in ["Çırak, saklan", "çırak gizlen", "Apprentice, hide"]:
        assert c.parse(t) == ("hide", ""), t
    for t in ["Çırak, geri gel", "Apprentice, come back", "çırak ortaya çık"]:
        assert c.parse(t) == ("show", ""), t
    assert c.parse("apprentice go back") == ("media", "prev")  # "come back" only, not "back"
