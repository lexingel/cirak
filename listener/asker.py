"""Turns recent narration into one short, curious question.

Order: local model (Ollama, free, nothing leaves the PC) -> Claude Haiku (only if ANTHROPIC_API_KEY
is set) -> a local list of gentle questions.
"""
import json
import os
import random
import re
import urllib.request

LOCAL_URL = "http://127.0.0.1:11434/api/chat"
LOCAL_MODEL = os.environ.get("CIRAK_MODEL", "qwen2.5:3b")
HAIKU = "claude-haiku-5-5"
MAX_WORDS = 15
KEEP_ALIVE = "2h"  # ponytail: holds ~2 GB VRAM while idle; after 2h silence the first question uses the list

SYSTEM = {
    "en": ("You are a tiny wizard apprentice keeping the user company while they work. The potion you stir "
           "is YOUR task, not theirs: never ask about potions, ingredients or magic. Read what the user just "
           "said and reply with ONE short, curious question (15 words max) about something they actually "
           "said. Never invent details. If they only greet you or chat, greet back briefly and ask what "
           "they are working on. No advice, no judging, no pushing. Reply with the question only.\n"
           "Examples:\n"
           "User: Hello apprentice, how are you? -> Hello! I'm stirring away. What are you working on?\n"
           "User: I'm fixing the menu buttons and trying new colors. -> Which color is winning so far?\n"
           "User: This function keeps returning null. -> Where does the null first show up?"),
    "tr": ("Sen kullanıcıya çalışırken eşlik eden küçük bir büyücü çıraksın. Karıştırdığın iksir SENİN işin, "
           "onun değil: asla iksir, malzeme ya da büyü sorma. Kullanıcının az önce söylediğini oku ve "
           "gerçekten söylediği bir şey hakkında tek bir kısa, meraklı soru sor (en fazla 15 kelime). "
           "Asla ayrıntı uydurma. Sadece selam verirse ya da sohbet ederse kısaca selam ver ve ne üzerinde "
           "çalıştığını sor. Tavsiye verme, yargılama, hesap sorma. Sadece soruyu yaz, \"sen\" diye hitap et.\n"
           "Örnekler:\n"
           "Kullanıcı: Merhaba çırak, nasılsın? -> Merhaba! Ben kazanı karıştırıyorum. Sen ne üzerinde çalışıyorsun?"),
    # ponytail: no work examples in TR, the 3b model copies them verbatim; a 7b model could take them
}

FALLBACK = {
    "en": [
        "What comes after this part?",
        "Where are you stuck right now?",
        "What are you looking at the most?",
        "Which part is the most fun?",
        "What could the next tiny step be?",
        "How will this look when it's done?",
        "What question is on your mind?",
        "How would you explain this in one sentence?",
        "Which part is the easiest?",
        "Who are you making this for?",
        "What do you have in front of you?",
        "What would you like to move on to next?",
        "What's making you think the most here?",
        "Who will you show it to first?",
        "Which part went better than expected?",
        "What are you trying right now?",
        "What are you curious about in this step?",
        "My cauldron is bubbling. How's yours going?",
    ],
    "tr": [
        "Bu bitince sırada ne var?",
        "Takıldığın yer neresi?",
        "Şu an en çok neye bakıyorsun?",
        "Bunun en keyifli kısmı hangisi?",
        "Bir sonraki küçük adım ne olabilir?",
        "Bu parça bitince nasıl görünecek?",
        "Şu an aklındaki soru ne?",
        "Bunu bana bir cümleyle anlatsan nasıl anlatırdın?",
        "Hangi kısmı yapmak en kolayı?",
        "Bunu kimin için yapıyorsun?",
        "Şu an elinin altında ne var?",
        "Bundan sonra neye geçmek istersin?",
        "Burada seni en çok ne düşündürüyor?",
        "Bitince ilk kime göstereceksin?",
        "Hangi kısım beklediğinden iyi gitti?",
        "Şu an neyi deniyorsun?",
        "Bu adımda neyi merak ediyorsun?",
        "Kazanım fokurduyor, seninki nasıl gidiyor?",
    ],
}


def ask_local(context: str, lang: str):
    """Ask the local Ollama model. Returns the reply text, or None if it isn't running."""
    body = json.dumps({
        "model": LOCAL_MODEL, "stream": False, "keep_alive": KEEP_ALIVE,
        "messages": [{"role": "system", "content": SYSTEM[lang]}, {"role": "user", "content": context}],
        "options": {"num_predict": 40, "temperature": 0.7},
    }).encode()
    try:
        req = urllib.request.Request(LOCAL_URL, body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.load(r)["message"]["content"]
    except Exception:
        return None


def _haiku(context: str, lang: str, client):
    try:
        if client is None:
            import anthropic
            client = anthropic.Anthropic(max_retries=0)
        r = client.messages.create(model=HAIKU, max_tokens=60, timeout=8, system=SYSTEM[lang],
                                   thinking={"type": "disabled"},  # a 15-word question needs no thinking
                                   messages=[{"role": "user", "content": context}])
        return r.content[0].text
    except Exception:
        return None


def _clean(reply):
    """First line, without quotes or a 'Question:' label; None if empty or too long."""
    if not reply:
        return None
    lines = reply.strip().splitlines()
    q = lines[0].strip() if lines else ""
    q = re.sub(r"^(question|soru)\s*:\s*", "", q, flags=re.I).strip().strip('"“”\'').strip()
    # advice or a remark instead of a question -> the gentle list instead
    return q if q.endswith("?") and len(q.split()) <= MAX_WORDS else None


def ask(context: str, lang: str = "en", client=None, local=ask_local, rng=random) -> str:
    lang = lang if lang in SYSTEM else "en"
    q = _clean(local(context, lang))
    if not q and (client is not None or os.environ.get("ANTHROPIC_API_KEY")):
        q = _clean(_haiku(context, lang, client))
    return q or rng.choice(FALLBACK[lang])
