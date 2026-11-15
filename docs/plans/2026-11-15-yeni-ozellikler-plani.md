# Çırak: yeni özellikler planı (sesle komut, medya, Claude/Codex, dağıtım)

Tarih: 2026-11-15 · Kaynak: kodun okunması (app/, listener/), bu PC'de salt-okunur kontroller, belgeler (kaynaklar en sonda). **Kod değiştirilmedi.**

Kısa özet: Dört istek de aynı iskelete oturuyor. İlk üçü (uygulama açma, medya, Claude'a sorma) **tek bir "komut yolu"** ister: Whisper metni çıktıktan sonra, soru kapısından önce, "Çırak, …" ile başlayan cümleyi yakalayıp bir eylem tablosuna bakmak. Bu yol bir kez kurulunca her yeni komut 5-15 satır. Dördüncüsü (dağıtım) kodu az değiştirir, asıl iş paketleme; ama iki önemli bulgusu var: **Python 3.10 ömrünü doldurdu** (2026-10-01) ve `listener.log` kurulum klasörüne yazıyor (Program Files'ta çalışmaz). Bir yan karar üçünü birden kolaylaştırıyor: venv'i Python 3.12'ye taşımak hem dağıtımı hem medya API'sini (WinRT paketleri 3.11+) açar.

Boyutlar: **S** = birkaç satır, bir oturumun parçası · **M** = bir-iki dosyada 20-60 satır + test · **L** = birden fazla dosya, yeni süreç ya da indirme.

---

## 0) Ortak altyapı: komut yolu

Üç ses özelliği de aynı üç parçayı ister; önce bunlar.

### 0.1 Komut mu, anlatım mı? (uyandırma sözü + kalıp eşleme)

**Bulgu:** Dinleyici zaten her sözü Whisper'a gönderiyor (`listener_core.py:48 speech_end → transcribe`). Yani ayrı bir uyandırma-sözü motoru (Porcupine, openWakeWord) **gerekmez**: metin elimizde, başına bakmak bedava. Üç seçenek:

| Seçenek | Nasıl | Artı | Eksi |
|---|---|---|---|
| **A. Metin öneki + kalıp (önerilen)** | Metin "çırak"/"cirak"/"apprentice" ile başlıyorsa komut adayı; geri kalanı 8-10 regex kalıbıyla eşle | Sıfır bağımlılık, saf fonksiyon, test edilebilir, 0 ms | Whisper "Çırak"ı "Cirak/Çırağ/Chirac" yazabilir → normalize + küçük varyant listesi |
| B. LLM niyet sınıflandırması (Ollama) | Her metni qwen'e "komut mu?" diye sor | Serbest ifade | Her sözde 1-3 s, Ollama yoksa çalışmaz, 3b Türkçede güvenilmez, yanlış pozitif = yanlış uygulama açılır |
| C. Ayrı uyandırma-sözü modeli | Ses üzerinde sürekli tarama | Whisper'dan önce yakalar | Yeni bağımlılık + CPU, mevcut VAD/Whisper zinciriyle çakışır |

**Whisper'a yardım (S, bedava):** `hearing.py:_run` içinde `transcribe(..., initial_prompt=...)` ya da `hotwords="Çırak, Spotify, Discord, …"` ver; faster-whisper ikisini de destekler (`initial_prompt: "prompt for the first window"`, `hotwords: "Hotwords/hint phrases to provide the model with"`, kaynak [FW]). Uygulama adlarını `hotwords`a koymak "Spotify'ı" → "spotifayı" türü hataları azaltır. Dikkat: `initial_prompt` halüsinasyonu artırabilir; önce `hotwords` dene.

**Yanlış tetik koruması:**
- Komut yalnızca cümle **başında** uyandırma sözü varsa; "…çırak gibi çalışıyorum" anlatımdır.
- Uyandırma sözü var ama kalıp eşleşmedi → **anlatım sayılmaz, soru da sorulmaz**, çırak kısa bir "Anlamadım" balonu gösterir (geri bildirim; aksi halde kullanıcı neden olmadığını bilemez).
- Eşik: eşleme için tam kelime, bulanık değil ("spotif" yetmez). Uygulama adında bulanıklık yalnızca Türkçe ekleri soymak için (`'ı/'i/'u/'ü/'yı`, apostrof sonrası at).
- `gate.py:MIN_UTTERANCE_WORDS = 3` komutları etkilemez çünkü komut kontrolü kapıdan **önce** çalışır; "Çırak, duraklat" iki kelimedir ve yine yakalanır.

### 0.2 Hoparlör çalarken komut (speaker_busy ile ilişki)

**Bulgu (önemli):** `listener_core.py:37` hoparlör çalıyorsa `speech_start`ta `_heard=False` yapar, `speech_end` (satır 42) **yazıya bile çevirmeden** döner. Yani müzik çalarken "Çırak, duraklat" hiç duyulmaz. Bu, medya komutlarının tam da çalışması gereken anı kapatıyor.

Seçenekler:
1. **Kulaklık anahtarı** (önceki planda 6.1): "Kulaklıktayım" açıkken hoparlör kapısı devre dışı → komutlar müzikte de çalışır, mikrofona müzik girmiyor. Kulaklıkla çalışan için doğru çözüm, S.
2. **Hoparlörde "sadece komut" modu:** `speaker_busy` iken de yazıya çevir, ama metni **yalnızca** komut kalıbına sok, asla soru kapısına verme. Bedeli: hoparlörden çıkan müzik enerji-VAD'ı sürekli tetikler, Whisper her 8-30 s'de bir şarkı parçası çevirir (GPU'da ~0.3 s, CPU'da 2-5 s → laptopta ısı). `MAX_SECONDS`i bu modda 8'e çekmek yükü sınırlar. Ayar olarak, varsayılan kapalı. M.
3. Olduğu gibi bırak: komutlar yalnızca sessizken (müzik duraklatılmışken "devam et" çalışır, çalarken "duraklat" çalışmaz). Kullanıcı medya tuşunu kullanır.

**Öneri:** 1 + 3. Hoparlörden müzik dinleyen biri için 2'yi sonra, isteğe göre.

### 0.3 Çırağın onayı: `say` mesajı

Yeni mesaj dinleyici → uygulama: `{"type":"say","text":"Spotify açılıyor"}`. `apprentice.gd:handle` içine bir dal: `bubble.show_text(text)` + `_enter(State.NODDING)` (soru değil, "yaptım" baş sallaması). ~4 satır. Komut başarısızsa aynı balon: "Spotify'ı bulamadım". Sesli onay yok (çırak konuşmaz, spec).

**Komut için "emin misin?" diyaloğu yok:** uygulama açmak ve şarkı atlamak geri alınabilir; onay sürtünmesi ADHD bağlamında özelliği öldürür. Tek istisna Claude'a göndermek (bölüm 3): metin PC'den çıkar, orada ikinci adım var.

### 0.4 Dosyalar

- **Yeni `listener/commands.py`** (saf): `parse(text, lang) -> (intent, arg) | None`; `WAKE = ("çırak", "cirak", "çırağ", "apprentice")`; kalıp tablosu. Test: `tests/test_commands.py` (TR/EN 10-15 örnek + 5 negatif).
- `listener/listener_core.py:speech_end`: `transcribe` sonrası `cmd = commands.parse(text, self.lang)`; varsa `self.run_command(cmd)` (dışarıdan verilen `actions` sözlüğü: `{"open_app": fn, "media": fn, "ask_claude": fn}`) ve `send({"type":"say", ...})`, `_narrate` çağrılmaz. `on_client` içinde `typed` için de aynı (yazarak komut vermek bedava gelir).
- `listener/main.py:run`: `Listener(..., actions={...})`.
- `app/apprentice.gd:handle`: `"say"` dalı.

Boyut: **M** (altyapı). Her üç özellik buna yaslanır.

---

## 1) Sesle uygulama açma ("Çırak, Spotify'ı aç")

### Bulgular (bu PC)

- `shell:AppsFolder` 270 girdi döndürüyor ve **hem Store hem klasik uygulamaları tek listede** veriyor: `Spotify | SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify` (Store, **Start Menu'de .lnk'si yok**), `Discord | com.squirrel.Discord.Discord`, `Claude | Claude_pzs8sxrjxfjjc!Claude`.
- Start Menu .lnk sayısı 160 (ProgramData) + 74 (kullanıcı); Spotify'ın .lnk'si yok → tek başına .lnk taraması Spotify'ı kaçırır.
- `App Paths` kayıt defteri (chrome.exe, excel.exe, …) klasik exe'ler için var ama Store uygulamalarını hiç içermez.

### Önerilen yaklaşım: AppsFolder tek kaynak

1. **Dizin kurma (başlangıçta bir kez, ~0.5 s):** PowerShell tek satır: `(New-Object -ComObject Shell.Application).NameSpace('shell:AppsFolder').Items() | % { $_.Name + '|' + $_.Path }` → `{ad.lower(): path}` sözlüğü. `subprocess.run([... "-NoProfile", "-Command", ...], creationflags=CREATE_NO_WINDOW)`; pythonw altında pencere açılmaz. comtypes zaten bağımlılık ama Shell.Application'ı dinamik dispatch ile sürmek pythonw+COM apartman meselesi çıkarır; PowerShell daha az risk. (ponytail: dizin başlangıçta; sonra kurulan uygulama yeniden başlatmada görünür, `mics` listesiyle aynı mantık.)
2. **Başlatma:** `os.startfile("shell:AppsFolder\\" + path)` — AUMID'ler (Store) ve kayıtlı klasik uygulamalar için aynı çağrı. Alternatif `subprocess.Popen(["explorer.exe", "shell:AppsFolder\\"+path])`. Hiçbir zaman `shell=True`, hiçbir zaman metinden gelen bir yol.
3. **Eşleme:** komut argümanını normalize et (küçük harf, Türkçe eki soy), AppsFolder adlarında **tam ad** ara; yoksa "ad ile başlayan tek sonuç" (örn. "visual studio" → "Visual Studio Code"? iki sonuç varsa açma, "Hangisi: Visual Studio, Visual Studio Code?" balonu).
4. **Takma adlar (kullanıcının kontrolü):** `%LOCALAPPDATA%\Cirak\apps.json` (bkz. 4.6 ayar yeri): `{"müzik": "Spotify", "kod": "Visual Studio Code"}`. Dosya yoksa yalnızca AppsFolder adları geçer. Bu dosya aynı zamanda **izin listesi görevi** görür: `"allow_only": true` yazıldıysa yalnızca listedekiler açılır. Varsayılan: AppsFolder'daki her şey (kullanıcının kendi kurduğu uygulamalar; "format c" gibi bir şey listede yok).

**Güvenlik sınırı:** metinden çalıştırmaya giden tek şey AppsFolder sözlüğünden seçilmiş bir **anahtar**tır; argüman yok, komut satırı yok, URL yok. "Çırak, cmd'yi aç ve …" → yalnızca "cmd" eşleşir (Komut İstemi AppsFolder'da varsa açılır, geri kalan yok sayılır). İstersen `apps.json`a `"deny": ["Komut İstemi", "PowerShell", "Kayıt Defteri Düzenleyicisi"]` — S.

### Alternatifler

- **.lnk taraması:** Store uygulamalarını kaçırır (Spotify). Atla.
- **App Paths kaydı:** eski exe'ler için, Store yok. Atla.
- **`os.startfile("spotify")` deneyip görmek:** Çalışırsa şans, çalışmazsa sessiz hata. Atla.
- **Spotify URI (`spotify:`), `discord://`:** uygulamaya özel, genel değil. Atla.

### Değişen dosyalar

- Yeni `listener/apps.py`: `index() -> dict`, `find(index, spoken, aliases) -> path | list | None` (saf, testli), `launch(path)`.
- `listener/commands.py`: kalıplar `^(aç|başlat|open|launch|start)\s+(.+)$` ve `^(.+?)('?[ıiuü]|'?y[ıiuü])?\s*(aç|başlat)$` (TR: "Spotify'ı aç"), EN: `open|launch|start (.+)`.
- `listener/main.py`: `actions["open_app"]`.
- Test: `tests/test_apps.py` (ek soyma, iki sonuç, bulunamadı).

**Boyut:** M (0.4 altyapı üstüne S-M). **Risk:** düşük. Whisper özel adları yanlış yazar (hotwords yardımcı); AppsFolder adları yerelleştirilmiş ("Komut İstemi") → takma adlar.

---

## 2) Medya kontrolü (sonraki, duraklat, devam, önceki, ses)

### Bulgular

**GSMTC (Windows.Media.Control)** — [MS-GSMTC-M], [MS-GSMTC-S]:
- Windows 10 1809+ (bu PC 19045, uygun). `GlobalSystemMediaTransportControlsSessionManager.RequestAsync()` → `GetCurrentSession()` ("the session the system believes the user would most likely want to control") / `GetSessions()`.
- Oturum: `SourceAppUserModelId` (ör. `Spotify.exe` ya da Store AUMID; tarayıcıda YouTube için `chrome.exe`/`msedge.exe`), `GetPlaybackInfo().PlaybackStatus`, `TryGetMediaPropertiesAsync()` (Title/Artist), `TryPlayAsync / TryPauseAsync / TryTogglePlayPauseAsync / TrySkipNextAsync / TrySkipPreviousAsync / TryStopAsync`.
- **Ses seviyesi yok**: GSMTC'de volume metodu bulunmuyor. Ses için pycaw (zaten bağımlılık) ya da VK tuşları.

**Python'dan GSMTC:**
- `winrt-Windows.Media.Control` (pywinrt, Oct 2026): modül `winrt.windows.media.control`, **Python ≥ 3.11** [PYPI-WRT]. Ek paketler: `winrt-runtime>=4` + her ad alanı için ayrı paket (`winrt-Windows.Foundation` IAsyncOperation için) [PYWINRT]. Mevcut venv **3.10** → kurulamaz.
- Eski `winsdk` 1.0.0b10 (Ağu 2023) 3.10'u destekler ama beta ve bakımsız [PYPI-WINSDK]. Üretim için zayıf dayanak.
- **PowerShell köprüsü:** `[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime]` + `IAsyncOperation`ı `AsTask` ile bekletmek PS 5.1'de ~15 satırlık yansıma hilesi ister; her çağrı yeni süreç (~300-500 ms). Bağımlılıksız ama kırılgan; sadece "ne çalıyor?" okumak için makul, kontrol için değil.

**Medya sanal tuşları** [MS-VK]: `VK_MEDIA_NEXT_TRACK 0xB0`, `VK_MEDIA_PREV_TRACK 0xB1`, `VK_MEDIA_STOP 0xB2`, `VK_MEDIA_PLAY_PAUSE 0xB3`, `VK_VOLUME_MUTE 0xAD`, `VK_VOLUME_DOWN 0xAE`, `VK_VOLUME_UP 0xAF`. `ctypes.windll.user32.keybd_event(vk, 0, 0, 0)` + `KEYEVENTF_KEYUP` → 5 satır, bağımlılık yok. Windows bu tuşları **zaten GSMTC'nin güncel oturumuna** yönlendirir; yani "hangi uygulama çalıyor" sorusunu Windows bizim yerimize çözer (Spotify ya da tarayıcıdaki YouTube, en son hangisi aktifse).

**Spotify Web API** [SPOT]: `POST /me/player/next`, OAuth kapsamı `user-modify-playback-state`, **"This API only works for users who have Spotify Premium"**, geliştirici panelinde uygulama kaydı + token yenileme. Yalnızca Spotify; YouTube'u kapsamaz. **Atla.**

### Önerilen yaklaşım: iki aşama

**Aşama 1 (S, bugün yapılabilir):** medya tuşları + pycaw ses.
- Yeni `listener/media.py`: `press(vk)`; `next/prev/play_pause/stop` tuşla; `volume(delta)`/`mute()` için ya `VK_VOLUME_*` (sistem sesi, Windows'un ses göstergesi de çıkar) ya pycaw `IAudioEndpointVolume.SetMasterVolumeLevelScalar` (sessiz, ±%10 adım). pycaw zaten `mic_guard.py`de; `AudioUtilities.GetSpeakers()` kodu kopyalanır. Tercih: pycaw (göstergesiz, kesin adım).
- Komut kalıpları (`commands.py`): TR `sonraki|geç|atla`, `duraklat|dur|sus`, `devam|oynat|çal`, `önceki|geri`, `sesi (aç|yükselt|arttır)`, `sesi (kıs|azalt|düşür)`, `sessize al`; EN `next|skip`, `pause|stop`, `play|resume`, `previous|back`, `volume up|louder`, `volume down|quieter`, `mute`.
- Onay balonu: "Sonraki şarkı" / "Duraklattım".

**Aşama 2 (M, venv 3.12'ye geçince, karar K1):** GSMTC salt-okunur + hedefli kontrol.
- `winrt-runtime`, `winrt-Windows.Media.Control`, `winrt-Windows.Foundation` ekle. `GetCurrentSession()` → `SourceAppUserModelId` + başlık: balon "Spotify: sonraki → <şarkı adı>" olur; iki oturum varsa (Spotify duraklatılmış, YouTube çalıyor) `GetSessions()` içinden `PlaybackStatus == Playing` olanı seç ve **onun** `TrySkipNextAsync()`'ini çağır. Tuşla yapılamayan tek şey bu "doğru oturumu seçmek". Async: `asyncio.run(...)` worker thread'inde (zaten ayrı thread).
- Ek faydası: `speaker_busy` yerine/yanına **"çalan var mı" bilgisi** — ama pycaw tepe ölçeri oyun/sistem seslerini de yakalar, GSMTC yalnızca kayıtlı medya oturumlarını. İkisini birleştirme; ölçer kalsın.

### Mevcut mantıkla bağ (speaker_busy / mic_guard)

- **Hoparlör kapısı:** bkz. 0.2. Kulaklık anahtarı olmadan "duraklat" müzik çalarken duyulmaz. Bu, medya özelliğinin **ön koşulu**; önce 6.1 kararı.
- **Komut sonrası:** "duraklat" → hoparlör susar → `speaker_busy()` False → anlatım normal akar. "devam et" → müzik → kapı tekrar kapanır (doğru: şarkı sözü soruya dönüşmez).
- **Görüşme (mic_guard):** `call_busy` iken `listening` False, komutlar da işlenmez. Doğru: Discord görüşmesinde "sonraki" dememek daha iyi; spec "görüşmede hiçbir şeyi yazıya çevirme" diyor. Değişiklik yok.
- **Kendi sesimiz:** çırak ses çıkarmıyor; "medya tuşu bastıktan sonra kendi sesini duymak" sorunu yok.

### Değişen dosyalar

- Yeni `listener/media.py` (+ `tests/test_media.py`: sadece kalıp → eylem adı eşlemesi; tuş basma test edilmez).
- `listener/commands.py` kalıplar; `listener/main.py` `actions["media"]`.
- Aşama 2: `listener/requirements.txt` + `.lock` (3 paket), `media.py:current()`.

**Boyut:** Aşama 1 S, Aşama 2 M. **Risk:** düşük/orta. Tuşlar: Spotify ve tarayıcılar medya tuşlarını dinler; bazı oyun/overlay yazılımları (Overwolf bu PC'de otomatik başlıyor) tuşları yutabilir — gerçek testte bak. GSMTC: `TryGetMediaPropertiesAsync` bazı oturumlarda boş başlık döner; balon metni "Sonraki" ile yetinir.

---

## 3) Claude'a / Codex'e soru ya da iş göndermek

### Bulgular (bu PC, salt-okunur)

| Ne | Durum |
|---|---|
| Claude Code CLI | **Var:** `claude 2.1.302`, `C:\nvm4w\nodejs\claude.cmd` → `…\nvm\v24.21.0\node_modules\@anthropic-ai\claude-code\bin\claude.exe`. **Yol nvm sürümüne bağlı**: kodda `shutil.which("claude")` kullan, yolu yazma. |
| Claude Desktop | **Var** (MSIX `Claude_5.11492.5.0_x64__pzs8sxrjxfjjc`). `claude://` protokolü HKCR'de kayıtlı → `Claude.exe -- "%1"`. |
| `claude-cli://` | **Kayıtlı** (HKCU\Software\Classes\claude-cli → `claude.exe --handle-uri "%1"`). |
| Codex CLI | **Yok** (`where codex` boş). |
| Windows Terminal (`wt.exe`) | **Yok**; `claude-cli://` Windows'ta "Windows Terminal, sonra PowerShell, sonra cmd" sırasını izler → burada PowerShell penceresi açılır [CC-DL]. |

**Doğrulanmış arayüzler:**

- **Headless:** `claude -p "soru"` ("Print response without interactive mode"); `--output-format text|json|stream-json`; `--tools ""` ("Use `""` to disable all" → araç yok, izin sorusu yok); `--permission-mode default|acceptEdits|plan|auto|dontAsk|bypassPermissions`; `--permission-prompts none` ("Pass `none` when nobody can answer, and Claude Code denies them instead"); `--max-turns N`; `--no-session-persistence`; `--append-system-prompt "…"`; `--bare` (hook/skill/MCP/CLAUDE.md yüklemez, "scripted calls start faster"); `--add-dir`; stdin: `cat file | claude -p "…"` [CC-CLI]. `--dangerously-skip-permissions` = bypassPermissions; **kullanılmaz**.
- **Claude Code derin bağlantı:** `claude-cli://open?cwd=<mutlak yol>&q=<URL-encoded metin>`; `q` en fazla 5.000 karakter; **"The prompt is populated but not sent until you press Enter"**; "A deep link never executes anything on its own"; pencerede "Prompt from an external link" uyarısı; Windows: `Start-Process "claude-cli://open?…"` / `start "" "…"`; `cwd`de `..` ve UNC reddedilir [CC-DL].
- **Claude Desktop derin bağlantı:** `claude://claude.ai/new?q=…` (yeni sohbet, alan **önceden doldurulur, gönderilmez**, ~14.000 karakter), `claude://code/new?q=…&folder=…` (Desktop'ın Code sekmesi), `claude://cowork/new?q=…&folder=…&file=…`; Windows: `start "" "claude://claude.ai/new?q=Hello"` [CL-DESK].
- **Codex:** `codex exec [flags] [PROMPT]` ("scripted or CI-style runs"), `PROMPT` `-` ise stdin; `--sandbox read-only|workspace-write|danger-full-access`; `-C <path>` çalışma dizini; `-o <path>` son mesajı dosyaya; `--json`; `--yolo` (= `--dangerously-bypass-approvals-and-sandbox`, "Dangerous") **kullanılmaz** [CODEX]. Kurulum komutu belgenin okunan kısmında yoktu; kurulum kullanıcının kararı (K5).

### Önerilen yaklaşım: iki komut, iki çıkış yeri

**A. "Çırak, Claude'a sor: …" → cevap balonda (M).**
- `subprocess.run([which("claude"), "-p", soru, "--output-format", "text", "--tools", "", "--bare", "--no-session-persistence", "--max-turns", "1", "--append-system-prompt", "Answer in at most two short sentences."], timeout=60, creationflags=CREATE_NO_WINDOW, cwd=<çalışma dizini>)`.
- `--tools ""` → Claude dosya okuyamaz, komut çalıştıramaz; izin sorusu hiç oluşmaz, "tehlikeli araç otomatik onayı" sorunu tanım gereği yok. Sadece bilgi sorusu.
- Çıkış: `say` balonu (bölüm 0.3). 15 kelime sınırı burada **uygulanmaz**; `bubble.show_seconds` kelimeyle uzuyor zaten (`bubble.gd:30`). 60 kelimeyi aşarsa kes + "…" ve tam metni `%LOCALAPPDATA%\Cirak\last_answer.txt`e yaz (balon küçük; kullanıcı isterse açar). Çırak beklerken `listening` pozunda kalır (0.3 düşünme hissi).
- Gecikme 5-20 s; `claude` kullanıcının planından harcar. Hata (claude yok, giriş yok, zaman aşımı) → "Claude'a ulaşamadım".

**B. "Çırak, Claude'a iş ver: …" → yeni terminal, kullanıcı Enter'a basar (S).**
- `os.startfile("claude-cli://open?cwd=" + quote(workdir) + "&q=" + quote(metin))`. Claude Code kendi penceresinde, normal etkileşimli izinlerle; metin **gönderilmeden önce ekranda**, kullanıcı okur, düzeltir, Enter. Araç izinleri her zamanki gibi sorulur: otomatik onay yok, çırak hiçbir şeyi onaylamaz.
- Codex için aynı kalıp yok (Codex'in derin bağlantısı yok); Codex kurulursa B'nin karşılığı `codex exec --sandbox read-only -C <dir> -o <tmp> "<metin>"` + balon (A gibi), ya da PowerShell penceresinde `codex "<metin>"` etkileşimli. K5'e kadar yazılmaz.
- Alternatif B': `claude://code/new?q=…&folder=…` → Claude Desktop'ın Code sekmesi. Aynı güvenlik (önceden doldurulur). Kullanıcının tercihine göre tek satır fark (K4).

**Çalışma dizini:** yeni ayar `workdir` (Godot menü → "Proje klasörü…" `FileDialog` ile seç, `settings.cfg`e yaz, `{"type":"workdir","path":...}` olarak dinleyiciye gönder). Boşsa `%USERPROFILE%`. `--add-dir` gerekmez; `cwd`/`-p` içinde `cwd` yeterli.

**Gizlilik kuralları (kodda zorunlu):**
- Dışarı giden metin **yalnızca** uyandırma sözü + "Claude'a sor/iş ver" kalıbından **sonra gelen kısım**. `gate` tamponu (son 180 s anlatım) **asla** eklenmez. Test: `test_commands.py` → `parse("çırak claude'a sor hava nasıl")` sadece "hava nasıl" döndürür.
- Metin gönderilmeden önce balon: "Claude'a soruyorum: 'hava nasıl'" — kullanıcı yanlış duyulduğunu görür. A'da bu balonun ardından 2 s içinde çırağa tıklanırsa iptal (S, isteğe bağlı; B'de zaten terminalde görünür, iptal Esc).
- `ANTHROPIC_API_KEY`/Haiku yedeği ile karışmaz; bu özellik `claude` ikilisini kullanır, anahtar okumaz.

### Alternatifler (ve neden değil)

- **Agent SDK (Python `claude_agent_sdk`):** yeni bağımlılık, aynı `-p` çıktısı. Atla.
- **Etkileşimli PowerShell penceresi + `claude "soru"`:** `claude-cli://` bunu zaten yapıyor ve uyarı bandı/önceden doldurma güvenliği hazır. Atla.
- **Codex şimdi:** kurulu değil. Atla.

### Değişen dosyalar

- Yeni `listener/assistants.py`: `ask_claude(text, workdir) -> str | None`, `open_claude_task(text, workdir)`; `which` ile bulma; `codex` için ileride aynı dosyada.
- `listener/commands.py` kalıplar: TR `claude'a sor (.+)`, `claude'a (iş ver|yaptır|söyle) (.+)`; EN `ask claude (.+)`, `tell claude (to )?(.+)`.
- `listener/listener_core.py`: `workdir` alanı, `on_client` `"workdir"` dalı.
- `app/main.gd`: menü öğesi "Proje klasörü…" + `FileDialog(FILE_MODE_OPEN_DIR)`, `settings.cfg`, bağlantıda gönderme (`link.connected` lambda'sına bir satır).

**Boyut:** A M, B S, menü S → toplam M. **Risk:** orta (gizlilik). Whisper "Claude"u "Klod/Cloud/Kolt" yazabilir → kalıpta varyantlar; `hotwords`a "Claude".

---

## 4) Başkalarının bilgisayarında çalışması (dağıtım)

### 4.1 Bulgular (ölçümler)

| Parça | Boyut | Not |
|---|---|---|
| `build/Cirak.exe` (Godot, pck gömülü) | 109 MB | Normal; sıkıştırmada ~35-40 MB |
| `listener/.venv` toplam | 401 MB | aşağıda kırılım |
| `ctranslate2.dll` | 61 MB | + `libiomp5md.dll` 1.6 MB, `cudnn64_9.dll` 0.3 MB (yalnızca saplama) |
| `av.libs` (FFmpeg DLL'leri) | 63 MB | faster-whisper dosya okumak için ister; **biz numpy veriyoruz, hiç kullanılmıyor**; ama `faster_whisper` modül seviyesinde `import av` yapar |
| `sympy` | 55 MB | onnxruntime bağımlılığı (Silero VAD, `vad_filter=True` kullanıyoruz) |
| `onnxruntime` | 41 MB | Silero VAD |
| `numpy` + `numpy.libs` | 52 MB | |
| `anthropic` (+pydantic, httpx…) | ~40 MB | yalnızca Haiku yedeği |
| `pip`, `setuptools`, `pytest`, `_pytest` | ~25 MB | dağıtımda gereksiz |
| Whisper `small` (HF cache) | 464 MB | `~/.cache/huggingface/hub/models--Systran--faster-whisper-small` |
| Ollama + `qwen2.5:3b` | ayrı kurulum, 1.9 GB | isteğe bağlı |

Kaba dağıtım hesabı: exe 109 + dinleyici ~330 (anthropic/pip/pytest çıkmış) ≈ 440 MB açık, **~160-190 MB zip**; model ilk çalıştırmada +464 MB.

**Python 3.10.11 ömrünü 2026-10-01'de doldurdu** ("no longer supported and does not receive security updates") [PY310]. Gömülebilir paket hâlâ iniyor (8.2 MB) ama yeni makineye EOL yorumlayıcı dağıtmak yanlış başlangıç. **Python 3.12.10** son tam-bakım 3.12, gömülebilir zip 10.6 MB [PY312]; ctranslate2 4.9.0'ın cp310-cp315 win_amd64 tekerlekleri var (~20 MB) [CT2]. Diğer bağımlılıklar (onnxruntime 1.23, numpy 2.2, av 17, websockets 16) 3.12'yi destekler. 3.12'ye geçiş = `python -m venv` + `pip install -r requirements.txt` + `pip freeze > requirements.lock`; kodda değişiklik beklenmiyor (test paketi çalıştırılır). **Karar K1.**

### 4.2 Python'u paketlemek

| Seçenek | Artı | Eksi | Karar |
|---|---|---|---|
| **A. Gömülebilir Python + `pip install --target lib` (önerilen)** | Resmî yol: "intended for acting as part of another application"; `._pth` dosyasıyla arama yolu kontrolü; pip yok ama paketleri **kurulum sırasında** biz koyarız [PYEMB]. DLL yükleme sorunu yok: ctranslate2 normal site-packages düzeninde kalır. Hata ayıklama = normal Python. | Zip içinde .py dosyaları açık (sorun değil: proje açık) | **Bu** |
| B. PyInstaller (onedir) | Tek klasör | faster-whisper/ctranslate2 ile bilinen tuzaklar: CUDA saplama DLL'leri import'ta zorla yükleniyor ve CUDA'sız makinede çöküyor, eski `MSVCP140.dll` çakışması, gizli import'lar (`--collect-all faster_whisper ctranslate2`), `av` dışlanınca başlatma kırılıyor; çözüm `os.add_dll_directory` hileleri [PYI-FW]. Boyut kazancı yok (aynı DLL'ler). Lisans sorun değil ("shipped with whatever license you want") [PYI-LIC]. | Atla |
| C. Nuitka | Derlenmiş | Aynı DLL sorunları + 20-40 dk derleme, hata ayıklama zor | Atla |

**A'nın adımları** (`tools/build.ps1`, bölüm 4.11): zip'i aç → `dist/Cirak/listener/python/`; `python312._pth` içine `..\lib` satırı ekle (`import site` **ekleme**, kullanıcı makinesindeki Python paketleri karışmasın); geliştirme makinesindeki **aynı minör** Python ile `pip install --target dist/Cirak/listener/lib -r requirements.dist.txt --only-binary :all:`; `pythonw.exe` zip'in içinde var.

**`link.gd:_launch` değişikliği (tek satır):** `listener.path_join(".venv/Scripts/pythonw.exe")` → önce `listener/python/pythonw.exe` (dağıtım), yoksa `.venv/Scripts/pythonw.exe` (geliştirme). `mic_guard.own_exes()` `sys.executable`/`_base_executable` okur; gömülebilir Python'da ikisi de aynı `pythonw.exe` → mikrofon kayıt anahtarı yine eşleşir.

**Dağıtımdan çıkarılacaklar:** `pytest`, `pip`, `setuptools`, `anthropic` (Haiku yedeği: `asker._haiku` içinde import zaten tembel; `requirements.dist.txt`'e koymazsan `ask()` 124. satırda `ANTHROPIC_API_KEY` varsa bile `_haiku` None döner → liste; istenen davranış). **`av` çıkarılamaz** (`faster_whisper/audio.py` modül düzeyinde import eder) → 63 MB kalır; lisans notu 4.10.

### 4.3 Whisper modeli ilk çalıştırmada

- Bugün: `WhisperModel("small", …)` HF cache'e indirir (`hearing.py:106`). Dağıtımda **`download_root=%LOCALAPPDATA%\Cirak\models`** ver (faster-whisper: "Directory where the models should be saved. If not set, the models are saved in the standard Hugging Face cache directory") [FW]. Böylece model kullanıcı profilinde, kurulum klasörü salt-okunur kalabilir, kaldırmada silinecek yer belli.
- İlk çalıştırma akışı: dinleyici `{"type":"status","text":"İlk kurulum: konuşma modeli iniyor (~460 MB)"}` gönderir → aynı `say` balonu; indirme bitince "Hazırım". `huggingface_hub` ilerleme çubuğu pythonw'da görünmez; yüzde göstermeye uğraşma (YAGNI). İnternet yoksa: "Model inemedi; yazarak devam edebilirsin" + 60 s'de bir yeniden dene (Ollama ısıtmasındaki `warm["at"] % 60` kalıbı).
- Modeli kuruluma gömmek: kurulum dosyası ~600 MB olur; ilk açılışta internet olmadan çalışır. Arkadaşlara dağıtım için gereksiz; **indir**. (K6: Türkçe için `medium` kararı burada da geçerli: 1.5 GB.)

### 4.4 Ollama isteğe bağlı

- Bugün zaten: Ollama yok → `ask_local` None → liste (`asker.py:93, 126`). Isıtma 60 s'de bir deneniyor (`main.py:117`). Çökmez.
- Eksik olan **görünürlük**: menüde devre dışı satır "Sorular: yerleşik liste (Ollama yok)" — `paused` satırıyla aynı kalıp (`main.gd:_set_paused`): dinleyici `{"type":"brain","local":false}` gönderir, `warm["ok"]` değişince bir kez. S.
- Kurulum notu (README/kurulum sonrası sayfa): "Daha iyi sorular için Ollama kur ve `ollama pull <model>`". **Model lisansı:** `qwen2.5:3b` HF kartında **"qwen-research"** (araştırma lisansı) [QWEN]; 7B Apache-2.0'dır ama 5 GB. Modeli biz dağıtmıyoruz, kullanıcı çekiyor → lisans kullanıcıya ait; ancak varsayılan öneriyi Apache-2.0 bir modele çevirmek daha temiz (K7; Qwen3 4B Apache-2.0 olarak biliniyor, Türkçesi denenmeli).
- Kodda `LOCAL_MODEL` zaten `CIRAK_MODEL` ortam değişkeninden okunuyor (`asker.py:13`); `apps.json` gibi bir `settings.json`a taşımak S.

### 4.5 CUDA / CPU yedeği

- Var ve doğru: `hearing.py:transcribe` GPU yüklemesi ya ilk kullanımı başarısızsa CPU int8'e kalıcı geçer. venv'de **hiç** `nvidia-*` pip paketi yok → bu PC'de GPU, sistemde kurulu CUDA 12 + cuDNN 9 sayesinde çalışıyor. Başkasının PC'sinde büyük olasılıkla CPU: `small` int8 ile ~2 s / 8 s konuşma (README'deki ölçüm). Kabul edilebilir; **nvidia tekerleklerini paketleme** (1 GB+). README'de "GPU isteğe bağlı: CUDA 12 + cuDNN 9 kuruluysa kullanılır" bir satır.
- Dağıtımda `compute_type="int8"` CPU'da zaten; `cpu_threads` varsayılan 0 (= otomatik). Değişiklik yok.

### 4.6 Sabit yollar ve ayarların yeri

**Grep sonucu (`D:\`, `C:\Users`, mutlak yollar):** kodda (**.py/.gd**) **hiç yok**. Yalnızca `docs/plans/…companion.md` (Godot exe yolu, geliştirme notu) ve `tests/test_mic_guard.py` (sahte `C:#Users#x#Discord.exe` anahtarları, olması gereken). Temiz.

**Ama iki yazma yeri yanlış:**
- `listener/main.py:12` `listener.log`u `main.py`nin yanına yazar → Program Files'a kurulursa açılamaz, `open()` istisna fırlatır ve **dinleyici başlamaz** (pythonw'da stderr None olduğu için hata da görünmez). Düzeltme: `%LOCALAPPDATA%\Cirak\listener.log` (`os.environ["LOCALAPPDATA"]`, klasörü `mkdir(exist_ok=True)`). S, **dağıtım için zorunlu**.
- Whisper modeli → 4.3 (`download_root`).

**Godot ayarları:** `user://settings.cfg` = `%APPDATA%\Godot\app_userdata\Cirak\settings.cfg` (doğrulandı; yanında `logs/`, `shader_cache/`). Çalışıyor, dokunulmayabilir. "Tek klasör" istenirse `project.godot`: `application/config/use_custom_user_dir=true` + `application/config/custom_user_dir_name="Cirak"` → `%APPDATA%\Cirak\`. Dinleyici `%LOCALAPPDATA%\Cirak\` kullanır (log, model, apps.json); iki klasör olması sorun değil (Godot Roaming, dinleyici Local; model 460 MB'ın Roaming profiline girmemesi zaten doğru). K8.

**Kurulum yeri:** per-user (`%LOCALAPPDATA%\Programs\Cirak`) → UAC yok, yazma hakkı var, SmartScreen'de "yönetici izni istemeyen" bir kurulum. Inno: `PrivilegesRequired=lowest`, `DefaultDirName={localappdata}\Programs\Cirak`.

### 4.7 Kurulum paketi, imza, SmartScreen

- **Zip (ilk adım, S):** `Cirak-0.x-win64.zip` → aç, `Cirak.exe` çalıştır. Arkadaş testi için yeter.
- **Inno Setup (M):** ücretsiz, non-admin kurulumları destekler ("extensive support for both administrative and non administrative installations") [INNO]; `setup.iss` ~40 satır: dosyalar, Start Menu kısayolu, "Windows açılışında başlat" görevi (`{userstartup}` kısayolu), kaldırmada `%LOCALAPPDATA%\Cirak` sorusu. `iscc` bu PC'de **yok** (kurulum kararı K9).
- **İmza / SmartScreen:** imzasız exe → "Windows PC'nizi korudu" uyarısı (Ek bilgi → Yine de çalıştır). İmza bile anında güven vermiyor: Microsoft, Azure Artifact Signing için "does not provide instant SmartScreen trust", EV için "same as OV for new files"; fiyat ~9,99 $/ay ve **bireyler için yalnızca ABD/Kanada**; OV sertifika yıllık yüzlerce dolar [SMART]. Windows 11 Smart App Control imzasızı tamamen engelleyebilir. **Öneri:** arkadaş dağıtımı için imzalama **yapma**; README'ye uyarı ekran görüntüsü + "Yine de çalıştır" notu. Steam/itch tarzı geniş dağıtım gündeme gelirse yeniden bak.

### 4.8 Otomatik başlatma

- Bu PC'de örnek var: `shell:startup` içinde `Ollama.lnk`; HKCU `Run` anahtarında Discord, Steam vb.
- En az kod: Inno kurulum görevi (onay kutusu) → `{userstartup}\Cirak.lnk`. Zip dağıtımında: README "kısayolu `shell:startup`a kopyala".
- Menüden anahtar istenirse: dinleyici `winreg` ile `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\Cirak = "<exe yolu>"` yazar/siler (`mic_guard` zaten winreg kullanıyor); Godot `{"type":"autostart","on":true}` gönderir, exe yolunu `OS.get_executable_path()`tan ekler. S-M. Önce Inno görevi; menü anahtarı istenirse sonra (K10, önceki plan 6.7 ile aynı).
- Ollama otomatik başlıyorsa yarış: `warm_model` 60 s'de bir zaten tekrar deniyor (önceki plan 4.2 yapıldı). İyi.

### 4.9 İlk çalıştırmada mikrofon seçimi

- Mikrofon alt menüsü var (`main.gd:MIC_ID`, `mics` listesi dinleyiciden geliyor). Varsayılan = Windows varsayılanı çoğu kişide doğru.
- Minimal: `settings.cfg`de `first_run` yoksa (ya da `mic_device` hiç kaydedilmemiş ve `mics.size() > 1`) ilk `mics` mesajında bir kez balon: "Birden fazla mikrofon var. Sağ tık → Mikrofon'dan seç" + menüyü otomatik aç (`menu.popup(...)`). `_save()` ile `first_run=false`. S. Tam bir "sihirbaz" **yapma**.
- Ses ölçer (`python hearing.py`) geliştirici aracı; kullanıcıya gerekmez.

### 4.10 Lisanslar

Kurulu paketlerin `dist-info/METADATA` alanlarından (bu venv) ve model kartlarından:

| Bileşen | Lisans | Dağıtımda |
|---|---|---|
| Godot 4 | MIT | exe'ye gömülü; `LICENSES.txt`e Godot + üçüncü taraf bildirimi ekle (Godot'un `--license`/engine third-party listesi) |
| faster-whisper 1.2.1 | MIT | lib/ |
| CTranslate2 4.9.0 | MIT | lib/ (61 MB DLL) |
| onnxruntime 1.23.2 | MIT | lib/ |
| Silero VAD (faster-whisper içinde) | MIT | lib/ |
| numpy, websockets, psutil, sympy, pyreadline3 | BSD-3 | lib/ |
| sounddevice (PortAudio) | MIT | lib/ |
| pycaw, comtypes, coloredlogs, humanfriendly | MIT | lib/ |
| huggingface_hub, tokenizers, hf_xet | Apache-2.0 | lib/ (NOTICE dosyası varsa taşı) |
| **PyAV 17 (`av`)** | BSD-3 **ama** tekerleğe gömülü FFmpeg DLL'leri `libx264`, `libx265` içeriyor (`av.libs/` listesinde görüldü; pyav-ffmpeg README x264/x265'i "enabled for all platforms" diyor [PYAV]) → bu bileşenler **GPL**; FFmpeg'in GPL derlemesi dağıtılıyor demek | Proje açık kaynak (MIT/GPL-uyumlu) kalırsa sorun yok; kapalı dağıtım planı olursa `av`sız bir faster-whisper çatalı ya da `av`yi `audio.py`de tembel import eden yama gerekir. **Projenin lisansını seç: K11.** |
| anthropic SDK | Apache-2.0 | dağıtımdan **çıkar** (4.2) |
| Whisper `small` ağırlıkları (Systran/faster-whisper-small) | MIT [FWS] | kullanıcı indirir |
| Ollama | MIT | kullanıcı kurar |
| qwen2.5:3b | **qwen-research** [QWEN] | kullanıcı çeker; varsayılan öneriyi değiştir (K7) |
| Python 3.12 | PSF | python/ içinde `LICENSE.txt` zaten var |
| Inno Setup | ücretsiz (ticari kullanıcılardan satın alma **rica** edilir) [INNO] | kurulum aracı, dağıtılmaz |
| Grok ile üretilen çırak çizimleri | xAI kullanım koşulları (kullanıcı hesabı) | exe'de; ticari dağıtımda koşulları oku (K11) |

`tools/build.ps1` son adımı: `pip-licenses` **kurma**; `dist-info/METADATA`dan `License` satırlarını toplayan 10 satırlık Python ile `dist/Cirak/LICENSES.txt` üret.

### 4.11 Hedef klasör düzeni ve derleme adımları

```
dist/Cirak/
  Cirak.exe                  # Godot export, pck gömülü (109 MB)
  listener/
    main.py  hearing.py  listener_core.py  asker.py  gate.py  mic_guard.py
    commands.py  apps.py  media.py  assistants.py      # bölüm 0-3 eklenince
    python/                  # python-3.12.10-embed-amd64.zip açılmış hali (pythonw.exe, python312.dll, python312.zip)
      python312._pth         # içerik: python312.zip / . / ..\lib   (import site YOK)
    lib/                     # pip install --target ile kurulan paketler (~330 MB)
  README.txt                 # ilk çalıştırma: model iner (~460 MB); SmartScreen "Yine de çalıştır"; Ollama isteğe bağlı; mikrofon seçimi
  LICENSES.txt

%LOCALAPPDATA%\Cirak\        # çalışma zamanı (dinleyici)
  listener.log  models\  apps.json  last_answer.txt
%APPDATA%\Godot\app_userdata\Cirak\settings.cfg   # Godot ayarları (K8'e göre %APPDATA%\Cirak olabilir)
```

`tools/build.ps1` (ya da `.sh`; Godot ve pip çağrıları aynı):

1. `git status` temiz mi, sürüm etiketi (`project.godot` `config/version`).
2. **Godot export:** `Godot --headless --path app --export-release "Windows Desktop" ../dist/Cirak/Cirak.exe` (mevcut komut, hedef `dist/`). Godot yolunu betiğe **yazma**: `$env:GODOT` ya da parametre.
3. **Gömülebilir Python:** `python-3.12.10-embed-amd64.zip` (10,6 MB) → `dist/Cirak/listener/python/`; **indirme kullanıcının onayıyla**, SHA256'yı python.org'dan al ve betikte kontrol et. `python312._pth`e `..\lib` ekle.
4. **Paketler:** `py -3.12 -m pip install --target dist/Cirak/listener/lib -r listener/requirements.dist.txt --only-binary :all: --no-compile`; `requirements.dist.txt` = `requirements.lock` eksi `anthropic`, `pytest`, `pip`, `setuptools` ve bunların yalnız-onlara-ait bağımlılıkları (pydantic*, httpx*, anyio, jiter, distro, sniffio, iniconfig, pluggy, tomli, exceptiongroup, docstring_parser, annotated-types, typing-inspection). `lib/bin/` klasörünü sil (konsol betikleri).
5. **Kaynak:** `listener/*.py` kopyala (`tests/`, `__pycache__`, `.venv` hariç). `README.txt`, `LICENSES.txt` üret.
6. **Duman testi (zorunlu):** `dist/Cirak/listener/python/pythonw.exe dist/Cirak/listener/main.py` çalıştır → `%LOCALAPPDATA%\Cirak\listener.log`te hata yok, `127.0.0.1:47613` açık; sonra `dist/Cirak/Cirak.exe` → bağlanıyor, `mics` listesi geliyor, yazı kutusundan soru geliyor. Dinleyiciyi **`bye` ile** kapat (uygulama kapanınca kendi gönderiyor); asla `taskkill /F` değil.
7. **Paket:** `Compress-Archive dist/Cirak → dist/Cirak-<sürüm>-win64.zip` (ilk sürümler). Inno kararı sonrası `iscc tools/setup.iss` → `dist/Cirak-<sürüm>-Setup.exe`.
8. Temiz bir Windows'ta (ikinci PC ya da sanal makine) **tek gerçek test**: CUDA'sız, Ollama'sız, mikrofonlu. Beklenen: model iner, CPU'da çalışır, sorular listeden, mikrofon menüsü dolu.

**Kodda değişen yerler (dağıtım için gereken asgari):** `app/link.gd:_launch` (python yolu, 1 satır), `listener/main.py:12` (log yolu), `listener/hearing.py:_load` (`download_root`), `listener/main.py` (ilk kurulum/`brain` durum mesajları, ~10 satır), `app/apprentice.gd:handle` (`say`/`status` dalı), `app/main.gd` (ilk çalıştırma mikrofon ipucu, ~6 satır), yeni `tools/build.ps1`, `listener/requirements.dist.txt`, isteğe bağlı `tools/setup.iss`.

**Boyut:** L (çoğu betik + test; kod küçük). **Risk:** orta: `--target` kurulumunda bazı paketlerin `.pth`/`.libs` düzeni (`numpy.libs`, `av.libs`) `lib/` içinde yan yana durur; `delvewheel` bu düzeni `__init__`te `os.add_dll_directory` ile çözer, çalışır; duman testi (adım 6) bunu doğrular.

---

## Önerilen iş sırası

1. **K1: venv'i Python 3.12'ye taşı** (S). EOL 3.10'dan kurtul; dağıtım ve GSMTC yolunu açar. Testleri çalıştır, `requirements.lock` yenile.
2. **Dağıtım için zorunlu küçükler** (S): log yolu `%LOCALAPPDATA%\Cirak`, `download_root`, `link.gd` python yolu. Bunlar bugünkü geliştirme kurulumunu bozmaz.
3. **Komut yolu altyapısı** (M): `commands.py` + `listener_core.speech_end` kancası + `say` balonu + testler. Tek komutla başla: "Çırak, duraklat" (medya tuşu, 5 satır) → tüm zincir canlı görülür.
4. **Medya Aşama 1 + uygulama açma** (S + M): `media.py`, `apps.py`, kalıplar, `hotwords`. Kulaklık anahtarı (önceki plan 6.1) burada gerekir.
5. **Claude'a sor / iş ver** (M): `assistants.py`, `workdir` menüsü, gizlilik testleri.
6. **`tools/build.ps1` + zip + temiz makine testi** (L). Inno/otomatik başlatma/mikrofon ipucu bu adımda.
7. Sonra, istenirse: medya Aşama 2 (GSMTC), hoparlörde komut modu, Codex, menüden autostart.

Atlananlar (YAGNI): ayrı uyandırma-sözü modeli, LLM niyet sınıflandırması, Spotify Web API, PyInstaller/Nuitka, kod imzası, kurulum sihirbazı, Agent SDK.

---

## Kullanıcının karar vermesi gerekenler

- **K1. Python 3.12'ye geçiş:** venv yeniden kurulur (10 dk, ~400 MB indirme). 3.10 EOL. Önerim: evet, ilk adım.
- **K2. Hoparlörde komut:** (a) yalnızca kulaklık anahtarıyla (basit, önerim), (b) "müzik çalarken de komut dinle" ayarı (Whisper müzik parçalarını çevirir, CPU'da ısı), (c) komutlar yalnızca sessizde.
- **K3. Uygulama açma izin listesi:** AppsFolder'daki her şey mi (varsayılan), yoksa yalnızca `apps.json`dakiler mi? Yasak listesi (cmd/PowerShell/regedit) istensin mi?
- **K4. Claude "iş ver" penceresi:** `claude-cli://` (PowerShell penceresi; Windows Terminal kurulu değil) mi, `claude://code/new` (Claude Desktop Code sekmesi) mi?
- **K5. Codex:** kurulmasın (şimdilik, önerim) / kurulsun ve `codex exec --sandbox read-only` ile "sor" eklensin.
- **K6. Whisper modeli dağıtımda:** `small` (460 MB, EN iyi, TR orta) / `medium` (1.5 GB, TR belirgin iyi, CPU'da 3-4× yavaş). Önceki planın 6.6'sı.
- **K7. Varsayılan Ollama modeli:** `qwen2.5:3b` (qwen-research lisansı, kullanıcı çeker) kalsın mı, Apache-2.0 bir modele (örn. Qwen3 4B; Türkçesi denenmeli) geçilsin mi?
- **K8. Godot ayar klasörü:** `%APPDATA%\Godot\app_userdata\Cirak` kalsın (dokunmak yok) / `%APPDATA%\Cirak` (iki satır).
- **K9. Paket biçimi:** zip (önerim, ilk) / Inno Setup kurulumu (iscc indirilecek, ~5 MB). İmza: yok (önerim).
- **K10. Otomatik başlatma:** kurulum görevi onay kutusu (önerim) / menüde anahtar / hiçbiri.
- **K11. Proje lisansı:** dağıtılacaksa bir lisans gerekir. PyAV tekerleğindeki GPL FFmpeg bileşenleri ve Grok çizimlerinin koşulları yüzünden açık kaynak (MIT kod + "üçüncü taraf bildirimi") en az sürtünmeli yol. Kapalı/ticari istenirse `av` meselesi ayrıca çözülür.
- **K12. Claude'a gönderimde iptal penceresi:** balon göründükten sonra 2 s tıkla-iptal olsun mu (A yolu), yoksa doğrudan gitsin mi?

---

## Kaynaklar

- [MS-GSMTC-M] GlobalSystemMediaTransportControlsSessionManager — https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionmanager (Win10 1809+, RequestAsync/GetCurrentSession/GetSessions)
- [MS-GSMTC-S] GlobalSystemMediaTransportControlsSession — https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession (SourceAppUserModelId, Try*Async; volume yok)
- [PYPI-WRT] winrt-Windows.Media.Control — https://pypi.org/project/winrt-Windows.Media.Control/ (Python ≥3.11, modül `winrt.windows.media.control`)
- [PYWINRT] pywinrt README — https://github.com/pywinrt/pywinrt (winrt-runtime + ad alanı başına paket, asyncio ile await)
- [PYPI-WINSDK] winsdk — https://pypi.org/project/winsdk/ (1.0.0b10, Ağu 2023, Python ≥3.8, MIT, beta)
- [MS-VK] Virtual-Key Codes — https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
- [SPOT] Spotify Skip To Next — https://developer.spotify.com/documentation/web-api/reference/skip-users-playback-to-next-track (Premium, `user-modify-playback-state`)
- [CC-CLI] Claude Code CLI reference — https://code.claude.com/docs/en/cli-reference (`-p`, `--output-format`, `--tools`, `--permission-mode`, `--permission-prompts`, `--bare`, `--max-turns`, `--no-session-persistence`)
- [CC-DL] Claude Code deep links — https://code.claude.com/docs/en/deep-links (`claude-cli://open?cwd=&q=`, 5.000 karakter, gönderilmez, Windows terminal sırası)
- [CL-DESK] Open Claude Desktop with a link — https://support.claude.com/en/articles/14729294-open-claude-desktop-with-a-link (`claude://claude.ai/new?q=`, `claude://code/new?q=&folder=`, ~14.000 karakter)
- [CODEX] Codex CLI reference — https://developers.openai.com/codex/cli/reference → https://learn.chatgpt.com/docs/developer-commands?surface=cli (`codex exec`, `--sandbox`, `-C`, `-o`, `--json`)
- [FW] faster-whisper transcribe.py — https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py (`download_root`, `local_files_only`, `initial_prompt`, `hotwords`)
- [FWS] Systran/faster-whisper-small — https://huggingface.co/Systran/faster-whisper-small (MIT)
- [QWEN] Qwen/Qwen2.5-3B-Instruct — https://huggingface.co/Qwen/Qwen2.5-3B-Instruct (lisans etiketi `qwen-research`)
- [PYAV] pyav-ffmpeg — https://github.com/PyAV-Org/pyav-ffmpeg (x264, x265 "enabled for all platforms")
- [PY310] Python 3.10.11 — https://www.python.org/downloads/release/python-31011/ (EOL 2026-10-01; embed zip 8,2 MB)
- [PY312] Python 3.12.10 — https://www.python.org/downloads/release/python-31210/ ("last full maintenance release"; embed zip 10,6 MB)
- [PYEMB] Using Python on Windows, embeddable package — https://docs.python.org/3/using/windows.html ("intended for acting as part of another application"; pip yok; `._pth`)
- [CT2] ctranslate2 4.9.0 files — https://pypi.org/project/ctranslate2/4.9.0/#files (cp39–cp315 win_amd64, ~20 MB)
- [PYI-LIC] PyInstaller license — https://pyinstaller.org/en/stable/license.html
- [PYI-FW] faster-whisper + PyInstaller tuzakları (Qiita, topluluk raporu; tek yazar) — https://qiita.com/KLjp/items/1cd9260ed0e754f3dcc3
- [INNO] Inno Setup — https://jrsoftware.org/isinfo.php
- [SMART] Microsoft code signing options / SmartScreen reputation — https://learn.microsoft.com/windows/apps/package-and-deploy/code-signing-options ; https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation

---

## Kararlar (2026-11-15, kullanıcı)

- **K1:** evet, Python 3.12'ye geçilir.
- **K2:** müzik çalarken komut **bas-konuş** ile verilir (bir tuş basılıyken söylenen her şey komut sayılır; uyandırma sözü gerekmez, hoparlör kapısı aşılır). Sessizken "Çırak, …" ile de olur.
- **K3:** açılabilecek uygulamaları **kullanıcı listeler** (`apps.json` yalnızca izin listesi; listede olmayan hiçbir şey açılmaz).
- **K11:** proje açık kaynak olacak.
- Kalan kararlar (K4-K10, K12) için şimdilik öneriler varsayıldı: K4 `claude-cli://`, K5 Codex yok, K12 iptal penceresi yok (balon ne gönderildiğini gösterir).
