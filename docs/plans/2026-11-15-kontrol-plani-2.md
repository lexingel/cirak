# Çırak: kontrol planı 2 (sesli komutlar, dağıtım, çırak görünümleri)

Tarih: 2026-11-15 · Kapsam: `git log 92dfc13..HEAD` (5f3e091 komutlar, 37a13ba dağıtım, 5285cb0 görünümler) · Kod okundu, `dist/Cirak` incelendi, testler çalıştırıldı (dinleyici 74/74, Godot 0 hata). **Kod değiştirilmedi, Cirak.exe çalıştırılmadı.**

Boyutlar: **S** birkaç satır · **M** 20-60 satır + test · **L** birden fazla dosya ya da yeni süreç.

## Kısa özet

Komut yolu, bas-konuş, uygulama listesi ve Claude köprüsü planın kararlarına (3.12, bas-konuş, yalnızca `apps.json`, açık kaynak) uygun kurulmuş; gizlilik sınırı kodda doğru: PC'den çıkan tek metin "Claude'a sor" sonrası kısım. Ama üç şey dağıtımı bu hâliyle bozar ya da kullanıcıyı sessiz bırakır:

1. **Temiz bir PC'de dinleyici hiç duymaz:** `ctranslate2.dll` ve `onnxruntime.dll` `MSVCP140.dll` ister, zip'te yok (gömülü Python yalnızca `vcruntime140` taşır). Hata da görünmez.
2. **Yazıya çevirme başarısız olunca çırak "dinliyor" pozunda takılı kalır** ve hiçbir şey söylemez (model inmedi, internet yok, DLL yok: hepsi aynı yere düşer).
3. **Sağ Ctrl her kısayolda kayıt başlatır** (Sağ Ctrl+C, oyunda çömelme, VirtualBox), 15 sn'den uzun basılı kalınca sonsuza dek 15 sn'lik parçalar çevirir.

Gerisi küçük: uyandırma sözü düzeltmesi, İngilizce "I" sorunu, uygulama adı yazımı, Claude hatalarının loga düşmesi, görünüm için yedek, plandan kalan parçalar (ilk çalıştırma balonları, "Ollama yok" satırı, proje klasörü).

---

## Yüksek

### Y1. Temiz PC'de `MSVCP140.dll` yok → Whisper/VAD yüklenmez
- **Nerede:** `tools/build.py:72-85` (`embed_python`), `dist/Cirak/listener/python/` (yalnızca `vcruntime140.dll`, `vcruntime140_1.dll` var).
- **Kanıt:** `ctranslate2.dll` içe aktarımları: `MSVCP140.dll, VCRUNTIME140.dll, VCRUNTIME140_1.dll, cublas64_12.dll`; `onnxruntime.dll`: `MSVCP140.dll, MSVCP140_1.dll, …`. numpy kendi `numpy.libs/msvcp140-<hash>.dll`sini taşır ama adı karıştırılmış, ctranslate2'ye yaramaz. Bu PC'de VC++ runtime kurulu olduğu için duman testi geçti; Visual C++ 2015-2022 kurulmamış bir PC'de `from faster_whisper import WhisperModel` patlar. `hearing.py:134` tembel içe aktardığı için dinleyici açılır, bağlanır, mikrofon listesi gelir, ama her sözde `transcribe` istisna atar (→ Y2).
- **Düzeltme (S):** `build.py`de `C:\Windows\System32\{msvcp140.dll, msvcp140_1.dll, msvcp140_2.dll}` dosyalarını `dist/Cirak/listener/python/` içine kopyala (exe'nin klasörü DLL aramasında ilk sırada; Microsoft bu dosyaların uygulamayla dağıtımına izin verir). `LICENSES.txt`e bir satır. Yedek: README'ye "VC++ Redistributable kur" (daha kötü: kurulum adımı).
- **Doğrulama:** Windows Sandbox (Win10 Pro'da var, her açılışta temiz Windows, mikrofon aktarımı destekler) içinde zip'i aç → çalıştır. Planın 4.11/8 adımı ("temiz makinede tek gerçek test") hâlâ yapılmadı; bu, dağıtmadan önceki tek zorunlu test. Sandbox'ı açmak Windows özelliği (kullanıcı yapar).

### Y2. Yazıya çevirme hatası çırağı "dinliyor" pozunda bırakır, kullanıcı hiçbir şey görmez
- **Nerede:** `listener_core.py:53` (`text = self.transcribe(audio, self.lang)`) ve `:67` (`ptt_end`). İstisna worker'da yakalanıp loga yazılır (`main.py:111`), ama `speech_end` mesajı hiç gitmez → `apprentice.gd:81-86` LISTENING'de kalır. Model inememiş (internet yok), DLL yok (Y1), CUDA sonrası CPU da çökmüş: hepsi aynı belirti, hepsi sessiz.
- **Düzeltme (S):** `speech_end`/`ptt_end`de `transcribe`yi `try/except` içine al: hata olursa `speech_end` gönder ve **bir kez** `say` ile "Konuşma modeli yüklenemedi; yazarak devam edebilirsin (listener.log)". Sonraki hatalarda yalnızca `speech_end`. Test: `test_listener.py`de `transcribe` istisna atan bir vaka.
- İlk çalıştırma balonlarıyla (E1) birlikte yapılmalı; ikisi aynı `say` kanalını kullanır.

### Y3. Bas-konuş tuşu (Sağ Ctrl) çakışır ve takılır
- **Nerede:** `main.py:31` (`PTT_KEY = 0xA3`), `main.py:47-49` (`GetAsyncKeyState`), `hearing.py:118-127` (`PushToTalk.feed`).
- **Sorunlar:**
  - (a) Sağ Ctrl+C/V, oyunlarda Ctrl=çömel, VirtualBox'ın varsayılan host tuşu: her basış bir kayıt, her bırakış bir Whisper çevirisi (GPU/CPU işi) ve "Anlamadım" balonu. Kayıtta müzik/şarkı sözü varsa `dur|stop|back|play` gibi kelimeler **gerçek bir medya tuşuna** dönüşebilir (`commands.py:23-26` komut metninin herhangi bir yerinde arar).
  - (b) 15 sn üstü basılı tuş: `feed` parçayı gönderir, `_chunks` boşalır, bir sonraki blokta tuş hâlâ basılı → yeni kayıt başlar. Takılı tuş ya da uzun oyun turu = her 15 sn bir çeviri, sonsuza dek.
  - (c) `GetAsyncKeyState` yönetici (yükseltilmiş) bir pencere öndeyken 0 döner → bas-konuş o anda sessizce çalışmaz.
  - (d) Ses geri çağrısında (PortAudio iş parçacığı) 30 ms'de bir `GetAsyncKeyState`: iş parçacığı açısından sorun yok (mesaj döngüsü gerekmez, ucuz). Ama "her 30 ms tuş okuyan, mikrofon açan, imzasız exe'den doğan pythonw" bazı antivirüs sezgilerini tetikleyebilir; dağıtım notuna bir cümle.
- **Düzeltme:**
  - (b) **S:** 15 sn kesiminden sonra tuş bırakılana kadar yeni kayıt başlatma (`PushToTalk`a `_spent` bayrağı; `held()` False olunca sıfırla). Test: `test_detector.py`.
  - (a) **S:** 0,4 sn'den kısa parçayı (tuşa dokunma, kısayol) hiç çevirme; `keep()` zaten boş döndürürse `speech_end` gidiyor. **M:** tuşu ayarlanabilir yap: Godot menüsünde "Komut tuşu" alt menüsü (Sağ Ctrl / Pause / Scroll Lock / Sağ Shift), `settings.cfg`, `{"type":"ptt_key","vk":…}` mesajı; `main.gd:31,36` ipucu metni seçilen tuşu yazar. Dinleyici tarafı 3 satır (`core.ptt_vk`, `ptt_held` onu okur).
  - (c) README'ye not; kod yok.
- **Karar K-A:** varsayılan tuş Sağ Ctrl kalsın mı? Alternatif **Pause/Break**: neredeyse hiçbir program kullanmaz, TR klavyede var, kısayol çakışması yok. (Sağ Alt olmaz: TR Q klavyede AltGr.)

---

## Orta

### O1. Duraklat/devam için hoparlör ölçeri karar veriyor, kullanıcıya rağmen
- **Nerede:** `media.py:16-25` (`plan`), `main.py:54-55` (`speaker_busy()` ile).
- Sessiz pasaj ya da kısık ses → "Çalan bir şey yok", tuş basılmaz. Spotify duraklamış ama oyun sesi var → "Zaten çalıyor", tuş basılmaz. Kullanıcı tuşu basılı tutup açıkça söylemiş.
- **Seçenekler:** (a) **S:** duraklat/devam her zaman `toggle` tuşunu basar; balon metni ölçere göre ("Duraklattım"/"Çalıyor") — kullanıcıya güven. Bedeli: hiçbir şey çalmazken "duraklat" demek Spotify'ı başlatır. (b) **M:** GSMTC Aşama 2 (`winrt-Windows.Media.Control`, 3.12'ye geçildi, artık kurulabilir): gerçek oynatma durumu, hangi uygulama, şarkı adı balonda. (c) Olduğu gibi.
- **Karar K-B.** Önerim (a) şimdi, (b) yalnızca gerçek testte "yanlış uygulamayı" sorunu çıkarsa (YAGNI).

### O2. Uyandırma sözü "çırak…" ile başlayan her kelimeyi yutuyor
- **Nerede:** `commands.py:8` `(ç|c|ch)[ıi]ra(k|ğ|g)\w*\b`.
- "Çıraklık dönemimde böyle yapardık" → komut sayılır → "Anlamadım" ve cümle anlatımdan düşer (`gate`e girmez). "Chirac" (Whisper'ın sık yazımı) ise yakalanmaz.
- **Düzeltme (S):** `(ç|c|ch)[ıi]ra(k|ğ|g|c)(ım|ın)?\b`. Test: "çıraklık…" → None, "chirac duraklat" → pause.

### O3. `norm()` her "I"yı "ı" yapıyor, dil fark etmeden
- **Nerede:** `commands.py:45`; `apps.find` `apps.py:47-55` bu metni alır.
- İngilizce kullanıcı "open IntelliJ" → arg `ıntellij` → `apps.json` anahtarı `intellij` eşleşmez → "listemde yok". Türkçe için doğru, İngilizce için yanlış.
- **Düzeltme (S):** `find`de `tries`e `s.replace("ı", "i")` ekle (1 satır) **ya da** `parse(text, ptt, lang)` ve I→ı yalnızca `tr`. İlki daha küçük. Test: `apps.find("ıntellij", {"intellij": …})`.

### O4. Whisper uygulama adlarını bozuyor; ipucu kelimeleri yalnızca bas-konuşta
- **Nerede:** `hearing.py:10` (`HOTWORDS = "Çırak, Claude"`), `main.py:101` (yalnızca `transcribe_cmd`), `main.py:96` (`speech_end` için `transcribe` ipucusuz).
- TTS testinde "Spotify'ı aç" kötü çıktı. Uyandırma-sözü yolu ("Çırak, …" sessizken) ipucu almıyor; oysa "Çırak"ın doğru yazılması tam o yolda gerekli. Uygulama adlarının ipucudan çıkarılma gerekçesi (Türkçeyi İngilizceye kaydırıyor) yerinde.
- **Düzeltme:** (a) **S:** `apps.find`e bulanık eşleme: `difflib.get_close_matches(t, aliases, n=1, cutoff=0.75)` (stdlib, 1 satır) → "spotifay" → "spotify". Tam eşleşme ve ön ek denemelerinden sonra, yalnızca tek sonuç varsa. (b) **S:** README/`apps.json`: "Whisper nasıl yazıyorsa o yazımı da anahtar yap" (`"ispotifay": "Spotify"`); `apps.edit` dosyayı zaten açıyor. (c) **S, ölçülü:** `HOTWORDS`u anlatım yolunda da ver, 10 TR cümlede soru kalitesi bozuluyor mu bak; bozuyorsa geri al.

### O5. `apps.index()` hatası `apps.json`u kalıcı boşaltır; ilk "aç" 20 sn'ye kadar bekletir
- **Nerede:** `apps.py:22-30` (`index`, PowerShell, `timeout=20`), `apps.py:33-39` (`load` boş `idx` ile `{}` yazar), `apps.py:58-63` (`launch`).
- PowerShell engelli/yavaşsa `index()` `{}` döner → tohum `{}` olarak **yazılır**; dosya artık var, tohum bir daha denenmez. `index()` ilk komutta, worker'da çalışır → o sırada çeviri kuyruğu durur. `launch`: hedef AppsFolder'da yoksa `os.startfile` OSError → `_command` yakalar → "Anlamadım" (yanıltıcı).
- **Düzeltme (S):** `load`: `idx` boşsa dosya yazma, `{}` döndür. `index()`i başlangıçta `work.put` ile ısıt (Whisper ısıtmasından sonra, `main.py:114`). `do_open`: `launch` OSError → yeni cevap anahtarı `"cant_open": "{} açılamadı"`. Bozuk JSON (`apps.py:42-43`) → bir kez "apps.json okunamadı" de. Testler: boş idx → dosya yok; bozuk JSON → mesaj.

### O6. Claude hataları hiçbir yere yazılmıyor; `--max-turns` yardımda yok
- **Nerede:** `assistants.py:35-41` (`r.stderr` atılıyor, dönüş kodu loglanmıyor), `assistants.py:18-20` (`ask_cmd`).
- "Giriş yapılmamış", bilinmeyen bayrak, zaman aşımı: hepsi "Claude'a ulaşamadım", `listener.log`ta iz yok. `claude --help` (2.1.302) `--restricted`, `--strict-mcp-config`, `--tools`, `--no-session-persistence`, `--append-system-prompt`u listeliyor; **`--max-turns` listede yok**. Canlı test geçti (bayrak gizli ya da hâlâ kabul ediliyor), ama bir sürüm sonra reddedilirse özellik sessizce ölür.
- **Düzeltme (S):** başarısızlıkta `print("claude:", r.returncode, r.stderr[:300], file=sys.stderr)`; `--max-turns 1`i kaldır (araç yokken tek tur zaten). Test: `test_assistants.py`de komut listesinde `--max-turns` yok.
- Gizlilik kontrolü (doğrulandı, değişiklik yok): PC'den çıkan metin yalnızca `ask_claude`a giden `text` (kullanıcının Claude girişiyle Anthropic'e), `claude_task` metni yerel terminale (gönderim Enter'la), ilk çalıştırmada model indirme (huggingface.co). Anlatım tamponu hiçbir yola girmiyor (`listener_core.py:54` komutsa `_narrate` çağrılmaz; `commands.py:67-68` yalnızca eşleşen kuyruk). README'ye bu üç çıkışı tek cümlede yaz.

### O7. Proje klasörü seçici yok (plan §3 "workdir")
- **Nerede:** `main.py:70-71` (`open_claude_task(text)` → ev klasörü), `assistants.py:36` (`cwd=DATA`).
- "Claude'a iş ver" her zaman `%USERPROFILE%`de açılır; kullanıcı her seferinde `cd` yapar. "Sor" için `cwd` önemsiz (araç yok).
- **Düzeltme (M):** `main.gd` menü "Proje klasörü…" → `FileDialog(FILE_MODE_OPEN_DIR)`, `settings.cfg`, bağlantıda `{"type":"workdir","path":…}`; `listener_core.on_client` `workdir` dalı; `do_task(text, …)` → `open_claude_task(text, core.workdir)`. Test: Godot `test_ui_text` + dinleyici `on_client`.
- **Karar K-C:** şimdi mi, ilk arkadaş testinden sonra mı?

### O8. İlk çalıştırma balonları yok (plan §4.3)
- **Nerede:** `main.py:114` (ısıtma sessiz), `hearing.py:133-138`.
- ~460 MB iniyor, çırak hiçbir şey demiyor; bitince "Hazırım" yok; internet yoksa (Y2 ile) hiçbir şey. README "çalışıyor, yazabilirsin" diyor, uygulama demiyor.
- **Düzeltme (S-M):** `main.py` ısıtma işi: `DATA/models/models--Systran--faster-whisper-small` yoksa önce `core.say("İlk kurulum: konuşma modeli iniyor (~460 MB), yazarak başlayabilirsin")`, ısıtma bitince `core.say("Hazırım")`; istisnada Y2'nin mesajı. Dil: `core.lang` o anda `en` (uygulama ayarı bağlantıda gelir) → mesajı bağlantıdan sonra gönder ya da iki dilde yaz. Test: ısıtma fonksiyonunu `say` sahteyle.

### O9. "Sorular: yerleşik liste (Ollama yok)" menü satırı yok (plan §4.4)
- **Nerede:** `main.py:117-120,163` (`warm["ok"]`), `main.gd:257-269` (`_set_paused` kalıbı hazır).
- **Düzeltme (S):** `warm["ok"]` değişince `send({"type":"brain","local":bool})`; `main.gd` `PAUSE_ID` gibi devre dışı bir satır ("Sorular listeden; Ollama kurulu değil"). Test: Godot `test_command_menu`ya bir satır.

### O10. Görünüm dosyası eksikse dışa aktarımda script hatası; yedek yok
- **Nerede:** `apprentice.gd:67` (`load(path).get_image()`: `load` null dönerse `get_image` null üstünde çağrılır; `if img == null` kontrolü bir satır geç), `apprentice.gd:57-76` (hiç kare yoksa `sprite.play` boş animasyon → **görünmez çırak**), `main.gd:83-85` (yalnızca ad kontrolü, klasör kontrolü yok).
- Bugün 5 klasörde 5'er PNG var ve `export_filter=all_resources`; sorun gelecekteki bir görünüm ya da yarım kopya.
- **Düzeltme (S):** `var res = load(path); if res == null: continue`; `_load_frames` sonunda `working` karesi 0 ise `skin = ""` ile büyücüyü yükle ve `push_warning`. Test: `test_skins`e `set_skin("yok")` → büyücü kareleri.

---

## Düşük

- **D1. Görünüm önizlemesi yok.** `main.gd:113-117` alt menü yalnızca ad. **S:** her satıra ilk `listening` karesinden `AtlasTexture` ikon (`skin_menu.set_item_icon(i, …)`, `set_item_icon_max_width(i, 24)`). Seçim zaten anında uygulanıyor; ikon yeter, ayrı önizleme penceresi YAGNI. **Karar K-D:** istenir mi?
- **D2. Sürüm ve exe bilgisi yok.** `app/project.godot`ta `config/version` yok → zip hep `Cirak-0.1-win64.zip` (`build.py:59-61`); `export_presets.cfg:14` `modify_resources=false`, ikon yok → SmartScreen penceresinde "Bilinmeyen yayımcı, Cirak.exe", Godot varsayılan ikonu. **S:** `config/version="0.1.0"`, her dağıtımda artır. İkon/sürüm bilgisi için rcedit (önceki plan 6.7, **Karar K-E**).
- **D3. `LICENSES.txt` eksikleri.** `build.py:88-101`: Godot için tek satır; MIT, telif notunun eklenmesini ister (Godot `LICENSE.txt` + `COPYRIGHT.txt`, bir kez `tools/`a kopyala, ekle). numpy satırı "Copyright (c) 2005-2024…" (License alanı çok satırlı; ilk satır alınmış) → sınıflandırıcıyı tercih et. Grok çizimleri: `LICENSE` MIT'in kodu kapsadığı, çizimlerin ayrı olduğu bir satır (**Karar K-F:** çizimlere hangi lisans?). **S.**
- **D4. Derlemede duman testi yok** (plan 4.11/6 "zorunlu"). **S:** `build.py --smoke`: `dist/Cirak/listener/python/python.exe -I -c "import faster_whisper, ctranslate2, onnxruntime, av, sounddevice, pycaw, websockets"` (mikrofon açılmaz). Y1'i bu PC'de yakalamaz (runtime burada var) → Sandbox testi yine gerekli.
- **D5. `lib/` içinde çöp.** 0 baytlık `numpy-2.2.6-cp312-cp312-win_amd64.whl`, `isympy.py`, `readline.py`, `share/`. Zararsız; `build.py:137`de `*.whl` sil. **S.**
- **D6. "Sessizden çık" komutu yok.** `media.py:37-44`: `mute` yalnızca kapatır; geri açmak için "sesi aç" (aynı zamanda +%10). **S:** `unmute|sesi geri aç` → `SetMute(0)`.
- **D7. Bas-konuş ipucu metni sabit** (`main.gd:31,36` "Sağ Ctrl"). Y3 tuşu ayarlanabilir yapınca metin ayardan gelsin.
- **D8. İkinci dinleyici 10048 ile çöküyor** (eski `listener/listener.log`: port dolu). Zararsız (ilk dinleyici çalışır), ama tek satır "zaten çalışıyor" + çıkış daha temiz. Önceki commit'lerden; **S**, isteğe bağlı.
- **D9. `apps.json` değerine yazılan tam yol** (`apps.py:59-60`) `os.startfile` ile açılır: `.bat`/`.lnk` de çalışır. Kullanıcının kendi dosyası; kabul edilen sınır, README'de bir cümle ("uygulama adı ya da exe yolu yaz").
- **D10. Test sayısı:** dinleyici 74 test (not 77 diyordu).

## Plana göre durum (2026-11-15 yeni özellikler planı)

| Plan | Durum |
|---|---|
| 0 komut yolu, `say` balonu, yazarak komut | Yapıldı |
| 0.2 hoparlörde komut | Bas-konuş ile çözüldü (K2); kulaklık anahtarı gereksiz |
| 1 uygulama açma, yalnızca `apps.json` (K3) | Yapıldı; O3/O4/O5 pürüzleri |
| 2 medya Aşama 1 | Yapıldı; O1 karar. Aşama 2 GSMTC **açık** (K-B) |
| 3 Claude sor / iş ver | Yapıldı; **proje klasörü yok** (O7); iptal penceresi yok (K12 varsayım) |
| 4.1 Python 3.12 | Yapıldı (venv 3.12.10, `build.py:109` kontrol) |
| 4.2 gömülü Python + `lib/` | Yapıldı; **MSVCP140 eksik** (Y1) |
| 4.3 `download_root`, ilk çalıştırma balonları | Yol yapıldı; **balonlar yok** (O8) |
| 4.4 "Ollama yok" satırı | **Yok** (O9) |
| 4.6 log yolu `%LOCALAPPDATA%\Cirak` | Yapıldı |
| 4.7 zip / Inno | Zip yapıldı; Inno **yok** (K9) |
| 4.8 otomatik başlatma | **Yok** (K10) |
| 4.9 ilk çalıştırma mikrofon ipucu | **Yok** (S, `main.gd` `mics` mesajında bir kez) |
| 4.10 lisanslar | MIT + `LICENSES.txt` yapıldı; D3 eksikleri |
| 4.11/6 duman testi, /8 temiz makine | **Yapılmadı** (D4, Y1) |
| Codex (K5) | Yok, karar gereği |

## Önerilen sıra

1. **Y1 + D4 + Sandbox testi** — dağıtım bunsuz çalışmaz. (S + bir saat test)
2. **Y2 + O8** — sessiz takılma yerine iki balon. (S-M)
3. **Y3(b) 15 sn döngüsü, (a) kısa dokunuş filtresi** — bugün; tuş seçimi K-A sonrası. (S / M)
4. **Komut/uygulama/Claude küçükleri tek commit:** O2, O3, O4(a,b), O5, O6, D6 + testleri. (hepsi S)
5. **O10 görünüm yedeği** (+ D1 ikonlar istenirse). (S)
6. **O9 Ollama satırı, 4.9 mikrofon ipucu, O7 proje klasörü.** (S, S, M)
7. **D2, D3, D5 derleme cilası**, sürüm 0.1.0, zip'i yeniden al, README'ye üç dış çıkış + Sağ Ctrl notu. (S)
8. Sonra, karara göre: O1 (toggle / GSMTC), Inno + autostart, rcedit ikon, O4(c) ipucu ölçümü.

Atlananlar (YAGNI): ayrı önizleme penceresi, bulanık eşleme dışında yazım düzeltme motoru, GSMTC'yi kullanıcı sorun görmeden yazmak, kod imzası.

## Kullanıcının karar vermesi gerekenler

- **K-A. Bas-konuş tuşu:** Sağ Ctrl kalsın mı, Pause/Break varsayılan olsun mu; menüden seçilebilir olsun mu (M)?
- **K-B. Duraklat/devam:** (a) her zaman tuşa bas, balon ölçere göre · (b) GSMTC Aşama 2 · (c) olduğu gibi.
- **K-C. Proje klasörü seçici:** şimdi mi, ilk arkadaş testinden sonra mı?
- **K-D. Görünüm ikonları** menüde istenir mi?
- **K-E. Exe ikonu/sürüm bilgisi** için rcedit indirilsin mi (önceki plan 6.7)?
- **K-F. Çizimlerin lisansı:** MIT yalnızca kod; Grok çizimleri için ne yazılsın (CC-BY? "tüm hakları saklı"?).
- **Önceki plandan hâlâ açık:** K4 `claude-cli://` (varsayıldı), K6 Whisper `small`/`medium`, K7 Ollama varsayılan modeli (README hâlâ `qwen2.5:3b`, qwen-research lisansı), K8 Godot ayar klasörü, K9 Inno, K10 autostart, K12 iptal penceresi; iyileştirme planı 6.2-6.9.

## Kontrol edilen, sorun bulunmayan

- İş parçacıkları: ses geri çağrısı yalnızca `work.put` + `GetAsyncKeyState`; worker tek (COM/pycaw ilk kez worker'da içe aktarılıyor, `media._endpoint` de aynı iş parçacığında); Claude iş parçacığı yalnızca `say` → `run_coroutine_threadsafe` ve kendi dosyasını yazar; `apps._index`e yalnızca worker dokunur.
- Güvenlik sınırı: `apps.find` yalnızca `apps.json` değerlerini döndürür, `launch` yalnızca o değeri açar; metinden gelen hiçbir şey komut satırına girmez; `shell=True` yok.
- `._pth` (`python312.zip / . / .. / ..\lib`, `import site` yok) doğru; `..` satırı `main.py`nin komşu modüllerini bulur; `coloredlogs.pth` işlenmez, zararsız.
- `requirements.dist.txt` + `-c requirements.lock`: `anthropic`/`pytest` dışarıda, sürümler sabit; `asker._haiku` tembel içe aktarım → anahtar olsa da liste.
- `mic_guard.own_exes()` gömülü Python'da (`sys.executable` = `python/pythonw.exe`) doğru anahtarı üretir.
- `link.gd:50-52` python yolu: önce `listener/python/pythonw.exe`, sonra venv.
- Testler: dinleyici 74/74, Godot 0 hata (`test_say`, `test_command_menu`, `test_skins` dahil).
