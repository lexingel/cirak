import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from hearing import Detector, BLOCK, RATE

B = np.zeros(BLOCK, "float32")


def run(pattern):
    ev = []
    d = Detector(on_start=lambda: ev.append("start"), on_end=lambda a: ev.append(("end", len(a))))
    for loud in pattern:
        d.feed(B, loud)
    return ev


def test_single_click_is_not_speech():
    assert run([True] + [False] * 100) == []


def test_sustained_sound_is_speech():
    ev = run([True] * 20 + [False] * 60)
    assert ev[0] == "start" and ev[1][0] == "end"


def test_endless_noise_is_cut():
    blocks = int(31 * RATE / BLOCK)
    ev = run([True] * blocks)
    assert ev[:2][0] == "start" and ev[1][0] == "end"


def test_steady_noise_stops_counting_as_speech():
    from hearing import Loudness
    loud = Loudness(threshold=0.015)
    assert loud(0.1)  # speech in a quiet room
    results = [loud(0.03) for _ in range(3000)]  # a fan for ~90 s
    assert results[0] and not results[-1]
    assert loud(0.2)  # talking over the fan still counts


def test_quiet_room_keeps_plain_threshold():
    from hearing import Loudness
    loud = Loudness(threshold=0.015)
    for _ in range(500):
        loud(0.002)
    assert loud(0.02) and not loud(0.01)


def test_no_mic_does_not_crash():
    import main
    def broken():
        raise OSError("no input device")
    assert main.open_hearing(broken) is None


DEVICES = [
    {"name": "Microsoft Sound Mapper - Input", "hostapi": 0, "max_input_channels": 2},
    {"name": "FaceRig Virtual Microphone (Fac", "hostapi": 0, "max_input_channels": 2},
    {"name": "Mikrofon (USB 2.0 Camera)", "hostapi": 0, "max_input_channels": 1},
    {"name": "Speakers (Realtek)", "hostapi": 0, "max_input_channels": 0},
    {"name": "Mikrofon (USB 2.0 Camera)", "hostapi": 2, "max_input_channels": 1},
]


def test_mic_list_is_real_inputs_once():
    from hearing import input_mics
    assert input_mics(DEVICES) == ["FaceRig Virtual Microphone (Fac", "Mikrofon (USB 2.0 Camera)"]


def test_mic_by_name_falls_back_to_default():
    from hearing import device_index
    assert device_index(DEVICES, "Mikrofon (USB 2.0 Camera)") == 2
    assert device_index(DEVICES, "unplugged mic") is None
    assert device_index(DEVICES, "") is None


def test_gpu_failure_mid_transcribe_falls_back_to_cpu(monkeypatch):
    import hearing
    from types import SimpleNamespace as S

    class Gpu:
        def transcribe(self, *a, **k):
            raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")

    class Cpu:
        def transcribe(self, *a, **k):
            return iter([S(text=" what comes next", no_speech_prob=0.1, avg_logprob=-0.3)]), None

    monkeypatch.setattr(hearing, "_model", None)
    monkeypatch.setattr(hearing, "_load", lambda device: Gpu() if device == "cuda" else Cpu())
    assert hearing.transcribe(np.zeros(16000, "float32")) == "what comes next"
    assert hearing.transcribe(np.zeros(16000, "float32")) == "what comes next"  # stays on CPU


def test_bye_closes_the_mic_before_exiting():
    import main
    calls = []

    class Mic:
        def close(self):
            calls.append("close")

    main.quit_cleanly(Mic(), exit=lambda code: calls.append(("exit", code)))
    assert calls == ["close", ("exit", 0)]
    calls.clear()
    main.quit_cleanly(None, exit=lambda code: calls.append(("exit", code)))  # no mic: still exits
    assert calls == [("exit", 0)]


def test_whisper_segments_it_doubts_are_dropped():
    from types import SimpleNamespace as S
    from hearing import keep
    segs = [S(text=" fixing the menu", no_speech_prob=0.1, avg_logprob=-0.3),
            S(text=" thanks for watching", no_speech_prob=0.8, avg_logprob=-0.3),
            S(text=" mumble", no_speech_prob=0.1, avg_logprob=-1.5)]
    assert keep(segs) == "fixing the menu"


def _ptt(chord=False):
    import numpy as np
    from hearing import PushToTalk
    held, other, got, started = [True], [chord], [], []
    p = PushToTalk(lambda: held[0], lambda: started.append(1), got.append, lambda: other[0])
    return p, held, other, got, started, np.zeros(480, "float32")


def test_push_to_talk_keeps_every_block_until_release():
    from hearing import PTT_MIN
    p, held, _, got, started, quiet = _ptt()
    for _ in range(PTT_MIN):
        assert p.feed(quiet)  # quiet blocks count too: the key decides
    assert started == [1]
    held[0] = False
    assert p.feed(quiet) and len(got) == 1 and len(got[0]) == PTT_MIN * 480
    assert not p.feed(quiet)  # back to normal listening


def test_push_to_talk_tap_is_ignored():
    p, held, _, got, started, quiet = _ptt()
    p.feed(quiet); p.feed(quiet)  # Ctrl tapped, as in a shortcut
    held[0] = False
    p.feed(quiet)
    assert got == [] and started == []


def test_push_to_talk_shortcut_cancels():
    from hearing import PTT_MIN
    p, held, other, got, started, quiet = _ptt()
    for _ in range(PTT_MIN + 2):
        p.feed(quiet)
    other[0] = True  # Ctrl+C after a pause: not a command
    assert p.feed(quiet) and got == [None]
    other[0] = False
    assert p.feed(quiet) and got == [None]  # still held: nothing new starts
    held[0] = False
    assert not p.feed(quiet) and started == [1]


def test_push_to_talk_cut_at_max_does_not_restart():
    from hearing import PTT_MAX, BLOCK, RATE
    p, held, _, got, started, quiet = _ptt()
    for _ in range(int(PTT_MAX * RATE / BLOCK) + 50):
        p.feed(quiet)
    assert len(got) == 1 and started == [1]
    held[0] = False
    p.feed(quiet)
    assert len(got) == 1
