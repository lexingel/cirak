"""Opening apps by voice, only the ones the user listed in apps.json (spoken name -> app name).

App names are looked up in Windows' own app list (shell:AppsFolder), which holds Store apps
(Spotify has no Start Menu shortcut) and desktop apps alike. Nothing said ever runs as a command:
only a target written in apps.json can be launched.
"""
import difflib
import json
import os
import re
import subprocess

from paths import DATA

FILE = DATA / "apps.json"
SEED = {"spotify": "Spotify", "discord": "Discord", "chrome": "Google Chrome", "firefox": "Firefox",
        "vs code": "Visual Studio Code", "steam": "Steam", "notepad": "Notepad", "not defteri": "Not Defteri"}
PS = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; (New-Object -ComObject Shell.Application)"
      ".NameSpace('shell:AppsFolder').Items() | % { $_.Name + '|' + $_.Path }")
_index = None


def index() -> dict:
    """{app name lower: AppsFolder id}, read once (a newly installed app shows after a restart)."""
    global _index
    if _index is None:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS], capture_output=True,
                             text=True, encoding="utf-8", timeout=20,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        _index = {n.strip().lower(): p.strip() for n, _, p in (l.partition("|") for l in out.splitlines()) if p}
    return _index


def load(path=FILE, idx=None) -> dict:
    """The user's list; written with the apps from SEED that exist here if there is none yet."""
    if not path.exists():
        idx = index() if idx is None else idx
        if not idx:  # PowerShell blocked or slow: no seed now, try again next time
            return {}
        path.parent.mkdir(parents=True, exist_ok=True)
        seed = {k: v for k, v in SEED.items() if v.lower() in idx}
        path.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return {str(k).lower().strip(): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def find(spoken: str, aliases: dict):
    """The apps.json target for what was said ("Spotify'ı", "discordu"), or None."""
    s = spoken.lower().strip()
    tries = [s, re.sub(r"'\w*$", "", s), re.sub(r"(y|n)?[ıiuüae]$", "", s)]
    tries += [t.replace("ı", "i") for t in tries]  # Turkish I->ı made "IntelliJ" "ıntellij"
    for t in tries:
        if t in aliases:
            return aliases[t]
    hits = {v for k, v in aliases.items() if s.startswith(k)}
    if len(hits) == 1:
        return hits.pop()
    close = difflib.get_close_matches(tries[1], list(aliases), n=1, cutoff=0.75)  # "spotifay"
    return aliases[close[0]] if close else None


def launch(target: str, idx=None, start=os.startfile) -> None:
    if re.match(r"^[a-z]:\\|^\\\\", target, re.I):  # a full path the user wrote into apps.json
        start(target)
        return
    idx = index() if idx is None else idx
    start("shell:AppsFolder\\" + idx.get(target.lower(), target))


def edit(path=FILE) -> None:
    load(path)
    subprocess.Popen(["notepad.exe", str(path)])
