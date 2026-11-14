"""Turns recent narration into one short, curious question. Falls back to a local list."""
import random

MODEL = "claude-haiku-5-5"
SYSTEM = ("Sen kullanıcının yanında sessizce iksir karıştıran küçük bir büyücü çıraksın. "
          "Kullanıcı sana o an ne üzerinde çalıştığını anlatıyor. Anlattığına dayanarak tek bir kısa, "
          "meraklı soru sor (en fazla 15 kelime). Tavsiye verme, yargılama, hesap sorma. Sadece soruyu yaz.")

FALLBACK = [
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
]


def ask(context: str, client=None, rng=random) -> str:
    try:
        if client is None:
            import anthropic
            client = anthropic.Anthropic()
        r = client.messages.create(model=MODEL, max_tokens=60, timeout=8, system=SYSTEM,
                                   messages=[{"role": "user", "content": context}])
        lines = r.content[0].text.strip().splitlines()
        q = lines[0].strip() if lines else ""
        if q and len(q.split()) <= 15:
            return q
    except Exception:
        pass
    return rng.choice(FALLBACK)
