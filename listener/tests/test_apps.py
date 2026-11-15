import json

import apps

ALIASES = {"spotify": "Spotify", "müzik": "Spotify", "discord": "Discord", "vs code": "Visual Studio Code"}


def test_turkish_suffixes():
    assert apps.find("spotify'ı", ALIASES) == "Spotify"
    assert apps.find("discordu", ALIASES) == "Discord"
    assert apps.find("müzik", ALIASES) == "Spotify"
    assert apps.find("vs code", ALIASES) == "Visual Studio Code"


def test_not_on_the_list_is_never_found():
    assert apps.find("powershell", ALIASES) is None
    assert apps.find("format c", ALIASES) is None


def test_seed_only_lists_apps_that_exist(tmp_path):
    f = tmp_path / "apps.json"
    got = apps.load(f, idx={"spotify": "SpotifyAB!Spotify", "discord": "com.squirrel.Discord"})
    assert got == {"spotify": "Spotify", "discord": "Discord"}
    assert json.loads(f.read_text(encoding="utf-8")) == {"spotify": "Spotify", "discord": "Discord"}


def test_broken_file_means_no_apps(tmp_path):
    f = tmp_path / "apps.json"
    f.write_text("{oops", encoding="utf-8")
    assert apps.load(f, idx={}) == {}


def test_english_i_is_not_turned_into_dotless_i():
    assert apps.find("ıntellij", {"intellij": "IntelliJ IDEA"}) == "IntelliJ IDEA"


def test_close_spelling_is_found():
    assert apps.find("spotifay", ALIASES) == "Spotify"
    assert apps.find("xyz", ALIASES) is None


def test_no_app_index_writes_no_seed(tmp_path):
    f = tmp_path / "apps.json"
    assert apps.load(f, idx={}) == {}
    assert not f.exists()  # tried again next time instead of an empty list for good


def test_full_path_opens_as_is():
    opened = []
    apps.launch(r"C:\Tools\app.exe", idx={}, start=opened.append)
    assert opened == [r"C:\Tools\app.exe"]
