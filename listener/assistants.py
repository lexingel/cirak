"""Hand a question or a task to Claude Code if it is installed. Only the words after the command
phrase are sent; the narration the apprentice heard before never leaves the PC."""
import os
import shutil
import subprocess
from urllib.parse import quote

from paths import DATA

MAX_WORDS = 60  # what fits a bubble; the whole answer goes to last_answer.txt
ANSWER = DATA / "last_answer.txt"
SYSTEM = {"en": "Answer in at most two short sentences.",
          "tr": "En fazla iki kısa cümleyle, Türkçe cevap ver."}


def ask_cmd(exe: str, text: str, lang: str) -> list:
    # no tools at all: nothing to approve, nothing runs; --restricted skips user settings and hooks
    return [exe, "-p", text, "--output-format", "text", "--tools", "", "--restricted",
            "--strict-mcp-config", "--no-session-persistence", "--max-turns", "1",
            "--append-system-prompt", SYSTEM.get(lang, SYSTEM["en"])]


def short(answer: str) -> str:
    words = answer.split()
    return answer.strip() if len(words) <= MAX_WORDS else " ".join(words[:MAX_WORDS]) + " …"


def ask_claude(text: str, lang: str = "en", run=subprocess.run, which=shutil.which):
    """Claude's answer for the bubble, or None if Claude Code is missing or failed."""
    exe = which("claude")
    if not exe:
        return None
    DATA.mkdir(parents=True, exist_ok=True)
    try:
        r = run(ask_cmd(exe, text, lang), capture_output=True, text=True, encoding="utf-8",
                timeout=120, cwd=str(DATA), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = (r.stdout or "").strip()
    if r.returncode != 0 or not out:
        return None
    ANSWER.write_text(out, encoding="utf-8")
    return short(out)


def task_link(text: str, cwd: str) -> str:
    """Opens Claude Code in a terminal with the task typed in but NOT sent: the user reads it, presses Enter."""
    return "claude-cli://open?cwd=" + quote(cwd, safe="") + "&q=" + quote(text[:5000], safe="")


def open_claude_task(text: str, cwd: str = "") -> bool:
    try:
        os.startfile(task_link(text, cwd or str(__import__("pathlib").Path.home())))
        return True
    except OSError:
        return False
