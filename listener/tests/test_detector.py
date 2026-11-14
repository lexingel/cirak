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
