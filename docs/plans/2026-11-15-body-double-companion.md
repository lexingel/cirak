# Body-double çırak: uygulama planı

> **Ajanlar için:** GEREKLİ ALT BECERİ: Bu planı görev görev uygulamak için superpowers:subagent-driven-development (önerilen) ya da superpowers:executing-plans kullan. Adımlar `- [ ]` kutularıyla takip edilir.

**Amaç:** Masaüstünde çerçevesiz duran, sessizce iksir karıştıran ve kullanıcı ona işini anlattığında arada bir kısa soru soran bir pixel-art çırak.

**Mimari:** İki süreç var. Godot 4 uygulaması (`app/`) pencereyi, çırağı, balonu, yazı kutusunu ve menüyü yönetir. Python dinleyiciyi (`listener/`) kendisi başlatır ve kapatır. Dinleyici mikrofonu dinler, konuşmayı yerelde Whisper ile yazıya çevirir, soru zamanını belirler ve soruyu Claude Haiku'ya ürettirir. Bir sorun olursa yerel listeden bir soru seçer. İkisi `ws://127.0.0.1:47613` üzerinden JSON mesajlarla konuşur.

**Teknoloji:** Godot 4.7.2 (GDScript), Python 3.10, faster-whisper (CUDA), sounddevice, numpy, websockets, anthropic, pycaw.

**Spec:** `docs/specs/2026-11-15-body-double-companion-design.md`

## Genel kısıtlar

- Windows 10. Godot: `<Godot>/Godot_v4.7.2-stable_win64.exe`. Python 3.10.11. GPU: RTX 3060 Ti 8 GB.
- **Ses bilgisayardan çıkmaz.** Dışarıya, yani Anthropic'e, sadece yazıya dökülmüş metin gider.
- Başka bir uygulama mikrofonu kullanırken dinleyici hiçbir şeyi yazıya çevirmez ve dışarı göndermez.
- **Kullanıcı sessizse soru sorulmaz.** Soru sadece kullanıcının anlatımından sonra gelir ve iki soru arasında en az belirlenen süre geçer.
- Çırak sesli konuşmaz. Arayüz ve sorular Türkçe.
- Soru tonu merak eden bir ton olmalı, hesap soran değil. En fazla 15 kelime, tek soru, tavsiye yok.
- Model `claude-haiku-5-5`. Anahtar `ANTHROPIC_API_KEY` ortam değişkeninden okunur. Anahtar yoksa ya da hata dönerse yerel listeye geçilir.
- Yasak: zamanlayıcı, hatırlatma, bildirim, istatistik, sohbet geçmişi, bas-konuş tuşu.

## Mesaj protokolü (iki tarafın ortak sözleşmesi)

Spec, mesaj adlarını kurucuya bırakmıştı. Bu planda şu adlar kullanılacak:

- Dinleyici → uygulama: `{"type":"speech_start"}`, `{"type":"speech_end"}`, `{"type":"question","text":str}`, `{"type":"paused","reason":"call"}`, `{"type":"resumed"}`
- Uygulama → dinleyici: `{"type":"typed","text":str}`, `{"type":"mic","on":bool}`, `{"type":"frequency","level":"low"|"mid"|"high"}`

Soru sıklığı (iki soru arasındaki en kısa süre): `low` 600 sn, `mid` 300 sn (varsayılan), `high` 120 sn.

## İnceleme odağı

1. **Görüşme anlatımın ortasında başlarsa:** Tampon hemen boşaltılır. Görüşme bitince o yarım anlatım yüzünden soru sorulmaz. Test: Görev 1, `test_pause_clears_buffer`.
2. **"Hmm", "tamam" gibi çok kısa sözler ya da Whisper'ın sessizlikte uydurduğu metinler** ("Altyazı M.K.", "İzlediğiniz için teşekkürler" gibi): Bunlar asla soruya yol açmaz. Test: Görev 1, `test_ignores_hallucinations_and_short`.
3. **Boş ya da sadece boşluktan oluşan yazılı mesaj:** Yok sayılır, baş sallama tepkisi de olmaz. Test: Görev 5, `test_blank_typed_ignored`.
4. **Dinleyici çökmüşse ya da hiç başlamamışsa:** Çırak çalışmaya devam eder. Hata penceresi açılmaz, bağlantı sessizce yeniden denenir. Test: Görev 6, elle kontrol.
5. **Kaydedilen konum şu an ekranda görünmüyorsa** (monitör çıkarılmış ya da çözünürlük değişmiş): Çırak görünür alana çekilir. Test: Görev 5, `test_clamp_to_screen`.

---

### Task 1: Soru kapısı (ne zaman soru sorulur)

**Dosyalar:**
- Oluştur: `listener/gate.py`, `listener/tests/test_gate.py`, `.gitignore` (içinde `.superpowers/`, `__pycache__/`, `app/.godot/`), `listener/requirements.txt`
- İlk adımda: `git init` (repo `D:\Claude\body_double`)

**Arayüzler:**
- Üretir: `class QuestionGate(min_interval: float = 300, min_words: int = 8)`, metotları şunlar:
  - `add_text(text: str, now: float) -> None`: anlatımı tampona ekler. Uydurma metinleri ve boş metni atar. Son 180 saniyeyi tutar.
  - `should_ask(now: float) -> bool`: Tamponda en az `min_words` kelime varsa ve son sorudan bu yana `min_interval` geçtiyse `True` döner.
  - `context() -> str`: tampondaki metni döndürür.
  - `mark_asked(now: float) -> None`: tamponu boşaltır ve süreyi başlatır.
  - `pause() -> None`: tamponu boşaltır.
  - `set_level(level: str) -> None`: `low`/`mid`/`high` değerini 600/300/120 sn'ye çevirir.
- Üretir: `HALLUCINATIONS: tuple[str, ...]`. Küçük harfe çevrilmiş, içinde geçmesi yeterli olan kalıplar: `"altyazı m.k"`, `"izlediğiniz için teşekkür"`, `"abone olmayı unutmayın"`, `"altyazı"`.

- [ ] **Adım 1: Başarısız testleri yaz**

```python
from gate import QuestionGate

def test_no_question_without_narration():
    g = QuestionGate(min_interval=300)
    assert not g.should_ask(now=1000)

def test_asks_after_enough_words():
    g = QuestionGate(min_interval=300, min_words=8)
    g.add_text("şimdi giriş ekranındaki butonların hizasını düzeltiyorum galiba", now=10)
    assert g.should_ask(now=12)

def test_min_interval_between_questions():
    g = QuestionGate(min_interval=300, min_words=1)
    g.add_text("bir iki üç", now=0); g.mark_asked(now=1)
    g.add_text("dört beş altı", now=100)
    assert not g.should_ask(now=200)
    assert g.should_ask(now=302)

def test_ignores_hallucinations_and_short():
    g = QuestionGate(min_words=8)
    g.add_text("Altyazı M.K.", now=1); g.add_text("hmm tamam", now=2); g.add_text("   ", now=3)
    assert not g.should_ask(now=400)

def test_pause_clears_buffer():
    g = QuestionGate(min_words=1)
    g.add_text("uzun bir anlatım burada devam ediyor", now=1)
    g.pause()
    assert not g.should_ask(now=400) and g.context() == ""

def test_level_mapping():
    g = QuestionGate(); g.set_level("high")
    assert g.min_interval == 120
```

- [ ] **Adım 2:** `cd listener && python -m pytest tests/test_gate.py -v` komutunu çalıştır. Beklenen sonuç: FAIL (`No module named 'gate'`).
- [ ] **Adım 3:** `gate.py` dosyasını yaz. Saat dışarıdan `now` olarak verilir, kod içinde `time` çağrılmaz. Kelime sayımı `len(text.split())` ile yapılır. `requirements.txt` içeriği: `faster-whisper`, `sounddevice`, `numpy`, `websockets`, `anthropic`, `pycaw`, `comtypes`, `pytest`.
- [ ] **Adım 4:** Aynı komutu çalıştır. Beklenen sonuç: 6 test geçer.
- [ ] **Adım 5:** Commit: `feat(listener): question gate`

### Task 2: Görüşme ve hoparlör bekçisi

**Dosyalar:** Oluştur: `listener/mic_guard.py`, `listener/tests/test_mic_guard.py`

**Arayüzler:**
- Üretir: `mic_in_use_by_other(entries: dict[str, tuple[int, int]], self_exe: str) -> bool`. `entries` sözlüğü, anahtar adını `(LastUsedTimeStart, LastUsedTimeStop)` çiftine eşler. Bir anahtarda `start > 0` ve `stop == 0` ise mikrofon kullanımda demektir. Anahtar adı `self_exe` yolunu içeriyorsa (`\` yerine `#` yazılmış haliyle) bu dinleyicinin kendisidir ve sayılmaz.
- Üretir: `read_mic_entries() -> dict[str, tuple[int, int]]`. `winreg` ile `HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone` altındaki anahtarları okur, hem paketli uygulamaları hem de `NonPackaged\*` alt anahtarlarını.
- Üretir: `speaker_busy(threshold: float = 0.02) -> bool`. pycaw `IAudioMeterInformation.GetPeakValue()` ile varsayılan çıkış aygıtının ses seviyesini okur. Hata olursa `False` döner.

- [ ] **Adım 1: Başarısız testleri yaz**

```python
from mic_guard import mic_in_use_by_other
SELF = r"C:\Python310\python.exe"

def test_discord_in_call():
    assert mic_in_use_by_other({"C:#Users#x#Discord.exe": (5, 0)}, SELF)

def test_finished_call():
    assert not mic_in_use_by_other({"C:#Users#x#Discord.exe": (5, 9)}, SELF)

def test_self_not_counted():
    assert not mic_in_use_by_other({"C:#Python310#python.exe": (5, 0)}, SELF)
```

- [ ] **Adım 2:** `python -m pytest tests/test_mic_guard.py -v` çalıştır. Beklenen sonuç: FAIL.
- [ ] **Adım 3:** `mic_guard.py` dosyasını yaz. `read_mic_entries` ve `speaker_busy` için test yok. Bunlar ince Windows sarmalayıcıları ve Görev 4'teki elle kontrolde sınanacak.
- [ ] **Adım 4:** Testler geçer. Ek olarak `python -c "import mic_guard; print(mic_guard.read_mic_entries())"` çalıştır. Beklenen sonuç: bir sözlük basılır, hata olmaz.
- [ ] **Adım 5:** Commit: `feat(listener): call and speaker guard`

### Task 3: Soru üretici

**Dosyalar:** Oluştur: `listener/asker.py`, `listener/tests/test_asker.py`

**Arayüzler:**
- Üretir: `FALLBACK: list[str]`, 18 adet Türkçe nazik soru. Örnekler: "Bu bitince sırada ne var?", "Takıldığın yer neresi?", "Şu an en çok neye bakıyorsun?". Hepsi en fazla 15 kelime olmalı ve "neden hâlâ", "yapmadın" gibi hesap soran bir dil içermemeli.
- Üretir: `ask(context: str, client=None, rng=random) -> str`. `client` `None` ise `anthropic.Anthropic()` oluşturmayı dener. `messages.create(model="claude-haiku-5-5", max_tokens=60, timeout=8, system=SYSTEM, messages=[{"role":"user","content":context}])` çağırır. Cevabın ilk satırını alır ve kırpar. Herhangi bir hata, boş cevap ya da 15 kelimeden uzun bir cevap gelirse `rng.choice(FALLBACK)` döner.
- `SYSTEM` (sabit metin): "Sen kullanıcının yanında sessizce iksir karıştıran küçük bir büyücü çıraksın. Kullanıcı sana o an ne üzerinde çalıştığını anlatıyor. Anlattığına dayanarak tek bir kısa, meraklı soru sor (en fazla 15 kelime). Tavsiye verme, yargılama, hesap sorma. Sadece soruyu yaz."

- [ ] **Adım 1: Başarısız testleri yaz**

```python
import random
from asker import ask, FALLBACK

class Boom:
    class messages:
        @staticmethod
        def create(**k): raise RuntimeError("offline")

class Fake:
    def __init__(self, text): self.text = text
    @property
    def messages(self):
        t = self.text
        class M:
            @staticmethod
            def create(**k):
                assert k["model"] == "claude-haiku-5-5"
                return type("R", (), {"content": [type("C", (), {"text": t})()]})()
        return M

def test_uses_model_reply():
    assert ask("buton hizası", client=Fake("Hangi buton en çok canını sıkıyor?")) == "Hangi buton en çok canını sıkıyor?"

def test_falls_back_on_error():
    assert ask("x", client=Boom(), rng=random.Random(1)) in FALLBACK

def test_falls_back_on_too_long():
    assert ask("x", client=Fake(" ".join(["kelime"] * 20))) in FALLBACK

def test_fallback_list_shape():
    assert len(FALLBACK) == 18 and all(len(q.split()) <= 15 for q in FALLBACK)
```

- [ ] **Adım 2:** `python -m pytest tests/test_asker.py -v` çalıştır. Beklenen sonuç: FAIL.
- [ ] **Adım 3:** `asker.py` dosyasını yaz.
- [ ] **Adım 4:** Testler geçer.
- [ ] **Adım 5:** Commit: `feat(listener): question asker with offline fallback`

### Task 4: Dinleyici süreci (mikrofon, Whisper, WebSocket)

**Dosyalar:** Oluştur: `listener/hearing.py`, `listener/main.py`

**Arayüzler:**
- Tüketir: Görev 1-3'teki `QuestionGate`, `mic_in_use_by_other`, `read_mic_entries`, `speaker_busy`, `ask`.
- Üretir: `class Hearing(on_start, on_end)`. sounddevice ile 16 kHz mono ses alır, 30 ms'lik bloklar halinde. Konuşma algılama enerjiye dayalı: RMS `> threshold` olunca `on_start()` çağrılır. 1,5 saniye sessizlikten sonra `on_end(audio: np.ndarray)` çağrılır. `threshold` bir ayar düğmesidir, varsayılan 0,015. Yanına `# ponytail: energy VAD, swap for silero if noisy rooms misfire` yorumu konur.
- Üretir: `transcribe(audio) -> str`. `WhisperModel("small", device="cuda", compute_type="float16")` kullanır. CUDA yüklenemezse `device="cpu", compute_type="int8"` ile tekrar dener. Çağrı `language="tr", vad_filter=True` ile yapılır.
- Üretir: `main.py`, protokoldeki WebSocket sunucusu (`127.0.0.1:47613`, tek istemci). Her saniye bekçiyi kontrol eder. Başka bir uygulama mikrofonu kullanıyorsa `gate.pause()` çağırır, sesi atar ve `paused` gönderir. Görüşme bitince `resumed` gönderir. `on_end` geldiğinde: bekçi temizse ve `speaker_busy()` değilse yazıya çevirir, `gate.add_text` çağırır, `speech_end` gönderir. `should_ask` doğruysa `ask` ve `mark_asked` çağrılır, sonra `question` gönderilir. `typed` mesajı da aynı `add_text` ve `should_ask` yolundan geçer. `mic:false` gelince ses alma durur. **İstemci 10 saniye boyunca bağlı değilse süreç kendini kapatır**, böylece arkada kimsesiz bir mikrofon kalmaz.

- [ ] **Adım 1:** `pip install -r listener/requirements.txt` çalıştır. CUDA DLL hatası olursa `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` kur. CPU'ya düşmek kabul edilebilir.
- [ ] **Adım 2:** `hearing.py` ve `main.py` dosyalarını yaz.
- [ ] **Adım 3, elle kontrol:** `python listener/main.py` çalıştır. Ayrı bir terminalde `python -m websockets ws://127.0.0.1:47613` ile bağlan. Türkçe bir şeyler anlat. Beklenen: `speech_start`/`speech_end` gelir, en az 8 kelimeden sonra bir `question` gelir. Discord'da bir sesli kanala gir. Beklenen: `paused` gelir ve konuşmak hiçbir şey üretmez. YouTube'da konuşmalı bir video aç. Beklenen: `question` gelmez. Bağlantıyı kapat. Beklenen: süreç 10 saniye içinde kapanır.
- [ ] **Adım 4:** Testlerin hepsi geçer (`python -m pytest listener/tests -v`).
- [ ] **Adım 5:** Commit: `feat(listener): mic, whisper and websocket loop`

### Task 5: Godot uygulaması, pencere ve çırak

**Dosyalar:**
- Oluştur: `app/project.godot`, `app/main.tscn`, `app/main.gd`, `app/apprentice.tscn`, `app/apprentice.gd`, `app/bubble.gd`, `app/art/apprentice.png` (geçici sprite), `app/tests/run_tests.gd`

**Arayüzler:**
- `project.godot`: `display/window/size/borderless=true`, `transparent=true`, `always_on_top=true`, `display/window/per_pixel_transparency/allowed=true`, `rendering/viewport/transparent_background=true`, pencere boyutu 260x220, `display/window/subwindows/embed_subwindows=false`.
- `apprentice.gd` (Node2D, içinde AnimatedSprite2D): `enum State { WORKING, LISTENING, NODDING, ASKING }`. Üretir: `func handle(msg: Dictionary) -> void`. `speech_start` gelince LISTENING. `speech_end` gelince NODDING, bir süre sonra WORKING. `question` gelince ASKING ve `bubble.show_text(text)`. `paused` gelince WORKING. Üretir: `func on_typed(text: String) -> bool`. Metin boş ya da sadece boşluksa `false` döner ve hiçbir şey yapmaz. Değilse NODDING'e geçer ve `true` döner.
- `bubble.gd`: `func show_text(t: String) -> void`. 8 saniye görünür kalır, sonra 0,5 saniyede kaybolur.
- `main.gd`: Üretir: `static func clamp_to_screen(pos: Vector2i, size: Vector2i, rect: Rect2i) -> Vector2i`. Sol tuşla basılınca sürükleme başlar, fare 4 pikselden fazla oynarsa sürükleme sayılır. Daha az oynarsa tıklama sayılır ve yazı kutusu açılır (LineEdit, Enter ile gönderilir, Esc ile kapanır). Sağ tık PopupMenu açar: "Mikrofonu kapat"/"Mikrofonu aç", "Soru sıklığı" alt menüsü (Az, Orta, Çok), "Kapat". Fare geçirgenliği `DisplayServer.window_set_mouse_passthrough(polygon)` ile ayarlanır. Polygon çırağın kutusudur. Balon ya da yazı kutusu açıkken polygon onları da kapsayacak şekilde genişler. Konum, mikrofon durumu ve sıklık `user://settings.cfg` dosyasına (ConfigFile) kaydedilir. Açılışta okunur ve konum `clamp_to_screen` ile ekrana sığdırılır.
- Geçici sprite: brainstorm taslağındaki 16x15 çırak ızgarası 3x büyütülür. WORKING için 2 kare kullanılır: kepçe çubuğu bir sağa bir sola, kazandan kabarcık çıkar.

- [ ] **Adım 1: Başarısız testleri yaz** (`app/tests/run_tests.gd`, `extends SceneTree`, her test `assert` kullanır, sonunda `quit(0)` ya da hata sayısıyla `quit(1)`)

```gdscript
func test_states():
    var a = preload("res://apprentice.tscn").instantiate(); root.add_child(a)
    a.handle({"type":"speech_start"}); assert(a.state == a.State.LISTENING)
    a.handle({"type":"question","text":"Takıldığın yer neresi?"}); assert(a.state == a.State.ASKING)
    a.handle({"type":"paused","reason":"call"}); assert(a.state == a.State.WORKING)

func test_blank_typed_ignored():
    var a = preload("res://apprentice.tscn").instantiate(); root.add_child(a)
    assert(a.on_typed("   ") == false and a.state == a.State.WORKING)
    assert(a.on_typed("menüyü yapıyorum") == true and a.state == a.State.NODDING)

func test_clamp_to_screen():
    var r = Rect2i(0, 0, 1920, 1080)
    assert(Main.clamp_to_screen(Vector2i(3000, 50), Vector2i(260, 220), r) == Vector2i(1660, 50))
    assert(Main.clamp_to_screen(Vector2i(100, 100), Vector2i(260, 220), r) == Vector2i(100, 100))
```

(Çırak kendi sahnesinde durur: `app/apprentice.tscn`. `main.gd` dosyasında `class_name Main` tanımlıdır.)

- [ ] **Adım 2:** `"<Godot>/Godot_v4.7.2-stable_win64.exe" --headless --path app -s tests/run_tests.gd` çalıştır. Beklenen sonuç: hata ve 1 çıkış kodu. Çıktıda `SCRIPT ERROR` satırları da aranır.
- [ ] **Adım 3:** Dosyaları yaz.
- [ ] **Adım 4:** Aynı komut 0 çıkış kodu verir ve `SCRIPT ERROR` satırı çıkmaz.
- [ ] **Adım 5, elle kontrol:** `godot --path app` ile çalıştır. Çırak masaüstünde çerçevesiz görünür. Çırağın dışına tıklayınca alttaki pencere tıklanır. Çırak sürüklenebilir. Kapatıp açınca aynı yerde başlar. Ekran görüntüsü al.
- [ ] **Adım 6:** Commit: `feat(app): frameless apprentice window`

### Task 6: Bağlantı (uygulama ↔ dinleyici)

**Dosyalar:** Oluştur: `app/link.gd`. Değiştir: `app/main.gd`, `app/tests/run_tests.gd`

**Arayüzler:**
- Tüketir: protokol, `apprentice.handle`, `apprentice.on_typed`.
- Üretir: `link.gd` (Node, `class_name Link`). `static func parse(text: String) -> Dictionary`: geçersiz JSON ya da `type` alanı olmayan mesaj için `{}` döner. `func send(msg: Dictionary) -> void`: bağlantı yoksa mesajı sessizce atar. `signal message(msg: Dictionary)`. `_ready` içinde `OS.create_process("python", [ProjectSettings.globalize_path("res://").path_join("../listener/main.py")])` çağrılır ve pid saklanır. `WebSocketPeer` 2 saniyede bir yeniden bağlanmayı dener. Hata penceresi açılmaz. `NOTIFICATION_WM_CLOSE_REQUEST` ve `_exit_tree` sırasında `OS.kill(pid)` çağrılır.
- `main.gd` bağlantıları: `link.message` sinyali `apprentice.handle`'a bağlanır. Yazı kutusu `on_typed` doğru dönerse `link.send({"type":"typed","text":t})` çağırır. Menüden mikrofon değişince `mic`, sıklık değişince `frequency` gönderilir. Bağlantı her kurulduğunda kayıtlı `mic` ve `frequency` değerleri yeniden gönderilir.

- [ ] **Adım 1: Başarısız test ekle**

```gdscript
func test_parse():
    assert(Link.parse('{"type":"question","text":"Ne var?"}')["text"] == "Ne var?")
    assert(Link.parse("bozuk{") == {})
    assert(Link.parse('{"text":"tipsiz"}') == {})
```

- [ ] **Adım 2:** Godot test komutunu çalıştır. Beklenen sonuç: FAIL.
- [ ] **Adım 3:** `link.gd` dosyasını yaz ve `main.gd` bağlantılarını yap.
- [ ] **Adım 4:** Testler geçer.
- [ ] **Adım 5, elle kontrol:** `godot --path app` ile tek komutla aç. Konuşunca çırak başını kaldırır. Bir süre anlatınca balonda bir soru çıkar. Yazı kutusuna yazınca çırak baş sallar. Görüşmedeyken tepki vermez. Uygulamayı kapatınca `python` süreci de kapanır (Görev Yöneticisi'nden ya da `tasklist | grep python` ile kontrol edilir). Dinleyiciyi elle öldürünce çırak çalışmaya devam eder ve hata penceresi açılmaz (inceleme odağı 4).
- [ ] **Adım 6:** Commit: `feat(app): link to listener`

### Task 7: Gerçek çırak sprite'ı

**Dosyalar:** Değiştir: `app/art/apprentice.png`, `app/apprentice.tscn` (SpriteFrames)

**Arayüzler:** Tüketir: Görev 5'teki dört durum. Üretir: `working` (6-8 kare döngü, kepçe karıştırma ve kabarcık), `listening` (2 kare, baş yukarıda, hafif nefes alma), `nodding` (3 kare), `asking` (2 kare, el kalkık). Kare boyutu 48x48. Bunlar kullanıcının `pixart` becerisiyle koddan çizilir. Spec çizim aracını kurucuya bıraktı, kullanıcının kendi aracı seçildi.

- [ ] **Adım 1:** pixart ile kareleri çiz. Sonra pixart lint ve inceleme sayfasını çalıştır.
- [ ] **Adım 2:** Kareleri 3x büyütülmüş bir inceleme sayfasında ya da GIF'te kullanıcıya göster ve onay al. Kullanıcı onaylamadan sprite yerine konmaz.
- [ ] **Adım 3:** SpriteFrames'e bağla. Godot testlerini çalıştır, hepsi geçmeli.
- [ ] **Adım 4:** Uygulamayı açıp ekran görüntüsü al.
- [ ] **Adım 5:** Commit: `art: apprentice sprite`

## Çalıştırma

```bash
"<Godot>/Godot_v4.7.2-stable_win64.exe" --path D:/Claude/body_double/app
```
