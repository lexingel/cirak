"""Is someone else using the mic (a call)? Is the speaker playing (video, music)?"""
import winreg

_STORE = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone"


def _own_keys(self_exes) -> set[str]:
    if isinstance(self_exes, str):
        self_exes = [self_exes]
    keys = set()
    for exe in self_exes:
        k = exe.replace("\\", "#").lower()
        keys |= {k, k.replace("#python.exe", "#pythonw.exe"), k.replace("#pythonw.exe", "#python.exe")}
    return keys


def own_exes() -> list[str]:
    """This process and, for a venv, the base interpreter that actually opens the mic."""
    import sys
    return [sys.executable, getattr(sys, "_base_executable", sys.executable)]


def mic_user(entries: dict[str, tuple[int, int]], self_exes):
    """Name of another app holding the mic right now (e.g. "Discord.exe"), or None."""
    mine = _own_keys(self_exes)
    for key, (start, stop) in entries.items():
        if start > 0 and stop == 0 and key.lower() not in mine:
            return key.split("#")[-1]
    return None


def mic_in_use_by_other(entries: dict[str, tuple[int, int]], self_exes) -> bool:
    return mic_user(entries, self_exes) is not None


def _read_children(key) -> dict[str, tuple[int, int]]:
    out = {}
    i = 0
    while True:
        try:
            name = winreg.EnumKey(key, i)
        except OSError:
            return out
        i += 1
        try:
            with winreg.OpenKey(key, name) as k:
                start = winreg.QueryValueEx(k, "LastUsedTimeStart")[0]
                stop = winreg.QueryValueEx(k, "LastUsedTimeStop")[0]
                out[name] = (start, stop)
        except OSError:
            pass  # e.g. the NonPackaged folder itself has no times


def read_mic_entries() -> dict[str, tuple[int, int]]:
    out = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STORE) as root:
            out.update(_read_children(root))
            with winreg.OpenKey(root, "NonPackaged") as np_:
                out.update(_read_children(np_))
    except OSError:
        pass
    return out


_meter = None


def speaker_busy(threshold: float = 0.02) -> bool:
    global _meter
    try:
        if _meter is None:
            from ctypes import POINTER, cast
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
            dev = AudioUtilities.GetSpeakers()
            dev = getattr(dev, "_dev", dev)  # newer pycaw wraps the IMMDevice
            _meter = cast(dev.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None),
                          POINTER(IAudioMeterInformation))
        return _meter.GetPeakValue() > threshold
    except Exception:
        return False
