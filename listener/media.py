"""Media control through the keys on a media keyboard: Windows sends them to whatever is playing
(Spotify, YouTube in a browser, ...), so we never need to know which app it is."""
import ctypes

KEYS = {"next": 0xB0, "prev": 0xB1, "toggle": 0xB3}
KEYUP = 0x2
STEP = 0.1


def press(vk: int) -> None:
    u = ctypes.windll.user32
    u.keybd_event(vk, 0, 0, 0)
    u.keybd_event(vk, 0, KEYUP, 0)


def plan(action: str, playing: bool) -> str:
    """What to do: a key name or "volume". Pause/play always press the one toggle key: the user
    asked for it, and the speaker meter can be wrong (quiet passage, a game making sound)."""
    if action in ("next", "prev"):
        return action
    if action in ("pause", "play"):
        return "toggle"
    return "volume"


def _endpoint():
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    dev = AudioUtilities.GetSpeakers()
    dev = getattr(dev, "_dev", dev)
    return cast(dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))


def volume(action: str) -> None:
    ep = _endpoint()
    if action in ("mute", "unmute"):
        ep.SetMute(int(action == "mute"), None)
        return
    level = ep.GetMasterVolumeLevelScalar() + (STEP if action == "up" else -STEP)
    ep.SetMute(0, None)
    ep.SetMasterVolumeLevelScalar(min(1.0, max(0.0, level)), None)


def run(action: str, playing: bool) -> str:
    """Does it; returns the reply key for the apprentice's bubble."""
    p = plan(action, playing)
    if p == "volume":
        volume(action)
        return action
    press(KEYS[p])
    if p == "toggle":  # the meter only picks the words: sound before the press means it paused
        return "pause" if playing else "play"
    return action
