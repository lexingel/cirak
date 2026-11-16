"""Is a fullscreen app (a game, a video) in front? Then the apprentice steps aside."""
import ctypes
from ctypes import wintypes

SHELL = {"Progman", "WorkerW", "Shell_TrayWnd"}  # the desktop itself is "fullscreen" but isn't an app


def is_fullscreen(win: tuple, mon: tuple, cls: str, zoomed: bool = False) -> bool:
    """win/mon = (left, top, right, bottom). A window covering its whole monitor, taskbar included,
    that isn't the desktop. Maximized (zoomed) never counts: on a monitor without a taskbar a
    maximized browser covers it all too."""
    if zoomed or cls in SHELL:
        return False
    return win[0] <= mon[0] and win[1] <= mon[1] and win[2] >= mon[2] and win[3] >= mon[3]


class _MonInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


_u32 = ctypes.windll.user32
try:  # real pixels, like the Godot app; without this the rects are scaled on a 150% screen
    _u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # this process only, not a system setting
except Exception:
    pass


def fullscreen_rect():
    """The monitor rect a fullscreen window covers right now, or None."""
    hwnd = _u32.GetForegroundWindow()
    if not hwnd:
        return None
    r = wintypes.RECT()
    if not _u32.GetWindowRect(hwnd, ctypes.byref(r)):
        return None
    mi = _MonInfo(cbSize=ctypes.sizeof(_MonInfo))
    if not _u32.GetMonitorInfoW(_u32.MonitorFromWindow(hwnd, 2), ctypes.byref(mi)):
        return None
    buf = ctypes.create_unicode_buffer(64)
    _u32.GetClassNameW(hwnd, buf, 64)
    m = mi.rcMonitor
    mon = (m.left, m.top, m.right, m.bottom)
    return list(mon) if is_fullscreen((r.left, r.top, r.right, r.bottom), mon, buf.value, bool(_u32.IsZoomed(hwnd))) else None
