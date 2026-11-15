"""Spoken commands: "Çırak, sonraki şarkı" / "Apprentice, open Spotify". Pure text matching, no model.

A command needs the wake word at the very start, or push-to-talk held (then everything said is a
command). Only the text AFTER a "Claude'a sor" phrase is ever sent anywhere; narration never is.
"""
import re

# "çırak", "çırağım", "Chirac" (Whisper); not "çıraklık", which is narration
WAKE = re.compile(r"^(hey\s+)?(ç|c|ch)[ıi]ra(k|ğ|g|c)([ıi]m|[ıi]n)?\b|^(hey\s+)?apprentice\b")
CLAUDE = r"(claude|klod|clod|klot|cloud|claud|cilau\s*de|klavd)\s*'?\s*(a|ya|e|ye)?"

# order matters: Claude first (its text can contain anything), volume before "open" ("sesi aç")
RULES = [
    ("ask_claude", re.compile(rf"^{CLAUDE}\s*sor\s*:?\s*(?P<arg>.+)$")),
    ("ask_claude", re.compile(rf"^ask\s+{CLAUDE}\s*:?\s*(?P<arg>.+)$")),
    ("claude_task", re.compile(rf"^{CLAUDE}\s+(iş\s+ver|yaptır|söyle)\s*:?\s*(?P<arg>.+)$")),
    ("claude_task", re.compile(rf"^tell\s+{CLAUDE}\s+(to\s+)?(?P<arg>.+)$")),
    ("unmute", re.compile(r"\bsesi\s+geri\s+aç|\bsessizden\s+çık|\bunmute\b")),
    ("up", re.compile(r"\bsesi\s+(aç|yükselt|art[ıt]?ır)|\bvolume\s+up\b|\blouder\b|\bturn\s+it\s+up\b")),
    ("down", re.compile(r"\bsesi\s+(kıs|kız|azalt|düşür)|\bvolume\s+down\b|\bquieter\b|\bturn\s+it\s+down\b")),
    ("mute", re.compile(r"\bsessize\s+al\b|\bsesi\s+kapat\b|\bmute\b")),
    ("open", re.compile(r"^(open|launch|start)\s+(?P<arg>.+)$")),
    ("open", re.compile(r"^(aç|başlat)\s+(?P<arg>.+)$")),
    ("open", re.compile(r"^(?P<arg>.+?)\s+(aç|başlat)$")),
    ("prev", re.compile(r"\b(önceki|previous|go\s+back|back)\b")),
    ("next", re.compile(r"\b(sonraki|geç|atla|değiştir|next|skip)\b")),
    ("pause", re.compile(r"\b(duraklat|durdur|dur|sus|pause|stop)\b")),
    ("play", re.compile(r"\b(devam|oynat|çal|play|resume)\b")),
]
MEDIA = {"unmute", "up", "down", "mute", "prev", "next", "pause", "play"}

REPLIES = {
    "en": {"next": "Next song", "prev": "Previous song", "pause": "Paused", "play": "Playing",
           "up": "Louder", "down": "Quieter", "mute": "Muted", "unknown": "Sorry, I didn't get that",
           "opening": "Opening {}", "no_app": "{} isn't on my app list", "asking": "Asking Claude: {}",
           "no_claude": "I can't reach Claude", "task": "Claude is open, press Enter to send",
           "ptt_set": "Command key: {}", "ptt_same": "Command key not changed", "unmute": "Sound on",
           "cant_open": "I couldn't open {}", "ready": "Ready", "pulling": "Downloading the question model: {}%",
           "pulled": "Question model ready, my questions just got better", "pull_failed": "I couldn't download the question model",
           "downloading": "First start: downloading the speech model (~460 MB), you can type meanwhile",
           "no_model": "I can't load the speech model; you can still type (details in listener.log)"},
    "tr": {"next": "Sonraki şarkı", "prev": "Önceki şarkı", "pause": "Duraklattım", "play": "Çalıyor",
           "up": "Sesi açtım", "down": "Sesi kıstım", "mute": "Sessize aldım", "unknown": "Anlamadım",
           "opening": "{} açılıyor", "no_app": "{} uygulama listemde yok", "asking": "Claude'a soruyorum: {}",
           "no_claude": "Claude'a ulaşamadım", "task": "Claude açıldı, göndermek için Enter'a bas",
           "ptt_set": "Komut tuşu: {}", "ptt_same": "Komut tuşu değişmedi", "unmute": "Sesi geri açtım",
           "cant_open": "{} açılamadı", "ready": "Hazırım", "pulling": "Soru modeli iniyor: %{}",
           "pulled": "Soru modeli hazır, sorularım artık daha iyi", "pull_failed": "Soru modelini indiremedim",
           "downloading": "İlk açılış: konuşma modeli iniyor (~460 MB), bu arada yazabilirsin",
           "no_model": "Konuşma modeli yüklenemedi; yazarak devam edebilirsin (ayrıntı listener.log'da)"},
}


def norm(text: str) -> str:
    t = text.replace("I", "ı").replace("İ", "i").lower()
    t = re.sub(r"[.,!?;:\"“”]+(?=\s|$)", "", t)  # trailing punctuation, keeps "claude'a" and "sor:"... mostly
    return re.sub(r"\s+", " ", t).strip()


def parse(text: str, ptt: bool = False):
    """(intent, arg) for a command, None for ordinary narration. intent "media" carries the action."""
    raw = text.strip()
    t = norm(raw)
    m = WAKE.match(t)
    if m:
        t = t[m.end():].lstrip(" ,")
    elif not ptt:
        return None
    if not t:
        return ("unknown", "")
    for intent, rx in RULES:
        hit = rx.search(t)
        if hit:
            if intent in MEDIA:
                return ("media", intent)
            arg = hit.group("arg").strip()
            if intent == "ask_claude":  # keep the user's own punctuation in what is sent
                arg = _tail(raw, arg)
            return (intent, arg)
    return ("unknown", t)


def _tail(raw: str, arg: str) -> str:
    """The original-case, original-punctuation end of `raw` matching the normalised `arg`."""
    words = len(arg.split())
    tail = " ".join(raw.split()[-words:])
    return tail if norm(tail) == arg else arg


def reply(lang: str, key: str, *args) -> str:
    return REPLIES.get(lang, REPLIES["en"])[key].format(*args)
