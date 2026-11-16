# Yeni görünüm önerisi: "Çırağın tezgâhı" (2026-11-16)

Kaynak: dört kısa araştırma, şu konularda:

- benzer masaüstü arkadaşları
- DEHB için tasarım
- piksel sanat stilleri
- Grok Imagine

Notlar oturumun scratchpad klasöründe, `design_research/*.md`. Kaynakların çoğu blog ve inceleme. Aşağıdaki sayıların bir kısmı ölçülmüş standart değil, kural olarak koyduğumuz başlangıç değerleri.

## 1. Fikir

Çırak masaüstünde havada duran bir figür olmaktan çıksın, **küçük bir tezgâhın başında oturan** bir çırak olsun.

- Tahta bir raf ya da pencere kenarı her şeyi tek parçada toplar: çırak, işinin aleti (kazan, örs, havan...) ve arkasında kavanoz rafı.
- Araştırma 1 bunu destekliyor: sevilen örneklerin hepsi bir zemine oturuyor. Bunlar Rusty's Retirement'ın alt şeridi ve Bongo Cat'in görev çubuğu.
- Bugün yalnız duran kavanoz ve rafın "havada" görünme sorunu da böylece kendiliğinden çözülür.

**Ana davranış: çırak senin konuştuğun kadar çalışır.**

- Sen anlatırken karıştırır.
- Susunca yavaşlar.
- Bir dakika sessizlikten sonra duruşu sabitlenir: nefes alır, gözünü kırpar.

Gerekçe:

- Bongo Cat'in tuttuğu yer tam bu: hareketin kullanıcıya tepki olması.
- DEHB araştırması da bunu destekliyor: dikkati çeken şey sürekli yavaş hareket değil, hareketin aniden başlaması.
- Böylece hareket senin eşin olur, kendi kendine dikkat çekmez.

## 2. Sanat yönü: sıcak masal pikseli

| Karar | Değer | Neden |
|---|---|---|
| Kanvas | 48x48, ekranda tam sayı katı (2x = 96 px, 3x = 144 px) | Mevcut kod ve testler aynı kalır; boyut menüden seçilir (araştırma: ~128 px civarı) |
| Gövde | **Altı görünüm için tek ortak gövde** (2-2,5 kafa boyu, aynı kafa, aynı yüz) | Mevcut altı görünümün en büyük sorunu: kafa boyu ve yüz hepsinde farklı |
| Değişen | Yalnız şapka/saç, giysi rengi, alet | Tutarlılık + her görünüm kendi silüetiyle tanınır |
| Dış çizgi | 1 px, **koyu sıcak kahve** (#3b2a22 civarı), siyah değil, seçici çizgi yok | Her arka planda okunur, sert durmaz; masaüstünün rengi bilinemediği için seçici çizgi riskli |
| Palet | **Tek kilitli palet, 24-32 renk**, ton kaydırmalı rampalar, orta tonlarda doygunluk ≤ %60 | Çırak, aletler, kavanozlar ve balon aynı aileden; DEHB: sakin, uyarı rengi yok |
| Işık | Sol üstten tek ışık | Tüm görünümlerde aynı |
| Aday paletler | Lospec: Ekko-64 (24-32 renk alt küme), Glomzy 05, Resurrect 64 alt küme | Sıcak ve "cozy" etiketli; ilk çizimden sonra biri seçilip kilitlenir |

Araştırma 3'teki diğer yönler:

- Stardew benzeri: ortak gövde fikrini ondan aldık.
- 1-bit + vurgu rengi: fazla soğuk.
- Yumuşak boyalı: bu boyutta dağılıyor.

## 3. Hareket ve arayüz kuralları (test edilebilir)

1. **Boşta hareket:**
   - Genlik en çok 2 px, döngü en az 6 saniye.
   - 60 saniye etkileşim yoksa sabit duruş: yalnız arada bir göz kırpma.
2. **Aynı anda tek şey hareket eder.** Balon açıkken çırak yalnız bakar.
3. **Balon:**
   - 250-400 ms içinde belirip kaybolur. Kayma, zıplama ya da ses yok.
   - Süre bugünkü gibi metnin uzunluğuna göre ayarlanır.
   - Cevap beklemez: görmezden gelinen balon iz bırakmaz.
4. **Balonun görünümü:**
   - Parşömen rengi, 9 dilimli (9-slice) kenar ve çırağa bakan küçük bir kuyruk.
   - **Yazı tipi yumuşak kalsın.** Piksel yazı tiplerinin çoğunda ğ, ş, ı, İ yok ya da küçük boyutta okunmuyor.
5. **Durum bilgisi hiçbir zaman yalnız renkle verilmez:**
   - Mikrofon noktası şekilli kalır (bugünkü gibi).
   - Kavanozun dolması 3:1 kontrastla gösterilir.
6. **Kavanoz:**
   - Dolunca bir kez, 1 saniyeden kısa bir animasyon oynar.
   - Animasyon sessiz bir anda gelir: balon açıkken değil.
   - Sayı yok, seri yok, kayıp yok (bugünkü gibi).
7. **Yeni ayarlar:**
   - **Boyut** (2x/3x).
   - **Saydamlık** (%30-100).
   - **Hareketi azalt**: Windows'ta animasyonlar kapalıysa varsayılan olarak açık.
8. **Kaynak:**
   - Boştayken düşük kare hızı (bugün de öyle).
   - Pencere sınırını aşan çizim yok.
   - Saydam her piksel tıklamayı arkaya geçirir.

## 4. Grok Imagine ile asset listesi

Grok'un sınırları:

- **Gerçek piksel üretmiyor.** Çıktı 1K/2K, yumuşak bir görüntü. Gizpix (`pix_snap`, `speck_fix`, `apply_palette`) bunu ızgaraya oturtur.
- **Karakter kilidi yok.** Aynı karakteri tutmanın yolu: aynı referans görselleri (en çok 3) ve aynı tam açıklama.
- **Saydam arka plan yok.** Düz magenta (#FF00FF) zemin kullan. Yeşil zemin referansa sızıyor.
- **Videosu yalnız zamanlama için.** Kareler titrek çıkıyor, her kare yeniden ızgaraya oturtulmalı.

### İş akışı

1. **Pilot olarak yalnız büyücüyle başla:**
   - Ana çizim (master), ızgaraya oturtma.
   - Palet kilidi.
   - Uygulamada 3x boyutta deneme.
   - Beğenirsek diğerlerine geçeriz.
2. **Ortak gövde:** büyücü master'ı, diğer beş görünüm için referans olur. Prompt'ta "same body, same face, only outfit and tool change" denir.
3. **Animasyon:**
   - Grok'tan görünüm başına tek satırda 4 ana poz (key pose) istenir.
   - Aradaki kareleri biz kodla üretiriz: küçük kayma, nefes, göz kırpma.
4. **Kodla çizilenler:** balon, kavanoz, raf ve tezgâh kenarı. Bunlar pixart ya da Godot'nun kendi çizimiyle yapılır, Grok'a gerek yok. Böylece paletle birebir uyarlar.

### Senin çizdireceklerin

Her prompt'un başına bu **ortak başlık** gelir:

> Pixel art game sprite, cozy storybook style, chunky square pixels as if 48x48, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from upper left, no anti-aliasing, no gradients, no blur, no text. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.

| # | Asset | Prompt'un geri kalanı |
|---|---|---|
| 1 | **Büyücü master** (pilot) | Chibi apprentice wizard, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly face with simple dot eyes and small blush, purple pointed hat with a soft fold, purple robe, stirring a small black cauldron with green potion on the bench. Upper body visible above the bench. |
| 2 | Büyücü pozları | Using the reference character exactly (same colours, hat, face, proportions): one row of 4 equal square cells with thin magenta gaps. 1: stirring, spoon left. 2: stirring, spoon right. 3: looking up and listening, spoon still. 4: small nod, eyes closed, smiling. Same size and same bench position in every cell. |
| 3 | Büyücü soru/atma | Same character, one row of 4 cells: 1: tilting head with a curious look. 2: holding a tiny herb above the cauldron. 3: dropping it in. 4: small green puff from the cauldron. |
| 4-8 | Diğer beş görünümün master'ı | Same body, same face and proportions as the reference, only outfit and tool change: **blacksmith** (leather apron, small anvil with glowing iron), **healer** (white headscarf, stone mortar with green herbs), **scribe** (short chestnut hair, round thin glasses, open book and quill), **archer** (green hood, wooden target stump with arrows), **cook** (white chef hat, copper pot with orange soup). |
| 9-13 | Her biri için pozlar | 2 ve 3 numaralı prompt'lar, ilgili görünümün kendi aletiyle |
| 14 | Uygulama ikonu | The wizard apprentice's head and hat only, front view, centred, fills the frame, 1:1 (32x32 ve 256x256'ya indirilecek) |
| 15 | Tanıtım görseli (README) | Wide 16:9 cozy desk scene: a laptop screen corner, the apprentice on a small wooden shelf beside it, a row of colourful jars on the shelf, warm evening light. (Burada piksel kuralı gevşek olabilir.) |

Kavanoz, raf, balon ve tezgâh kenarı listede yok. Bunları **kodla** çizeceğim (bkz. iş akışı 4).

## 5. Lisans

- **xAI kullanım şartları:** çıktının sahibi kullanıcı. Ama marka kullanılırsa atıf isteniyor ve çıktılarla başka model eğitmeye dair bir madde olabilir. Araştırma ajanı güncel metne erişemedi (403), çizimden önce senin okuman gerekiyor.
- **Telif:** yalnız yapay zekâyla üretilmiş görsel telif kapsamına girmeyebilir. CC BY 4.0 belki yalnız bizim düzenlemelerimizi kapsar. `app/art/LICENSE.txt`'ye şu not eklenir: "AI-assisted (Grok Imagine), edited by Çırak contributors".

## 6. Bizde değişecek kod (asset'ler geldikten sonra)

- **Kare sayıları:**
  - working şeridi: 8 kare → 4 ana poz + kodla nefes ve kırpma.
  - listening, nodding, asking: aynı kalır.
  - toss: atma isteğe bağlı olduğu için kısalır.
- **Konuşmaya bağlı karıştırma:**
  - `speech_start` ile hızlanır, sessizlikte yavaşlar.
  - 60 saniye sonra sabit duruşa geçer.
- **Tezgâh ve raf:** tek sahne. `jars.gd` aynı mantıkla çalışır, yalnız yeri ve görünümü değişir.
- **Menüye eklenecekler:** Ayarlar → Boyut, Saydamlık, Hareketi azalt.
- **Balon:** 9 dilimli parşömen ve kuyruk.
- **Testler:** yeni kurallar mümkün olduğunca test edilecek. Örnekler: boşta 60 saniyeden sonra sabit kare; balon açıkken tek hareket.

## 7. Açık sorular

1. Sabit tezgâh mı, yoksa tezgâhsız bugünkü serbest figür mü? Öneri: tezgâh.
2. Kanvas 48 mi kalsın, yoksa 64'e mi çıkalım? 64 daha fazla yüz detayı verir ama kodda ve ölçülerde iş çıkarır. Öneri: 48.
3. "Atma" animasyonu tamamen kalksın mı, yoksa "hareketli çırak" ayarında mı kalsın? Öneri: ayarda kalsın.
