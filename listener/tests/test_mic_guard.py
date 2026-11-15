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


def test_venv_launcher_base_interpreter_not_counted():
    # .venv pythonw.exe is a launcher; the base interpreter is what holds the mic
    selfs = [r"D:\proj\.venv\Scripts\python.exe",
             r"C:\Users\x\AppData\Local\Programs\Python\Python310\python.exe"]
    key = "C:#Users#x#AppData#Local#Programs#Python#Python310#pythonw.exe"
    assert not mic_in_use_by_other({key: (5, 0)}, selfs)


def test_mic_user_names_the_app():
    from mic_guard import mic_user
    assert mic_user({"C:#Users#x#Discord.exe": (5, 0)}, SELF) == "Discord.exe"
    assert mic_user({"C:#Users#x#Discord.exe": (5, 9)}, SELF) is None


def test_mic_permission_off_anywhere_means_blocked():
    import mic_guard as g
    allow = lambda hive, path: "Allow"
    assert g.mic_allowed(allow) is True
    assert g.mic_allowed(lambda hive, path: None) is True  # never set: Windows' default is on
    desktop_off = lambda hive, path: "Deny" if path.endswith("NonPackaged") else "Allow"
    assert g.mic_allowed(desktop_off) is False  # "let desktop apps access your microphone" off
    device_off = lambda hive, path: "Deny" if hive == "HKLM" else "Allow"
    assert g.mic_allowed(device_off) is False
