import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from mic_guard import mic_in_use_by_other

SELF = r"C:\Python310\python.exe"


def test_discord_in_call():
    assert mic_in_use_by_other({"C:#Users#x#Discord.exe": (5, 0)}, SELF)


def test_finished_call():
    assert not mic_in_use_by_other({"C:#Users#x#Discord.exe": (5, 9)}, SELF)


def test_self_not_counted():
    assert not mic_in_use_by_other({"C:#Python310#python.exe": (5, 0)}, SELF)


def test_self_match_ignores_case():
    assert not mic_in_use_by_other({"c:#python310#PYTHON.EXE": (5, 0)}, SELF)
