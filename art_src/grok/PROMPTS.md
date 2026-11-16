Bu görseller yapay zekâ (Grok Imagine) üretimidir; ai_free: false.
Credits: "AI-assisted (Grok Imagine), edited by Çırak contributors"

# Çırak handout pilotu: wizard (2026-11-16)

Kapsam: HANDOUT.md'deki pilot (wizard_master, wizard_row1, wizard_row2) ile icon.png ve hero.png (16:9).
Diğer 5 görünüm (blacksmith, healer, scribe, archer, cook) yapılmadı. Handout "pilotu teslim et, geri bildirim bekle" diyor.
Üretici: GenerateImage (Grok Imagine). Ücretli servis, PixelLab ve internete yükleme kullanılmadı.

## Klasörler
- teslim/: handout dosya adlarıyla seçilen ham denemeler (PNG). **Asıl teslim budur.** Son temizliği projenin yerel aracı yapar.
- sprites/: benim hattımla temizlenmiş 48x48 RGBA kareler (master + 8 hücre) ve ek olarak icon_32.png.
- sheets/: 48 px'lik şeritler: row1, row2 ve master+row1+row2 (9 kare).
- palettes/: ortak 24 renk (png/hex/json).
- preview/: 4x büyütmeler, GIF'ler ve genel-onizleme.png.
- ham-taslak/secilen-orijinal/: seçilen denemelerin üreticiden çıkan orijinal JPG'leri.
- ham-taslak/reddedilen/: reddedilen denemeler.
- prompts.json, meta.json, dogrulama.json, teslim_rapor.json

## Dosya başına bir satır (handout bölüm 6)
- wizard_master.png: 3 denemenin 2.'si (t2). Ortalı, temiz 3/4 görünüm, yüz okunaklı, kahverengi outline. Yanak allığı çok hafif. t1 arka planı daha soluk pembeydi, t3'te figür sağa kaymıştı ve masa eğikti.
- wizard_row1.png: 4 denemenin 4.'sü (t4). Hücre 3 net biçimde yukarı bakıyor, kaşık duruyor. Hücre 1/2 kaşık farkı küçük. Hücreler arası kayma yatayda ≤10 px (yaklaşık 1,5 sanat pikseli), dikeyde 6 px. Hücreler arasında görünür ince magenta boşluk yok.
  - t1 reddedildi: hücre kayması 23 px'e kadar çıkıyor, hücre 3 yukarı bakmıyor.
  - t2 reddedildi: hücre arkalarında açık pembe paneller vardı, arka plan düz değildi.
  - t3 reddedildi: hem yatay hem dikey kayma var.
- wizard_row2.png: 3 denemenin 1.'si (t1). Ot kazanın üstünde tutuluyor. Hücre 1'de el yanakta ve merakla bakıyor, hücre 4'te yeşil puf var. Kayma row1 ile aynı düzeyde (≤11 px yatay, 3 px dikey).
  - t2 ve t3 reddedildi: ot kazanın üstünde değil, elin yanında. t3'teki puf ayrıca soluk ve gri.
- icon.png: 2 denemenin 1.'si (t1). Nokta gözler master ile uyumlu, şapka kareyi dolduruyor. Yüz tam önden değil, hafif 3/4 duruyor. t2 reddedildi: gözlerde beyaz parlama vardı, master'dan farklıydı.
- hero.png: 3 denemenin 1.'si (t1). Büyücü dizüstünün yanındaki küçük rafta, kavanozlar da rafta, ışık sıcak. Üç denemenin hiçbirinde laptop ekranı görünmüyor, laptop arkadan çiziliyor ("screen glowing" tutmadı). t2 ve t3'te büyücü raf yerine masadaydı.

## Promptlar (birebir; handout bölüm 4 şablonlarından)
Not: Araç 4:1 oran desteklemiyor (1:1, 4:3, 3:4, 16:9, 9:16). Bu yüzden satırlar 16:9 (1280x720) üretildi. Her satır promptunun sonuna look tanımı kelimesi kelimesine eklendi (handout bölüm 2).

### wizard_master.png  (aspect 1:1, reference: none, tries: 3, chosen: t2)

```
Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, purple pointed hat with a soft fold, purple robe, stirring a small black iron cauldron of bright green potion that stands on the bench. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### wizard_row1.png  (aspect 16:9, reference: wizard_master (t2), tries: 4, chosen: t4)

```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and small black iron cauldron of bright green potion. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: stirring, spoon to the left. Cell 2: stirring, spoon to the right. Cell 3: looking up and listening, spoon resting, eyes open. Cell 4: a small nod, eyes closed, gentle smile. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: purple pointed hat with a soft fold, purple robe, stirring a small black iron cauldron of bright green potion that stands on the bench.
```

### wizard_row2.png  (aspect 16:9, reference: wizard_master (t2), wizard_row1 (t4), tries: 3, chosen: t1)

```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and small black iron cauldron of bright green potion. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: head tilted, curious, one hand raised a little as if asking a question. Cell 2: holding a tiny green herb above the cauldron. Cell 3: dropping it in. Cell 4: a small soft green puff rising, the character smiling. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: purple pointed hat with a soft fold, purple robe, stirring a small black iron cauldron of bright green potion that stands on the bench.
```

### icon.png  (aspect 1:1, reference: wizard_master (t2), tries: 2, chosen: t1)

```
Pixel art game icon of the reference character, exactly the same character: same colours, same purple pointed hat with a soft fold, same brown hair, same face. Only the wizard's head and hat, front view, filling most of the frame, chunky square pixels as if drawn at 32x32 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette, hue-shifted shading, single light from the upper left, big friendly round face with simple dot eyes and a small blush, no anti-aliasing, no gradients, no blur, no text, no frame. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### hero.png  (aspect 16:9, reference: wizard_master (t2), tries: 3, chosen: t1)

```
Pixel art scene, cozy storybook style, chunky square pixels, dark warm brown outlines (not black), soft muted palette with hue-shifted shading, no text. A cozy evening desk corner: a laptop screen glowing on the left, and the reference character (exactly the same chibi wizard apprentice: purple pointed hat with a soft fold, purple robe, brown hair, big round face with dot eyes and a small blush) on a small wooden shelf beside it, stirring a small black iron cauldron of bright green potion, with a row of small colourful potion jars on the shelf. Warm lamp light. No text, no logo, no watermark, no frame. 16:9.
```

## teslim/ üzerinde yapılan tek işlem
- Üretici JPG veriyor. Dosyalar PNG'ye çevrildi.
- Üretici tam #FF00FF vermiyor, düz ama sıcak pembe veriyor: master (241,3,131), row1 (235,0,120), row2 (234,0,115), icon (235,0,119).
- Kenarla bağlantılı arka plan bölgesi (ham arka plana uzaklık < 60) birebir #FF00FF yapıldı. Figür piksellerine dokunulmadı.
- hero.png'de magenta yok, yalnız PNG'ye çevrildi.
- Orijinaller ham-taslak/secilen-orijinal/ altında.

## Temizleme hattı (sprites/)
1. Gerçek piksel ızgarası:
   - master: kenar profilinden 11,76 px (ızgaraya oturtulmuş figür yaklaşık 72 px boyunda, yani gerçekten 48x48 değil).
   - satırlar: ızgara tespiti zayıftı (4,8–5,7 arası dalgalandı). Adım, masa genişliği master'a eşitlenerek türetildi: 5,35–5,44 px.
   - icon: 27 px.
2. Blok ortancasıyla yerel ızgaraya indirgendi, ardından nearest-neighbor ile 48x48'e küçültüldü.
3. Ortak ölçek: masa genişliği 32 px. Masanın alt orta noktası her karede aynı yere (x=24, alt satır 46) sabitlendi.
4. Kaynaktaki hücre kaymaları bu sabitlemeyle sıfırlandı. Masa satırları (37–47) master'dan kopyalanarak kilitlendi.
5. JPEG'in pembe arka plan hâlesi (kenar piksellerinde pembe ya da kırmızımsı) outline rengi #3B2A22'ye çevrildi.
6. Ortak palet: 24 renk, k-means. Outline #3B2A22 sabit tutuldu.
7. Magenta alfa ile ayrıldı: alfa yalnız 0 ya da 255.
8. 4x önizlemeler ve GIF'ler hazırlandı.

Palet: #120D0C #1F1921 #2B6407 #301509 #301644 #3B2A22 #3F215F #431D10 #4A8F0D #4E4849 #562F7A #572C14 #6C3A1B #6E3C91 #6FAC1C #726768 #7F4721 #8F53AF #995727 #A1D72D #B16931 #DB8648 #F8EAD8 #F9AE69

## Doğrulama (dogrulama.json): ALL_OK = True
- sprites: 9 kare 48x48, icon_32 32x32. Hepsi RGBA; alfa yalnız 0/255; tüm renkler ortak palette; kenara değen kare yok; hepsinde #3B2A22 outline var.
- Toplam palet 24 renk (≤24). Paletin #FF00FF'ye en yakın rengi 275 uzaklıkta, pembe hâle rengi kalmadı.
- Masa satırları 37–47 bütün satır hücrelerinde master ile birebir aynı: True.
- teslim: dört magenta görselin köşeleri ve kenarları birebir #FF00FF. hero 1280x720 (16:9).
- Ham satırlarda hücre kayması (eşit çeyreğe göre x ofseti):
  - row1: [19, 15, 10, 9], alt y: [562, 563, 566, 568]
  - row2: [20, 16, 10, 9], alt y: [571, 571, 572, 574]

## Bilinen kusurlar
- Arka plan: üretici tam #FF00FF vermiyor (sıcak pembe, ama düz). teslim'de kenarla bağlantılı bölge #FF00FF'ye çekildi; figür kenarlarında JPEG'den kalan pembe hâle duruyor. Yerel araç ham pembeyi değil #FF00FF'yi anahtarlayacaksa bu önemli.
- Satır formatı: 4 kare hücre tek 16:9 görselde; hücreler arasında görünür ince magenta boşluk yok. Hücreler eşit genişlikte (291–296 px), ama 320 px'lik eşit çeyreklere tam oturmuyor. Figür soldan sağa 9–20 px kayıyor (yaklaşık 1,5 sanat pikseli). 4 denemede de aynı eğilim vardı; temizlenmiş sürümde düzeltildi.
- 48x48'de yüz: gözler 1 piksele iniyor. Master'ın temiz sürümünde bir göz kayboluyor ya da göz kırpıyor gibi görünüyor. Allık palette ayrı renk olarak kalmadı, ten rengine karıştı. Handout'un "face readable at a glance" şartı ham görsellerde sağlanıyor, 48 px temiz sürümde zayıf. Gerekirse göz/allık rötuşu yapılabilir.
- Row1 hücre 1 ve 2: kaşığın sol/sağ farkı küçük, karıştırma döngüsü az hareketli.
- Row2 hücre 3: 48 px'de ot, kazandaki yeşille karışıyor.
- hero: laptop ekranı görünmüyor; bazı kavanozların rengi doygun.
- Ham görsellerin "piksel"leri tam kare ve keskin değil. JPEG ve ölçekleme yüzünden hafif yumuşaklık var. Kesin blur yok, ama satırlarda ızgara zayıf.
