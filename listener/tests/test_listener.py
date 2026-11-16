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
    # straight from listening to asking: no "back to stirring" flash before the bubble
    assert types(sent) == ["speech_start", "question"]


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


def test_pause_says_who_holds_the_mic():
    L, sent, state, _ = make()
    state["call"] = "Discord.exe"; L.tick()
    assert sent == [{"type": "paused", "who": "Discord.exe"}]


def test_app_picks_a_mic():
    L, *_ = make()
    assert L.device == ""
    L.on_client({"type": "mic_device", "name": "Mikrofon (USB 2.0 Camera)"})
    assert L.device == "Mikrofon (USB 2.0 Camera)"


def test_short_remark_just_nods():
    L, sent, *_ = make()
    L.speech_start(); L.speech_end("okay then")
    assert types(sent) == ["speech_start", "speech_end"]


def test_call_starting_mid_speech_still_ends_listening():
    L, sent, state, _ = make()
    L.speech_start()
    state["call"] = True; L.tick()
    L.speech_end(LONG)
    assert types(sent) == ["speech_start", "paused", "speech_end"]  # never stuck looking up


def make_cmd(speaker=False):
    L, sent, state, clock = make(speaker=speaker)
    done = []
    L.actions = {"media": lambda arg, lang, say: done.append(arg) or "ok " + arg}
    return L, sent, done


def test_wake_word_command_runs_and_is_not_narration():
    L, sent, done = make_cmd()
    L.speech_start(); L.speech_end("Çırak, sonraki şarkı")
    assert done == ["next"]
    assert types(sent) == ["speech_start", "say"] and sent[-1]["text"] == "ok next"
    assert L.gate.context() == ""  # never fed to the question gate


def test_push_to_talk_works_over_music_without_wake_word():
    L, sent, done = make_cmd(speaker=True)
    L.ptt_start(); L.ptt_end("duraklat")
    assert done == ["pause"] and types(sent) == ["speech_start", "say"]


def test_push_to_talk_respects_mic_off_and_calls():
    L, sent, done = make_cmd()
    L.mic_on = False
    L.ptt_start(); L.ptt_end("duraklat")
    assert done == [] and sent == []


def test_unknown_command_says_so_and_failing_action_does_not_crash():
    L, sent, done = make_cmd()
    L.on_client({"type": "typed", "text": "çırak mavi kediler"})
    assert sent[-1] == {"type": "say", "text": "Sorry, I didn't get that"}
    L.actions["media"] = lambda *a: 1 / 0
    L.on_client({"type": "typed", "text": "çırak sonraki"})
    assert sent[-1]["type"] == "say"


def test_empty_push_to_talk_just_ends_listening():
    L, sent, done = make_cmd()
    L.ptt_start(); L.ptt_end("  ")
    assert types(sent) == ["speech_start", "speech_end"]


def test_cancelled_push_to_talk_ends_listening():
    L, sent, done = make_cmd()
    L.ptt_start(); L.ptt_end(None)
    assert types(sent) == ["speech_start", "speech_end"] and done == []


def test_transcription_failure_never_leaves_listening_stuck():
    L, sent, done = make_cmd()
    L.transcribe = L.transcribe_cmd = lambda a, lang: 1 / 0
    L.speech_start(); L.speech_end("x")
    assert types(sent) == ["speech_start", "say", "speech_end"]  # told once why it can't hear
    sent.clear()
    L.ptt_start(); L.ptt_end("x")
    assert types(sent) == ["speech_start", "speech_end"]


def test_first_run_says_download_then_ready():
    L, sent, _, _ = make()
    L.lang = "tr"
    L.warm("silence", fresh=True)
    assert [m["text"] for m in sent] == ["İlk açılış: konuşma modeli iniyor (~460 MB), bu arada yazabilirsin", "Hazırım"]


def test_warm_with_model_present_is_silent_and_failure_is_told():
    L, sent, _, _ = make()
    L.warm("silence", fresh=False)
    assert sent == []
    L.transcribe = lambda a, lang: 1 / 0
    L.warm("silence", fresh=True)
    assert [m["text"] for m in sent][-1].startswith("I can't load the speech model")


def test_start_asks_a_fresh_opening_each_time():
    L, sent, _, _ = make()
    L.lang = "en"
    seen = []
    for _ in range(4):
        L.on_client({"type": "typed", "text": "Apprentice, let's start"})
        seen.append(sent[-1]["text"])
        assert sent[-1]["type"] == "question"
    assert len(set(seen)) == 4  # never one of the last three again
    L.on_client({"type": "typed", "text": "Çırak, başlıyorum"})
    assert sent[-1]["type"] == "question"


def test_where_was_i_quotes_the_last_two_things_said():
    L, sent, _, _ = make()
    L.lang = "en"
    L.on_client({"type": "typed", "text": "Apprentice, where was I?"})
    assert "haven't heard" in sent[-1]["text"]
    for s in ["I'm sorting the invoices by month", "now the March pile looks wrong", "ok"]:
        L.on_client({"type": "typed", "text": s})
    L.on_client({"type": "typed", "text": "Apprentice, where was I"})
    t = sent[-1]["text"]
    assert sent[-1]["type"] == "say" and "invoices by month" in t and "March pile" in t
    assert "“ok" not in t  # too short to count as narration


def test_recall_buffer_is_small_and_in_memory_only():
    L, _, _, _ = make()
    for i in range(30):
        L.on_client({"type": "typed", "text": f"step number {i} of the plan"})
    assert len(L.recent) == 10 and L.recent[-1] == "step number 29 of the plan"


def test_never_level_never_asks():
    L, sent, _, clock = make()
    L.on_client({"type": "frequency", "level": "off"})
    for _ in range(5):
        L.on_client({"type": "typed", "text": LONG})
        clock[0] += 10000
    assert "question" not in types(sent)


def test_done_sums_up_the_session_and_forgets_it():
    L, sent, _, _ = make()
    L.on_client({"type": "lang", "lang": "tr"})
    L.on_client({"type": "typed", "text": "Çırak, bitirdim"})
    assert sent[-1]["type"] == "say" and "görüşürüz" in sent[-1]["text"].lower()
    for i in range(30):
        L.on_client({"type": "typed", "text": f"step number {i} of the plan"})
    L.on_client({"type": "typed", "text": "Apprentice, done for today"})
    text = sent[-1]["text"]
    assert "step number 0 " in text and "step number 15 " in text and "step number 29 " in text
    assert len(L.session) == 0


def test_session_log_is_capped():
    L, _, _, _ = make()
    for i in range(500):
        L.on_client({"type": "typed", "text": f"step number {i} of the plan"})
    assert len(L.session) == 200


def test_a_reconnecting_app_hears_about_a_call_still_on():
    L, sent, state, _ = make()
    assert L.hello() == []
    state["call"] = "Discord.exe"; L.tick()
    assert L.hello() == [{"type": "paused", "who": "Discord.exe"}]
    state["call"] = False; L.tick()
    assert L.hello() == []


def test_typed_slash_runs_a_command_without_the_wake_word():
    L, sent, done = make_cmd()
    L.on_client({"type": "typed", "text": "/sonraki şarkı"})
    assert done == ["next"] and L.gate.context() == ""
    L.on_client({"type": "typed", "text": "sonraki şarkı"})  # no slash, no wake word: narration
    assert done == ["next"]
