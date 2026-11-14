"""Is someone else using the mic (a call)? Is the speaker playing (video, music)?"""
import winreg

_STORE = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone"


def mic_in_use_by_other(entries: dict[str, tuple[int, int]], self_exe: str) -> bool:
    me = self_exe.replace("\\", "#").lower()
    return any(start > 0 and stop == 0 and key.lower() != me for key, (start, stop) in entries.items())


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
