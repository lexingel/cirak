# Body-double masaüstü arkadaşı: tasarım

Tarih: 2026-11-15 · Durum: taslak, onay bekliyor

## Niyet ve neden

Kullanıcıda ADHD var. Odak dağıldığında ya da bir işe başlayamadığında yalnız kalmamak istiyor. Bu uygulama ona **body doubling** hissini vermeli: yanında biri var ve o da kendi işiyle uğraşıyor.

Kullanıcıya iki şey iyi geliyor:

1. **Birinin çalıştığını görmek.** Bunun için sessiz bir varlık yeterli.
2. **Yaptığı işi birine anlatırken çalışmak.** Konuşarak da yazarak da olabilir. Karşısındakinin onu derinlemesine anlaması gerekmiyor. Arada küçük bir soru sorması iyi geliyor.

Bu bir verimlilik aracı değil, bir arkadaş.

## Hedefler

- Masaüstünde, **çerçevesiz ve arkası görünmeyen** bir **fantastik çırak** olacak: iksir karıştıran küçük bir büyücü. Kullanıcı onu fareyle tutup ekranın istediği yerine sürükleyebilecek.
- Çırak varsayılan olarak **sessizce kendi işini yapacak**: iksirini karıştırıyor, kendi temposunda hareket ediyor.
- Kullanıcı **sesli konuştuğunda** çırak bunu fark edecek ve dinlediğini gösterecek. Arada bir, anlatılana göre **kısa bir soru** soracak, örneğin "Bu bitince sırada ne var?" ya da "Takıldığın yer neresi?". Sorular **konuşma balonunda** görünecek.
- Kullanıcı yazarak da anlatabilecek: çırağa tıklayınca küçük bir yazı kutusu açılacak. Yazılan metin, konuşmayla aynı yoldan geçecek.
- İki mod arasında geçiş otomatik olacak. Kullanıcının mod seçmesine gerek kalmayacak.

## Hedef olmayanlar

- Zamanlayıcı, pomodoro, görev listesi, hatırlatma, istatistik ya da bildirim olmayacak.
- Çırak sesli konuşmayacak.
- Telefon ya da tarayıcı sürümü olmayacak. Sadece Windows masaüstü.
- Sohbet geçmişi ya da "seni tanıyan" bir hafıza olmayacak, en azından bu sürümde.

## Kesinlikle olmaması gerekenler

Bunlardan biri olursa, uygulama teknik olarak çalışsa bile başarısız sayılır:

- **Kullanıcı sessizken araya girmesi.** Sessizlik ya odak ya mola demektir. Bu sürede uyarı, sayaç ya da "hâlâ orada mısın?" sorusu olmamalı.
- **Sık soru sorup dırdır etmesi.** Soru sadece kullanıcı anlatırken gelir, o zaman da seyrek gelir.
- **Suçluluk ya da izleniyormuş hissi vermesi.** Sorularda yargılayan ya da hesap soran bir dil olmamalı.
- **Kullanıcının işini engellemesi.** Çırağın görünmeyen kısımlarına yapılan tıklamalar alttaki pencerelere geçmeli.

## Kısıtlar

- Windows 10 kullanılıyor.
- **Ses bilgisayardan çıkmayacak.** Konuşmayı yazıya çevirme işi yerelde yapılacak. Dışarıya sadece yazıya dökülmüş metin gidecek.
- Konuşma dili **Türkçe**. Yazıya çevirme ve sorular Türkçe olacak.
- Kullanıcı Godot ve pixel art konusunda deneyimli. Kendi pixel-art araçları var: `D:\Claude\PixTools` (pixart, gizpix) ve PixelLab.

## Yaklaşımlar

Üç yol düşünüldü:

1. **Tek bir Python programı (PySide6, faster-whisper ve LLM çağrısı).** En az parça bu yolda. Ama animasyon Godot'daki kadar rahat değil.
2. **Godot'da karakter, yanında küçük bir Python dinleyici.** Kullanıcının bildiği araç ve pixel art ile animasyon için en iyi ortam. Bedeli, iki ayrı süreç olması. **Seçilen yol bu.**
3. **Electron veya Tauri.** Windows'ta tarayıcının ses tanıma özelliği burada güvenilir değil, yine dışarıdan bir dinleyici gerekiyor. Bu yüzden elendi.

Kullanıcı 2'yi seçti. Benim önerim 1'di. Kullanıcı çırağın ileride daha zengin, daha animasyonlu bir karaktere dönüşebileceğini düşünüyor ve Godot'yu iyi biliyor.

## Nasıl çalışacak

### İki parça

- **Godot uygulaması (Godot 4).** Pencereyi, çırağı, animasyonları, sürüklemeyi, konuşma balonunu ve yazı kutusunu yönetir. Açılırken dinleyiciyi başlatır, kapanırken dinleyiciyi de kapatır. Kullanıcı tek bir şey çalıştırır.
- **Python dinleyici.** Mikrofonu dinler, konuşma olup olmadığını anlar, konuşmayı yazıya çevirir ve soru sorma zamanı geldiğinde soruyu üretir. Godot'ya sadece olay gönderir.

İki parça yerel bir bağlantı üzerinden konuşur, `localhost` üzerinde WebSocket ya da benzeri bir yol. Olaylar şunlar:

- `konusma_basladi` / `konusma_bitti`: çırak dinleme pozuna geçer ya da işine döner.
- `soru`: bir metin taşır, çırak bunu balonda gösterir.
- Godot'dan dinleyiciye `yazili_metin`: kullanıcının yazı kutusuna yazdığı metin.
- Godot'dan dinleyiciye `mikrofon_kapat` / `mikrofon_ac`.

### Pencere

Pencere kenarlıksız, arkası şeffaf ve her zaman üstte olacak. Fare tıklamaları sadece çırağın kendisinde yakalanacak, geri kalan her yer alttaki pencerelere geçecek. Godot'da bunun için `mouse_passthrough` ile karakterin çevresi kullanılır. Çırak sol tıkla tutulup sürüklenir. Son konumu kaydedilir ve uygulama bir sonraki açılışta oradan başlar.

### Çırağın halleri

- **Çalışıyor** (varsayılan): iksir karıştırma döngüsü. Arada küçük, rastgele hareketler yapar: kazana bir şey atar, ocağın içinden bir kabarcık çıkar.
- **Dinliyor**: kullanıcı konuşurken başını kaldırır, dikkatini ona verir.
- **Soruyor**: konuşma balonu açılır, kısa bir süre görünür kalır ve kendiliğinden kaybolur.

### Ne zaman soru sorar

- Sadece kullanıcı konuştuktan ya da yazdıktan sonra, kısa bir duraklama olduğunda sorar.
- İki soru arasında en az belli bir süre geçmeli. Bu süre ayarlanabilir, varsayılanı birkaç dakika.
- Kullanıcı sessizse hiç sormaz.
- Soru üretilirken yakın zamanda anlatılanlar kullanılır. Ama soru kısa olmalı ve hesap soran değil merak eden bir tonda olmalı.

### Sağ tık menüsü

- Mikrofonu kapat / aç
- Soru sıklığı: az / orta / çok
- Kapat

## Kullanıcının belirlediği kısımlar

- Neden ve iki mod (görmek ve anlatmak)
- Sessizken araya girmeme kuralı
- Fantastik çırak karakteri
- Çerçevesiz, serbestçe sürüklenebilen yerleşim
- Godot ve yanında bir dinleyici

## Benim varsayılanlarım (kullanıcı itiraz etmedi, düzeltebilir)

- Yazıya çevirme yerelde, faster-whisper ile yapılacak. Türkçe için `small` ya da daha büyük bir model kullanılacak.
- Sorular Claude Haiku 5.5 (`claude-haiku-5-5`) ile üretilecek. Ona sadece metin gidecek. API anahtarı bir ortam değişkeninden okunacak.
- Çırak sesli konuşmayacak, sadece balon kullanacak.
- Yazı kutusu çırağa tıklanınca açılacak.
- Mod geçişi otomatik olacak.

## Başka sesler ve görüşmeler (kullanıcının kararı)

- **Görüşme sırasında kendini susturacak.** Bilgisayarda başka bir uygulama mikrofonu kullanıyorsa (Discord, Zoom, Meet vb.), dinleyici dinlemeyi tamamen durdurur. O sırada hiçbir şey yazıya çevrilmez ve dışarı gönderilmez. Çırak bu sırada sadece çalışıyor halinde kalır. Görüşme bitince kendiliğinden yeniden dinlemeye başlar.
- **Arka plan seslerini elemeye çalışacak.** Hoparlörden ses gelirken (YouTube, müzik) duyulanları anlatım saymamaya çalışır. Bunun yöntemi kurucuya bırakıldı: hoparlör sesini ölçmek, yankı eleme ya da benzeri bir yol olabilir. Ara sıra yanlış duyması kabul edilebilir, sessizken araya girmeme kuralı ise her durumda geçerli.
- Bas-konuş tuşu bu sürümde olmayacak.

## Gözden geçirmeden sonra verdiğim kararlar

- **Kim çalıştıracak ve hangi donanımda:** Şimdilik sadece kullanıcının kendi bilgisayarı. Bilgisayarda RTX 3060 Ti (8 GB) ve Python 3.10 var. Whisper GPU'da (CUDA) çalışacak. Dinleyici sistem Python'u ile çalışacak, ayrı bir paket (exe) haline getirilmeyecek. Başkalarına dağıtmak ileride ayrı bir iş olarak ele alınacak.
- **Yazılı mesajdan sonra ne olacak:** Çırak mesajı okuduğunu küçük bir tepkiyle gösterecek, yazısız bir baş sallama ya da "hmm" animasyonu gibi. Her mesaja cevap vermeyecek. Soru kuralları aynı kalacak, yani en az bekleme süresi geçmeden soru sormayacak.
- **Haiku'ya ulaşılamazsa:** Dinleyicide yazılı, nazik sorulardan oluşan küçük bir yerel liste olacak (Türkçe, 15-20 soru). İnternet yoksa, API anahtarı yoksa ya da hata dönerse bu listeden sorar. Uygulama internetsiz de çalışır.

## Kurucuya bırakılanlar

- Godot ile dinleyici arasındaki bağlantının tam şekli ve mesaj biçimi
- Konuşma algılama yöntemi (webrtcvad, silero vb.) ve eşik değerleri
- Whisper model boyutu ile hız arasındaki denge
- Soru üretme isteminin tam metni (yukarıdaki tona uyması şartıyla)
- Çırak sprite'ının boyutu, kare sayısı ve çizim aracı (pixart, PixelLab ya da elle)
- Sağ tık menüsünün ve yazı kutusunun görünümü

## Değişiklik (2026-11-15, kullanıcının kararı)

- **Dil seçilebilir, varsayılan İngilizce.** Sağ tık menüsünde "Language / Dil" var. Seçilen dil hem Whisper'ın dinlediği dili, hem soruların dilini, hem yedek listeyi, hem de menüyü belirliyor.
- **Sorular varsayılan olarak yerel modelden geliyor** (Ollama, `qwen2.5:3b`; `CIRAK_MODEL` ortam değişkeniyle değiştirilebilir). Ücretsiz ve hiçbir metin bilgisayardan çıkmıyor. Yerel model yoksa ve `ANTHROPIC_API_KEY` tanımlıysa Claude Haiku 5.5 kullanılıyor (düşünme kapalı). İkisi de yoksa yedek liste kullanılıyor.
- Protokole yeni bir mesaj eklendi: uygulama → dinleyici `{"type":"lang","lang":"en"|"tr"}`.
