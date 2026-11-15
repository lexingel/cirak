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
