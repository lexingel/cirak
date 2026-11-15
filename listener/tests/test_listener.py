import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from listener_core import Listener

LONG = "şimdi menüdeki butonları tek tek hizalıyorum ve renklerini deniyorum"


def make(call=False, speaker=False):
    sent, clock = [], [1000.0]
    state = {"call": call, "speaker": speaker}
    L = Listener(send=sent.append, transcribe=lambda a, lang: a, ask=lambda ctx, lang: "Ne var?",
                 call_busy=lambda: state["call"], speaker_busy=lambda: state["speaker"],
                 clock=lambda: clock[0])
    return L, sent, state, clock


def types(sent):
    return [m["type"] for m in sent]


def test_narration_leads_to_question():
    L, sent, *_ = make()
    L.speech_start(); L.speech_end(LONG)
    assert types(sent) == ["speech_start", "speech_end", "question"]


def test_call_pauses_and_drops_speech():
    L, sent, state, _ = make()
    state["call"] = True; L.tick()
    L.speech_start(); L.speech_end(LONG)
    assert types(sent) == ["paused"]
    state["call"] = False; L.tick()
    assert types(sent) == ["paused", "resumed"]


def test_speaker_audio_not_counted():
    L, sent, *_ = make(speaker=True)
    L.speech_start(); L.speech_end(LONG)
    assert "question" not in types(sent)


def test_typed_text_can_ask_and_blank_ignored():
    L, sent, *_ = make()
    L.on_client({"type": "typed", "text": "   "})
    assert sent == []
    L.on_client({"type": "typed", "text": LONG})
    assert types(sent) == ["question"]


def test_mic_off_ignores_speech():
    L, sent, *_ = make()
    L.on_client({"type": "mic", "on": False})
    L.speech_start(); L.speech_end(LONG)
    assert sent == []


def test_frequency_message_sets_interval():
    L, *_ = make()
    L.on_client({"type": "frequency", "level": "low"})
    assert L.gate.min_interval == 600


def test_speaker_busy_does_not_even_look_up():
    L, sent, *_ = make(speaker=True)
    L.speech_start(); L.speech_end(LONG)
    assert sent == []


def test_language_message_reaches_transcribe_and_ask():
    seen = {}
    sent = []
    L = Listener(send=sent.append,
                 transcribe=lambda a, lang: seen.setdefault("t", lang) and a,
                 ask=lambda ctx, lang: seen.setdefault("a", lang) and "Q?",
                 call_busy=lambda: False, speaker_busy=lambda: False, clock=lambda: 1000.0)
    assert L.lang == "en"
    L.on_client({"type": "lang", "lang": "tr"})
    L.speech_start(); L.speech_end(LONG)
    assert seen == {"t": "tr", "a": "tr"}
    L.on_client({"type": "lang", "lang": "klingon"})
    assert L.lang == "tr"
