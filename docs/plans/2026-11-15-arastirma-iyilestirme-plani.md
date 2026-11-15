# Araştırma sonrası iyileştirme planı (2026-11-15)

Kaynak: `reports/Benzer uygulamalar karşılaştırması.md` (git'e girmez; notlar `research_notes/`).
Kısa özet: pazarda Çırak'ın aynısı yok (yerel, kamerasız, ücretsiz, sesli body double). Doğru
yaptıklarımız, insanların rakipleri bırakma nedenlerine denk geliyor: fiyat, kamera, seri suçluluğu,
dırdır. Eksiğimiz şu: body doubling'in en iyi ölçülmüş iki anı **başlamak** ve **dağıldıktan sonra
geri dönmek**, ve Çırak ikisinde de pasif. Ayrıca bu tür uygulamalar kaynak tüketimi, oyun sırasında
araya girme ve yenilik solması yüzünden bırakılıyor.

İlkeler değişmiyor: sessizken asla bölme, dırdır yok, suçluluk yok, puan/seri yok, konuşulanlar
diske yazılmaz. Yeni her şey **kullanıcı isteyince** çalışır.

## Kodda zaten olanlar (rapor bunları eksik saydı)

- Whisper'ın önünde VAD var: `hearing.py:170` `vad_filter=True` (Silero), önünde de ses seviyesi kapısı.
- Godot `low_processor_mode=true` (ekran yalnız değişince çiziliyor).
- Arama sırasında susma var: başka bir uygulama mikrofonu kullanınca (`mic_guard.mic_user`).
- Yardım sayfasında gizlilik bölümü var; README'de "nothing leaves your PC" var.

## Faz 1: kaynak, araya girmeme, güven (ucuz, önce bu)

**1.1 Ölç ve yayınla.**
- Boşta ve konuşurken CPU/RAM ölç: Cirak.exe + pythonw listener (Whisper yüklü, Ollama ayrı).
- Tablo README'ye girsin: "boşta ~X% CPU, ~Y MB RAM".
- Çizim boşta yüksekse `Engine.max_fps` 30'la sınırlansın (animasyon zaten ~10 fps), sonra yeniden ölçülsün.
- Test: ölçüm betiği `tools/measure.py` (psutil, 60 s örnek), çıktısı README'ye.

**1.2 Tam ekranda gizlen.**
- Listener her 2 s'de bir ön pencereye bakar (ctypes `GetForegroundWindow` + monitör dikdörtgeni).
- Pencere tüm ekranı kaplıyorsa ve bizim değilse `{"type":"fullscreen","on":true}` gönderir; app çırağı gizler, kapanınca geri getirir.
- Dinleme sürer; ayrıca "oyundayken dinleme" seçeneği eklenebilir (K2).
- Menüye "1 saat gizle" de girsin.
- Test: fullscreen kararı saf bir fonksiyon `is_fullscreen(win_rect, mon_rect, own)`, pytest ile.

**1.3 Mikrofon durumu görünsün.**
- Çırağın yanında küçük bir işaret olsun: dinliyor (yeşil nokta), aramada duraklatıldı (gri), mikrofon kapalı (çarpı).
- Bugün bu bilgi yalnızca menüde.
- Godot'ta çizimle yapılır, yeni sanat gerekmez (K3 ister misin?).

**1.4 İnternete çıkan komutları işaretle.**
- "Claude'a sor" cevabının balonunda küçük bir "↗ Anthropic" etiketi olsun.
- Yardım sayfasında bu iki komutun yanına "internete çıkar" yazılsın.
- İmza: SignPath onayı bekleniyor (yapıldı, bekliyor).

**1.5 Dürüst tanıtım.**
- README/yardım: "pek çok kişi yanında biri varken daha kolay başladığını söylüyor; kontrollü kanıt sınırlı".
- Tıbbi bir iddia olmasın.

## Faz 2: başlamak ve geri dönmek (araştırmanın asıl dersi)

**2.1 "Başlıyorum" komutu.**
- "Çırak, başlıyorum" / "let's start" denince çırak her seferinde farklı bir açılış sorusu sorar ("Neyle uğraşıyoruz bugün?" ve benzerleri).
- Ollama varsa ondan, yoksa en az 12 cümlelik listeden, son 3'ü tekrar etmeden.
- Asla kendiliğinden sormaz.
- Test: `commands.py` kuralı + tekrar etmeyen seçici için pytest.

**2.2 "Neredeydik?" komutu.**
- "Neredeydim / where was I" denince son anlatılandan tek cümlelik bir hatırlatma gelir ("En son menü düğmelerini hizalıyordun").
- Son ~10 cümle yalnız **RAM'de** tutulur. Çıkınca silinir, diske yazılmaz (transkript kuralı korunur).
- Ollama yoksa son cümle aynen gösterilir.
- Test: tampon (boyut sınırı, temizleme) + komut kuralı.

**2.3 Etkileşim düzeyi.**
- Soru sıklığına **"Hiç (sadece dinle)"** eklensin. Bugün yalnızca low/mid/high var.
- "Durgun çırak" seçeneği: kazanı karıştırır ama malzeme atmaz, hareket azalır.
- Ses efekti yok, o yüzden ayrı ses ayarına gerek yok.
- Test: `gate.py` LEVELS'a "off" + main.gd menüsü + Godot testi.

## Faz 3: küçük ADHD yardımcıları (isteğe bağlı)

**3.1 "Bunu parçala" komutu.**
- "Çırak, bunu parçala: mutfağı toplamak" gibi bir istekte yerel Ollama 3-5 küçük adım çıkarır, balonda gösterir.
- İlk adım "2 dakikalık" kadar küçük olsun.
- Ollama yoksa "Bunun için soru modeli lazım" der ve menüdeki kurulum satırını gösterir.
- Test: prompt çıktısının ayrıştırılması (numaralı satırlar, en çok 5), sahte Ollama ile.

**3.2 Seans özeti (yalnız istenince).**
- "Bitirdim / done for today" denince RAM'deki anlatımdan 2-3 maddelik bir "bugün şunlarla uğraştın" çıkar.
- Kaydedilmez. Kanıtı zayıf olduğu için en küçük haliyle yapılsın (K4).

## Faz 4: uzun ömür (kullanıcı kararı gerekli)

**4.1 Kaybedilemeyen birikim.**
- Toplam anlatım dakikasıyla yavaşça dolan bir kazan. Dolunca yeni bir malzeme açılır (atılan malzemeler değişir).
- Seri yok, sıfırlanma yok, sayı gösterilmez.
- "Puan yok" ilkesiyle sürtünebilir ve yeni sanat ister (K1).

**4.2 Mod klasörü.**
- `%LOCALAPPDATA%\Cirak\questions\*.txt` ile kendi soru paketlerin, `looks\<ad>\` ile kendi görünümlerin olsun (mevcut sheet düzeni).
- Menüde "Mod klasörünü aç" satırı olsun. VPet'i ayakta tutan şey bu.

## Bilerek yapılmayanlar

- Zamanlayıcı/pomodoro, dikkat dağınıklığı tespiti, görev yöneticisi. Stres ve gözetim hissi yaratıyor, Çırak'ı ağırlaştırıyor.
- Yeni diller ve ekran okuyucu desteği: değerli ama pahalı. 4. fazdan sonra.

## Kararlar (kullanıcının)

- **K1:** Faz 4.1 birikim (dolan kazan + yeni malzemeler) olsun mu? Sanat Grok'tan mı gelecek?
- **K2:** Tam ekranda çırak gizlenirken dinleme de dursun mu (oyun sesini duymasın), yoksa sürsün mü?
- **K3:** Mikrofon işareti basit bir nokta mı olsun, yoksa çizimin kendisi mi değişsin (kulak/göz)?
- **K4:** Seans özeti (3.2) yapılsın mı, yoksa şimdilik atlansın mı?

## Sıra ve sürüm

Faz 1 ile 2.3 bir arada → **v0.2.0** (imza gelirse imzalı). Faz 2.1-2.2 + 3.1 → **v0.3.0**.
Faz 4 kararlardan sonra.

## Durum

- **Faz 1 bitti (2026-11-15).**
  - Ölçüm (`tools/measure.py`, boşta 60 s): Cirak.exe ~%0 CPU / 129 MB, listener ~%0,07 CPU / 250 MB. FPS sınırına gerek kalmadı.
  - Tam ekranda gizlenme (`listener/screen.py`, 2 s'de bir), "Çırak, saklan / geri gel" + menüde "1 saat saklan".
  - Mikrofon noktası (yeşil/sarı/kırmızı), Claude cevabında "(Claude, internetten)", yardım ve README güncellendi.
  - Canlı denendi: tam ekran mesajı, saklan/geri gel, nokta ekran görüntüsünde.
  - K2 kararı bekleniyor: gizliyken dinleme şimdilik sürüyor.
