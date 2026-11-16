from screen import is_fullscreen

MON = (0, 0, 1920, 1080)


def test_game_covering_the_monitor_is_fullscreen():
    assert is_fullscreen((0, 0, 1920, 1080), MON, "UnityWndClass")


def test_maximized_window_leaves_the_taskbar_so_is_not():
    assert not is_fullscreen((-8, -8, 1928, 1040), MON, "Chrome_WidgetWin_1")


def test_borderless_overhang_still_counts():
    assert is_fullscreen((-1, -1, 1921, 1081), MON, "SDL_app")


def test_the_desktop_is_not_an_app():
    assert not is_fullscreen((0, 0, 1920, 1080), MON, "WorkerW")


def test_second_monitor():
    assert is_fullscreen((1920, 0, 4480, 1440), (1920, 0, 4480, 1440), "x")


def test_maximized_window_on_a_monitor_without_taskbar_is_not():
    assert not is_fullscreen((-8, -8, 1928, 1088), MON, "Chrome_WidgetWin_1", zoomed=True)
