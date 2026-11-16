"""The push-to-talk key: is it down, is another key down with it, and picking a new one."""
import ctypes
import time

ESC = 0x1B
GENERIC = (0x10, 0x11, 0x12)  # Shift/Ctrl/Alt "either side": always down with their left/right key
MOUSE = range(0x01, 0x07)
PICKABLE = [vk for vk in range(0x08, 0xFF) if vk not in GENERIC]
EXTENDED = {*range(0x21, 0x29), 0x2D, 0x2E, 0x5B, 0x5C, 0x5D, 0x6F, 0x90, 0xA3, 0xA5}  # for the key name


def key_down(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def other_key_down(ptt: int, down=key_down) -> bool:
    """Any key or mouse button besides the push-to-talk key: Right Ctrl+C is a shortcut, not a command."""
    return any(down(vk) for vk in range(1, 0xFF) if vk != ptt and vk not in GENERIC)


def wait_for_key(down=key_down, sleep=time.sleep, timeout: float = 10.0, step: float = 0.02):
    """The next key pressed once every key and button is up (the menu click): its code, or None
    for Esc or no key in time."""
    t = 0.0
    while t < timeout and any(down(vk) for vk in [*MOUSE, *PICKABLE]):
        sleep(step)
        t += step
    while t < timeout:
        for vk in PICKABLE:
            if down(vk):
                return None if vk == ESC else vk
        sleep(step)
        t += step
    return None


def key_name(vk: int) -> str:
    """Windows' own name for the key, in the Windows language ("Right Ctrl", "F8")."""
    u = ctypes.windll.user32
    lparam = (u.MapVirtualKeyW(vk, 0) << 16) | ((1 << 24) if vk in EXTENDED else 0)
    buf = ctypes.create_unicode_buffer(64)
    return buf.value if u.GetKeyNameTextW(lparam, buf, 64) else {0x13: "Pause"}.get(vk, f"0x{vk:02X}")
