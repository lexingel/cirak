import keys
from listener_core import Listener


def fake(pressed_over_time):
    """down(vk) reading a script of key sets; sleep() moves to the next set."""
    t = [0]
    down = lambda vk: vk in pressed_over_time[min(t[0], len(pressed_over_time) - 1)]
    sleep = lambda s: t.__setitem__(0, t[0] + 1)
    return down, sleep


def test_picks_the_next_key_after_the_menu_click_is_released():
    down, sleep = fake([{0x01}, {0x01}, set(), set(), {0x77}])  # mouse still down, then F8
    assert keys.wait_for_key(down, sleep) == 0x77


def test_escape_or_timeout_keeps_the_old_key():
    down, sleep = fake([set(), {0x1B}])
    assert keys.wait_for_key(down, sleep) is None
    down, sleep = fake([set()])
    assert keys.wait_for_key(down, sleep, timeout=0.1) is None


def test_generic_modifiers_are_never_picked_left_right_ones_are():
    down, sleep = fake([set(), {0x11, 0xA3}])
    assert keys.wait_for_key(down, sleep) == 0xA3


def test_chord_ignores_the_key_itself_and_generic_modifiers():
    assert not keys.other_key_down(0xA3, lambda vk: vk in (0xA3, 0x11))
    assert keys.other_key_down(0xA3, lambda vk: vk in (0xA3, 0x11, 0x43))  # Right Ctrl+C
    assert not keys.other_key_down(0x77, lambda vk: vk == 0x77)


def test_listener_takes_the_saved_key():
    L = Listener(send=print, transcribe=None, ask=None, call_busy=None, speaker_busy=None)
    assert L.ptt_vk == 0xA3
    L.on_client({"type": "ptt_key", "vk": 0x77})
    assert L.ptt_vk == 0x77
    L.on_client({"type": "ptt_key", "vk": "junk"})
    L.on_client({"type": "ptt_key", "vk": 0x1B})
    assert L.ptt_vk == 0x77
