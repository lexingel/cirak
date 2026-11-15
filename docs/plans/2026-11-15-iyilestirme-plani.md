# Çırak: iyileştirme planı

Tarih: 2026-11-15 · Kaynak: kodun okunması (app/, listener/, build, docs/specs). Kod değiştirilmedi.

Kısa özet: Uygulama sağlam bir iskelet. Çok ekranlı konum, yeniden bağlanma, dinleyicinin uygulamayla birlikte kapanması, Ollama/GPU yoksa yedekler, origin kontrolü ve saf mantık testleri yerinde. Asıl eksikler üç yerde toplanıyor: **hata görünmezliği** (pythonw altında hiçbir log yok), **mikrofon/gürültü dayanıklılığı** (mik yoksa çökme döngüsü; gürültülü odada sürekli "dinliyor" pozu) ve **sessiz duraklama** (başka bir uygulama miki tutuyorsa çırak neden dinlemediğini söylemiyor). Geri kalanı tek satırlık cilalar ve kullanıcının vereceği birkaç karar.

Boyutlar: küçük = birkaç satır, bir oturumun küçük parçası · orta = bir dosyada 20-50 satır + test · büyük = birden fazla dosya / yeni çizim / indirme.

---

## 1) Hatalar ve riskler (önce bunlar)

### 1.1 pythonw altında hatalar hiçbir yere yazılmıyor
- **Ne / neden önemli:** Dinleyici `pythonw.exe` ile başlıyor (`app/link.gd:39`). pythonw'da `sys.stderr` ve `sys.stdout` `None`. `listener/main.py:43` `print(..., file=sys.stderr)` bu durumda sessizce hiçbir şey yazmaz. Whisper/CUDA hatası, Ollama hatası, ses cihazı hatası, "Task exception was never retrieved" uyarıları: hepsi kayboluyor. Gerçek ses testinde "soru gelmiyor" dendiğinde bakacak yer yok.
- **Yer:** `listener/main.py:37-45` (worker), `listener/main.py:80`.
- **Minimal düzeltme:** `main.py` başına 2 satır: `if sys.stderr is None: sys.stderr = sys.stdout = open(Path(__file__).with_name("listener.log"), "a", buffering=1, encoding="utf-8")`. Sadece hata/istisna yazılır; yazıya dökülen anlatım metni **loga yazılmaz** (gizlilik). `listener.log` `.gitignore`'a.
- **Boyut:** küçük.

### 1.2 Mikrofon açılamazsa dinleyici çöker, uygulama 10 s'de bir yeniden başlatır
- **Ne / neden önemli:** `Hearing(...)` ve `hearing.start()` (`listener/main.py:48-50`) try/except dışında. `sd.InputStream` (`listener/hearing.py:48`) cihaz yoksa, USB mik çekildiyse ya da cihaz 16 kHz'i reddederse istisna fırlatır → `asyncio.run` düşer → süreç biter. `app/link.gd:56-60` 10 s sonra yeniden başlatır. Her başlatmada worker thread Whisper'ı GPU'ya yüklemeye başlar (`main.py:46`) ve yarıda ölür. Sonsuz döngü, GPU boşa, yazılı yol da çalışmaz.
- **Yer:** `listener/main.py:48-51, 70-73`.
- **Minimal düzeltme:** Hearing kurulumunu try/except'e al; başarısızsa `hearing = None`, loga bir satır, websocket sunucusu yine çalışır (yazı kutusu çalışmaya devam eder). `want != mic_running` dalında `hearing is None` ise atla.
- **Boyut:** küçük-orta.

### 1.3 Gürültülü oda → çırak sürekli "dinliyor" pozunda, Whisper her 30 s çalışır
- **Ne / neden önemli:** Eşik sabit `0.015` RMS (`listener/hearing.py:44`). Fan/klima/sokak gürültüsü eşiği aşarsa `talking` hiç bitmez; `MAX_SECONDS=30` (`hearing.py:8,36`) ile 30 s'de bir kesilir, Whisper'a gider (boş döner), 270 ms sonra yeniden başlar. Sonuç: çırak kullanıcıya bakmaya devam eder ("izleniyormuş" hissi, bölüm 2), GPU boşuna döner, CPU yedeğinde laptop ısınır. Ayrıca `speech_start` ses tanınmadan **önce** gönderiliyor (`listener_core.py:31-35`): herhangi bir 270 ms sürekli ses başını kaldırtır.
- **Yer:** `listener/hearing.py:42-60`.
- **Minimal düzeltme:** `Hearing._cb` içinde gürültü tabanı takibi: sessiz blokların RMS'inin kayan ortalaması `floor`; `loud = rms > max(threshold, 3 * floor)`. ~5 satır, `Detector` saf kaldığı için test kolay. Önce 5.2'deki ölçerle gerçek sayıları gör (sessiz oda, klavye, konuşma), eşiği ona göre.
- **Boyut:** küçük-orta.

### 1.4 Arka planda miki tutan bir uygulama → kalıcı, sessiz duraklama
- **Ne / neden önemli:** Görüşme algısı `LastUsedTimeStart>0 and Stop==0` (`listener/mic_guard.py:23-25`). Bu, Discord'un sesli kanalı için doğru; ama miki sürekli açık tutan her şey için de "görüşme" sayılır: NVIDIA Broadcast, Krisp, VoiceMeeter, mik izni açık bir tarayıcı sekmesi, Discord'un ses ayarları ekranı. O zaman dinleyici duraklar (`listener_core.py:21-26`), çırak sadece karıştırır ve kullanıcı "neden dinlemiyor?" sorusunun cevabını hiçbir yerden alamaz. Spec "görüşmede sussun" dedi; bu doğru, eksik olan görünürlük.
- **Yer:** `listener/mic_guard.py:23`, `listener/listener_core.py:21-29`, `app/main.gd:70-76` (menü), `app/apprentice.gd:76`.
- **Minimal düzeltme:** `mic_in_use_by_other` tetikleyen anahtarı da döndürsün; `paused` mesajına `"who": "Discord.exe"` eklensin; Godot sağ tık menüsünde tıklanamaz (disabled) bir satır: "Dinleme: duraklatıldı (Discord.exe)" / "Listening: paused (…)". Menü sadece kullanıcı açınca görünür, yani bildirim değil, kurallara uygun.
- **Boyut:** orta-küçük.

### 1.5 Hoparlör ölçeri cihaz değişince eski cihazı okuyor (bilinen küçük)
- **Ne / neden önemli:** `_meter` bir kez alınıp sonsuza dek saklanıyor (`listener/mic_guard.py:58-72`). Kulaklık takılıp çıkarılınca varsayılan çıkış değişir, ölçer eski cihazı okur: ya hep 0 (gate kapalı) ya hata (gate kapalı). Hata sonrası `_meter` sıfırlanmıyor.
- **Minimal düzeltme:** `except` içinde `_meter = None`; ayrıca ölçeri 30-60 s'de bir yeniden al (bir zaman damgası, 2 satır).
- **Boyut:** küçük.

### 1.6 Uygulama gün boyu 60 fps çiziyor
- **Ne / neden önemli:** `app/project.godot` içinde `low_processor_mode` yok. Hep açık duran bir arkadaş için RTX'in ve CPU'nun bir dilimi sürekli boşa gider (fan, laptopta pil).
- **Minimal düzeltme:** `[application]` altına `run/low_processor_mode=true` (+ isteğe bağlı `run/max_fps=30`). `AnimatedSprite2D` kare değişiminde çizim ister, balon tween'i de; görsel fark yok. Test: animasyon akıyor mu, balon solması düzgün mü, websocket `_process` çalışıyor mu (evet, low processor sadece çizimi azaltır).
- **Boyut:** küçük.

### 1.7 Balon tıklama alanı bir kare geç hesaplanıyor (düşük)
- **Ne:** `show_text` sonrası hemen `shape_changed.emit()` (`app/apprentice.gd:73-75`); `main.gd:226-227` o anda `bubble.size`'ı okuyor, layout henüz çalışmamış → ilk soruda alan 0, sonrakilerde eski boyut. Sonuç: balona tıklama alta geçer. Balonda tıklanacak bir şey yok, pratikte fark edilmez.
- **Minimal düzeltme (istersen):** `apprentice.gd _ready` içinde `bubble.resized.connect(shape_changed.emit)`. Tek satır.
- **Boyut:** küçük.

### 1.8 Sürükleme: kod doğru görünüyor, test yeter
- `app/main.gd:131-151`: Godot Windows'ta tuş basılıyken fareyi yakalar (SetCapture), bu yüzden hızlı sürüklemede bırakma olayı kaçmamalı; `_pressed` takılı kalma riski düşük. Ucuz sigorta: `_notification`'da `WM_WINDOW_FOCUS_OUT` geldiğinde `_pressed = false` (tek satır). Monitörler arası sürükleme ve kısmen ekran dışına bırakma `restore_pos` (`main.gd:108-112`) ile bir sonraki açılışta toparlanıyor; iyi.

### 1.9 İki pythonw süreci: normal, düzeltme gerekmez
- `listener/.venv/Scripts/pythonw.exe` bir **başlatıcı** (`pyvenv.cfg` → home = Python310). Gerçek yorumlayıcıyı çocuk süreç olarak açar ve bir Windows Job nesnesine koyar (KILL_ON_JOB_CLOSE). `app/link.gd:76` `OS.kill(_pid)` başlatıcıyı öldürünce çocuk da ölür. İkinci sigorta: `listener/main.py:17,74-77` istemci yoksa 10 s'de kendini kapatır (Godot çökse bile mik açık kalmaz). `test_mic_guard.py:24` bu ikiliği zaten biliyor. Bir kez Görev Yöneticisi'nde doğrula: uygulama kapanınca 10 s içinde iki pythonw da gitmeli.

### 1.10 `send()` thread yarışı (bilinen küçük): zararsız
- `listener/main.py:27-30`: coroutine worker thread'de yaratılıyor, loop'ta çalışıyor; bu geçerli. Tek yan etki, bağlantı tam o anda kapandıysa "Task exception was never retrieved" uyarısı (1.1 ile artık loga düşer). İstersen `asyncio.run_coroutine_threadsafe(...)` ile sonucu yut. Düşük öncelik.

### 1.11 Mik, kayıtlı `mic:false` gelmeden kısa süre açılıyor (bilinen küçük)
- `listener/main.py:50` `hearing.start()` istemci bağlanmadan önce. Ses PC'den çıkmıyor, sadece Windows mik göstergesi 1-2 s yanıyor. Düzeltme: `core.mic_on` başlangıçta `None` (→ `listening` False), `hearing.start()`'ı döngüye bırak, ilk `mic` mesajı gelince açılır. 3 satır. Düşük öncelik.

### 1.12 Bağımlılık sürümleri sabit değil
- `listener/requirements.txt` pin'siz. faster-whisper 1.2.1 / ctranslate2 4.9.0 / CUDA DLL zinciri kırılgan; websockets 16 yeni asyncio API'si (kod `handler(ws, *_)` ile uyumlu, iyi). Bir `pip freeze` ile pin'le (ya da `requirements.lock`). Yeniden kurulum gerektiğinde saatler kazandırır.
- **Boyut:** küçük.

### İyi olanlar (dokunma)
- Çok ekran: kayıtlı konum var olan monitörde kalır, yoksa birinciye çekilir (`main.gd:96-112`, testli).
- Yeniden bağlanma 2 s, yeniden başlatma 10 s geri çekilmeli (`link.gd:9-10, 56-65`), bağlanınca ayarlar yeniden gönderilir (`main.gd:87-90`).
- Ollama yoksa / model çekilmemişse (404) / 8 s'de cevap yoksa → Haiku → liste (`asker.py:71-83, 109-114`). GPU yoksa CPU int8 (`hearing.py:70-73`). Hiçbiri çökertmez.
- Tarayıcıdan bağlanma engeli (`main.py:19`, testli). Bozuk JSON iki tarafta da yutuluyor.
- İki Cirak.exe açılırsa ikinci dinleyici portu alamaz ve 10 s'de bir dener; iki uygulama da ilk dinleyiciye bağlanır. Tek kullanıcı için sorun değil, uğraşma.

---

## 2) Kurallara aykırı düşebilecekler

### 2.1 Kulaklıkla müzik → çırak sağır (karar gerekir, bkz. 6.1)
- **Ne:** Hoparlör çıkışı varsa konuşma hiç sayılmıyor, başını bile kaldırmıyor (`listener/listener_core.py:32-35`, `mic_guard.py:61`). Hoparlörde doğru davranış (YouTube sesi anlatım sayılmasın; sayılsa kullanıcı sessizken şarkı sözünden soru gelir, asıl kural çiğnenir). Kulaklıkta yanlış: mikrofona müzik gitmiyor ama kullanıcı anlatırken çırak hiç tepki vermiyor. Kulaklıkla müzik dinleyerek çalışan biri için uygulama "bozuk" görünür.
- **Seçenekler:** (a) menüye "Kulaklıktayım" anahtarı (speaker gate kapalı) — küçük; (b) varsayılan çıkış cihazının form faktörünü oku (pycaw, `PKEY_AudioEndpoint_FormFactor`: Headphones/Headset ise gate kapalı) — orta, otomatik ama cihaz adlandırması güvenilmez olabilir; (c) olduğu gibi bırak.

### 2.2 Odadaki başka konuşma / TV → kullanıcı sessizken soru gelebilir
- Spec bunu kabul etmiş ("ara sıra yanlış duyması kabul edilebilir"). Mevcut korumalar yeterli: 3 kelime altı sayılmaz (`gate.py:5,19`), 8 kelime eşiği (`gate.py:11`), Whisper `no_speech_prob`/`avg_logprob` filtresi (`hearing.py:76`), halüsinasyon listesi (`gate.py:3-4`). Ek kod gerekmez; 1.3 eşiği odaya uydur ve gerçek testte izle.

### 2.3 İlk soru tek cümleden sonra geliyor
- **Ne:** `_last_asked = -inf` (`gate.py:15`) + `min_words=8` (`gate.py:11`): ilk 8 kelimelik cümlenin ardından hemen soru. "Seyrek" kuralı ancak ikinci sorudan itibaren işliyor. Sabah ilk cümlede soru gelmesi hevesli durabilir.
- **Minimal:** ya `min_words` 8 → 20 civarı, ya `_last_asked = now - min_interval/2` ilk `add_text`'te. Tek sayı. His meselesi → 6.5.
- **Boyut:** küçük.

### 2.4 Soru 1.5 s'lik nefes duraklamasında geliyor
- **Ne:** Söz 1.5 s sessizlikte biter (`hearing.py:7`), ardından hemen soru (`listener_core.py:48-54`). Kullanıcı düşünürken nefes aldığı anda balon açılırsa "araya girme" hissi.
- **Minimal:** `_narrate` soruyu üretmesin, adayı işaretlesin; `tick()` (saniyede bir, `main.py:69`) son söz bitiminden ≥4-5 s geçmiş ve o an konuşma yoksa (`Detector.talking` → core'a bir bayrak) soruyu gönderir. ~8-10 satır + 1 test.
- **Boyut:** küçük-orta. Önce gerçek testte his; belki gerekmez.

### 2.5 Yerel modelin cevabı tonu kaçırabilir
- **Ne:** `_clean` (`asker.py:99-106`) ilk satırı alıp uzunluğa bakıyor; "yargılama, hesap sorma" kuralı sadece istemde. 3b model Türkçede zayıf (bilinen); "Neden hâlâ bitirmedin?" gibi bir cümle geçer, soru olmayan bir tavsiye cümlesi de geçer. Yanlış dilde cevap da yakalanmıyor.
- **Minimal:** (1) `SYSTEM` istemine FALLBACK'ten 2-3 örnek soru ekle (few-shot; 3b'nin dilbilgisini belirgin düzeltir, ücretsiz); (2) `_clean`'de `?` ile bitmeyeni reddet (`q.endswith("?")`), böylece tavsiye/yorum cümleleri listeye düşer. Yanlış dil için güvenilir ucuz kontrol yok → 7b kararı 6.2.
- **Boyut:** küçük.

### 2.6 Haiku yedeği: Ollama tökezlerse anlatım metni sessizce buluta gidiyor
- **Ne:** `ANTHROPIC_API_KEY` ortamda tanımlıysa (`asker.py:112`) Ollama'nın her 8 s zaman aşımında metin Anthropic'e gider. Spec buna izin veriyor; ama kullanıcı değişiklik notunda "varsayılan yerel, hiçbir metin çıkmıyor" dedi ve anahtar bu PC'de muhtemelen başka işler için zaten tanımlı.
- **Minimal:** `CIRAK_CLOUD=1` yoksa Haiku'ya gitme (1 satır). Karar 6.4.

---

## 3) Deneyim / his

### 3.1 Baş sallama fark edilmiyor
- 3 kare @ 8 fps = 0.375 s (`app/apprentice.gd:14`). "Duydum" demiyor, titreme gibi. `8.0 → 4.0` (0.75 s). Tek sayı. **Küçük.**

### 3.2 Soru öncesi boşluk: dinle → karıştır → aniden balon
- Akış: `speech_end` → nod → working → 1-8 s sonra (transcribe + Ollama) balon (`listener_core.py:37-54`). Çırak işine dönmüş gibi görünürken balon pat diye açılıyor.
- **Minimal, çizimsiz:** `speech_end` içinde sırayı değiştir: önce transcribe + `gate.add_text`; soru gelecekse `speech_end` gönderme, doğrudan `question` gönder (çırak LISTENING → ASKING, arada karıştırma yok; soru üretilirken "dinliyor" pozu düşünüyormuş gibi durur). Soru gelmeyecekse `speech_end` (nod). ~4 satır yer değişimi + mevcut `test_narration_leads_to_question` beklentisi güncellenir.
- **Boyut:** küçük.

### 3.3 Boşta hayat: sadece yaprak atma (45-120 s)
- `apprentice.gd:17-18`. Çizimsiz seçenekler: (a) çalışma döngüsü hızına küçük rastgelelik, `animation_looped` sinyalinde `sprite.speed_scale = randf_range(0.9, 1.1)` → metronom hissi kırılır, tek satır; (b) kazandan kabarcık: `CPUParticles2D`, 2-3 px yeşil kare, 20-40 s'de bir 1-2 tane — spec'te geçiyor ("ocağın içinden bir kabarcık çıkar"), ~10 satır; (c) yeni çizim isteyenler (göz kırpma, esneme, uyuklama) → 6.8. Hepsi "kendi işiyle uğraşıyor" sınıfında, kurallara uygun.
- **Boyut:** (a) küçük, (b) küçük-orta, (c) büyük (çizim).

### 3.4 Yazarken soru gelirse balon yazı kutusunun üstüne biniyor
- Yazı kutusu (10,30) 240×30 (`main.gd:55-56`); balon (12,6)'dan aşağı ~80 px (`apprentice.gd:33`, metin uzunluğuna göre). `_open_text_box` içinde `apprentice.bubble.close()` tek satır: kullanıcı yazıyorsa soru bekleyebilir. **Küçük.**

### 3.5 Balon süresi sabit 8 s
- `bubble.gd:7`. 15 kelimelik Türkçe için dar olabilir. `6 + 0.4 × kelime` saniye, tek satır. Muhtemelen iyi; gerçek testte bak. **Küçük.**

### 3.6 DPI
- Pencere 260×220 sabit, `SCALE=3` (`project.godot`, `apprentice.gd:9`). %100 ölçekli monitörde doğru. %125-150'de çırak küçük görünür; iki monitör farklı ölçekteyse biri hep yanlış. Düzeltme: `k = DisplayServer.screen_get_dpi()/96`, SCALE + pencere boyutu + sabit konumlar (`main.gd:51,55-56`, `apprentice.gd:33`) k ile çarpılır → orta. Kullanıcıda HiDPI yoksa yapma → 6.9.

---

## 4) Paketleme

### 4.1 İkon
- `app/export_presets.cfg` ikon ayarı yok, `project.godot`'ta `config/icon` yok. Exe ikonu için Godot **rcedit** ister (indirme, kullanıcı onayı). İndirmesiz yol: pencere/görev çubuğu için `application/config/icon` = çırağın bir karesinden 64 px png; **masaüstü ve başlangıç kısayolunun ikonunu** .ico'ya ayarla (kısayol özellikleri). .ico'yu PixTools/Pillow ile 48 px kareden 16/32/48/256 boyutlarında üretmek 5 satır. **Küçük.** Exe'nin kendi ikonu → 6.7.

### 4.2 Otomatik başlatma
- `shell:startup` klasörüne `build\Cirak.exe` kısayolu, kod yok. Yan etki: oturum açılışında Ollama henüz hazır değilse `main.py:47` ısıtma boşa gider → ilk soru 8 s zaman aşımı → liste. Düzeltme: ısıtma başarısızsa `tick` içinde 60 s'de bir tekrar dene (3 satır). Başlasın mı → 6.7. **Küçük.**

### 4.3 Taşınabilirlik
- `app/link.gd:37-42` exe'nin yanındaki `../listener/.venv` sabit; tek kullanıcı için yeterli. Riskli kısım `pythonw` PATH yedeği (`link.gd:40-41`): venv bulunamazsa bağımlılıksız bir Python'la başlar, anında çöker, 10 s'de bir tekrar (1.2 döngüsü). Minimal: yedeği kaldır ya da `CIRAK_LISTENER` ortam değişkeniyle yol override. Dağıtım (PyInstaller, kurulum paketi) spec'te ileriye bırakıldı → yapma. **Küçük.**

### 4.4 İlk kurulum notu
- Whisper `small` modeli HF cache'ten geliyor (`hearing.py:71`); temiz makinede ilk çalıştırma ~500 MB indirir, internet yoksa her transcribe sessizce hata verir (1.1 ile görünür olur). Ollama + `ollama pull qwen2.5:3b` de ayrı. `listener/README` ya da `requirements.txt` yanına 5 satırlık kurulum notu. **Küçük.**

### 4.5 `preview.png` geri gelebilir
- `tools/import_frames.py:133` önizlemeyi `app/art/`'a yazıyor; şu an orada yok ama bir sonraki import'ta geri gelir ve `export_filter="all_resources"` ile exe'ye girer. `docs/` ya da `art_in/`'e yaz, tek satır. **Küçük.**

### 4.6 Sürüm pin'leri → 1.12.

---

## 5) Test eksikleri

### 5.1 Miksiz canlı animasyon kontrolü (en değerli)
- Kullanıcı dinleme/baş sallama/soru animasyonlarını canlı görmedi. `listener/tests/fake_listener.py` (~20 satır): 47613'te serve, 2 s `speech_start`, 5 s `speech_end`, 7 s `question`, 20 s `paused`. Gerçek dinleyici kapalıyken çalıştır, Godot kendisi bağlanır (`link.gd` zaten her 2 s dener). Balon konumu, tıklama alanı, 3.1/3.2 hissi hep buradan görülür. **Küçük.**

### 5.2 Mikrofon seviye ölçer
- `python hearing.py` → 10 s boyunca RMS yazdır (sessiz / konuşma / hızlı klavye). 0.015 eşiği ve 1.3'teki gürültü tabanı için gerçek sayılar. `hearing.py` sonuna `if __name__ == "__main__":` ~10 satır. **Küçük.**

### 5.3 Whisper segment filtresi saf değil
- `hearing.py:76` filtre `transcribe` içinde; `keep(segs)` olarak ayır + eşik testleri (`no_speech_prob`, `avg_logprob`). **Küçük.**

### 5.4 listener_core: konuşma sırasında görüşme başlarsa
- `speech_start → tick(call) → speech_end` sırasında `speech_end` gönderildiği (çırak dinlemede takılmaz, `listener_core.py:38-41`) test edilmiyor. 5 satır. **Küçük.**

### 5.5 Elle test listesi (Godot tarafı testlenmiyor, listelensin)
- Sürükle: yavaş, hızlı, monitörler arası, yarısı ekran dışında bırak → yeniden aç.
- Sağ tık menüsü: her öğe, dil değişince metinler, mik kapat → dinleyici `mic:false` alıyor mu (1.1 logundan).
- Yazı kutusu: Enter, Esc, dışarı tıklama, boş metin.
- Kapanış: iki pythonw 10 s içinde gidiyor mu (1.9).

### 5.6 Gerçek ses testi listesi (kullanıcı)
- Sessiz oda 10 dk → hiçbir şey olmamalı (çırak başını kaldırmamalı).
- Hızlı klavye → başını kaldırmamalı (kaldırıyorsa 1.3).
- 2-3 cümle anlatım → dinle → (nod) → soru; soru tonu ve dili.
- Discord sesli kanala gir/çık → duraklama ve devam.
- Hoparlörden YouTube → tepki yok. Kulaklıkla müzik + anlatım → 6.1 kararına göre.

### İyi olanlar
- Saf mantık testleri (gate, asker, detector, mic_guard, listener_core, origin) ve `run_tests.gd` 9 testi yerinde ve geçiyor. Mimari (ses/ağ dışarıda, mantık saf) testi kolay tutuyor; koru.

---

## 6) Kullanıcının karar vermesi gerekenler

1. **Kulaklıkla müzik** (2.1): (a) menüde anahtar, (b) cihaz tipinden otomatik, (c) olduğu gibi.
2. **Türkçe soru kalitesi** (2.5): önce ücretsiz few-shot + `?` kontrolü; yetmezse `qwen2.5:7b` (~5 GB indirme, VRAM ~5 GB + Whisper ~1 GB → 8 GB'a sığar, oyunla çakışır). Onay gerekir.
3. **Ollama keep_alive 2h** (`asker.py:16`): 2 GB VRAM iki saat tutulur. Oyun/başka GPU işi varsa `30m` daha rahat; bedeli ilk sorunun listeden gelmesi.
4. **Haiku yedeği** (2.6): açık onay değişkeni olsun mu, yoksa anahtar varsa otomatik mi?
5. **Soru zamanlaması** (2.3, 2.4): ilk soru eşiği ve soru öncesi bekleme; gerçek testten sonra his üzerinden.
6. **Whisper modeli:** İngilizce varsayılanda `small` yeter. Türkçe ağırlıklı kullanılacaksa `medium` (~1.5 GB indirme, VRAM ~2.5 GB) belirgin daha iyi. Onay gerekir.
7. **Otomatik başlatma + ikon** (4.1, 4.2): başlangıçta açılsın mı; exe ikonu için rcedit indirilsin mi, yoksa kısayol ikonu yeter mi?
8. **Yeni çizimler** (3.3c): göz kırpma, esneme, uyuklama Grok listesine eklensin mi? Önce çizimsiz (a)/(b) denensin.
9. **DPI** (3.6): HiDPI monitör var mı / gelecek mi? Yoksa dokunulmaz.

---

## Önerilen sıra: ilk 5

1. **1.1 Log dosyası.** Her şeyin önkoşulu; gerçek ses testinde ne olduğunu görmenin tek yolu. 2 satır.
2. **5.1 + 5.2 Sahte dinleyici ve mik ölçer.** Kod değiştirmeden animasyonları canlı gör, eşik için gerçek sayıları al. İki küçük script.
3. **1.2 Mik yoksa çökme döngüsü.** Yazılı yol ve uygulama mik olmadan da ayakta kalsın.
4. **1.3 Gürültü tabanı.** 5.2'nin sayılarıyla. "İzleniyorum" hissini ve boşa GPU'yu kesen tek değişiklik.
5. **1.4 Duraklama nedeni menüde.** Discord/Broadcast yüzünden dinlemeyen çırak sebebini söylesin.

Yolda tek satırlıklar, hangi commit'e denk gelirse: 1.6 `low_processor_mode`, 3.1 nod hızı, 2.5 `?` kontrolü + few-shot, 3.4 yazarken balonu kapat, 1.12 pin'ler, 4.5 preview yolu.

---

## Durum (2026-11-15 sonu)

Yapıldı: 1.1-1.5, 1.6, 1.7, 1.8, 1.10, 1.11, 1.12 (`listener/requirements.lock`), 2.5 (`?` kontrolü, EN örnekleri; TR'de örnek yok, 3b kopyalıyor), 3.1, 3.2, 3.3a, 3.4, 3.5, 4.2 (Ollama ısıtma 60 s'de bir tekrar), 4.3 (PATH yedeği kaldırıldı), 4.4 (`listener/README.md`), 4.5, 5.1-5.4. Ek: mikrofon seçici, CPU Whisper yedeği, takılan bağlantı, temiz kapanış, soru talimatı.

Açık (kullanıcı kararı): 6.1 kulaklık, 6.2 qwen2.5:7b, 6.3 keep_alive, 6.4 Haiku onayı, 6.5 soru zamanlaması (2.3, 2.4), 6.6 Whisper medium, 6.7 otomatik başlatma + ikon, 6.8 yeni çizimler (3.3b kabarcık dahil), 6.9 DPI. Elle test listeleri 5.5 ve 5.6.
