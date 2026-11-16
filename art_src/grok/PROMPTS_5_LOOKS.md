Bu görseller yapay zekâ (Grok Imagine) üretimidir; ai_free: false.

Kredi: AI-assisted (Grok Imagine), edited by Çırak contributors

# Çırak handout — 5 görünüm (demirci, şifacı, katip, okçu, aşçı)

Tarih: 2026-11-16 (Europe/Istanbul, UTC+3). Pilot (büyücü) referans: 2026-11-16-cirak-handout-pilot/teslim/wizard_master.png.

## Dosya başına deneme ve notlar

- teslim/blacksmith_master.png — deneme t2 / 4. çekiç ve parlayan demir net, tezgah referansla aynı; ten açık kaldı
    - reddedilen t1: çekiç/kızgın demir daha az net (ham-taslak/reddedilen/blacksmith_master_t1.jpg)
    - reddedilen t3: tezgah referanstan farklı (ham-taslak/reddedilen/blacksmith_master_t3.jpg)
    - reddedilen t4: çekiç/demir daha az net; ten yine açık (ham-taslak/reddedilen/blacksmith_master_t4.jpg)
- teslim/blacksmith_row1.png — deneme t4 / 4. (ek cümle): hafif panel kaldı, teslimde düzleştirildi
    - reddedilen t1: hücre arkasında açık panel (düz zemin değil) (ham-taslak/reddedilen/blacksmith_row1_t1.jpg)
    - reddedilen t2: panel (ham-taslak/reddedilen/blacksmith_row1_t2.jpg)
    - reddedilen t3: panel (ham-taslak/reddedilen/blacksmith_row1_t3.jpg)
- teslim/blacksmith_row2.png — deneme t1 / 2. el kalkık, demir örsün üstünde, kıvılcımlar; hafif panel düzleştirildi
    - reddedilen t2: pozlar daha zayıf (ek cümle) (ham-taslak/reddedilen/blacksmith_row2_t2.jpg)
- teslim/healer_master.png — deneme t2 / 2. taş havan + taş el, yeşil ot net
    - reddedilen t1: havan eli tahta çubuk gibi (ham-taslak/reddedilen/healer_master_t1.jpg)
- teslim/healer_row1.png — deneme t2 / 2. düz zemin, hücre 3 net yukarı bakıyor
    - reddedilen t1: hücre 3 yukarı bakmıyor (ham-taslak/reddedilen/healer_row1_t1.jpg)
- teslim/healer_row2.png — deneme t2 / 2. düz zemin; parmak kalkık, yaprak, ışıltı
    - reddedilen t1: panel (ham-taslak/reddedilen/healer_row2_t1.jpg)
- teslim/scribe_master.png — deneme t1 / 2. gözler gözlük arkasında görünür
    - reddedilen t2: daha dağınık, kravat eklenmiş (ham-taslak/reddedilen/scribe_master_t2.jpg)
- teslim/scribe_row1.png — deneme t4 / 4. (ek cümle): panel hâlâ var, en iyisi; teslimde düzleştirildi
    - reddedilen t1: güçlü panel (ham-taslak/reddedilen/scribe_row1_t1.jpg)
    - reddedilen t2: güçlü panel (ham-taslak/reddedilen/scribe_row1_t2.jpg)
    - reddedilen t3: güçlü panel (ham-taslak/reddedilen/scribe_row1_t3.jpg)
- teslim/scribe_row2.png — deneme t3 / 4. el yanakta, tüy hokkada, mürekkep yıldızı; panel teslimde düzleştirildi
    - reddedilen t1: panel (ham-taslak/reddedilen/scribe_row2_t1.jpg)
    - reddedilen t2: panel (ek cümle) (ham-taslak/reddedilen/scribe_row2_t2.jpg)
    - reddedilen t4: panel; NOT: düz prompt + yalnız master referansla gönderildi (ham-taslak/reddedilen/scribe_row2_t4.jpg)
- teslim/archer_master.png — deneme t2 / 2. hedef kütüğü + oklar, yay yok
    - reddedilen t1: fazladan yay eklenmiş (ham-taslak/reddedilen/archer_master_t1.jpg)
- teslim/archer_row1.png — deneme t1 / 2. düz zemin, pozlar doğru
    - reddedilen t2: panel (ham-taslak/reddedilen/archer_row1_t2.jpg)
- teslim/archer_row2.png — deneme t2 / 2. ok kütük üstünde, yapraklar
    - reddedilen t1: ok kütüğün üstünde net tutulmuyor (ham-taslak/reddedilen/archer_row2_t1.jpg)
- teslim/cook_master.png — deneme t2 / 2. tahta kaşık, bakır tencere, turuncu çorba
    - reddedilen t1: kaşık net değil (ham-taslak/reddedilen/cook_master_t1.jpg)
- teslim/cook_row1.png — deneme t3 / 4. düz zemin; hücre 3 yukarı bakış zayıf
    - reddedilen t1: panel (ham-taslak/reddedilen/cook_row1_t1.jpg)
    - reddedilen t2: panel (ham-taslak/reddedilen/cook_row1_t2.jpg)
    - reddedilen t4: panel (ek cümleye rağmen) (ham-taslak/reddedilen/cook_row1_t4.jpg)
- teslim/cook_row2.png — deneme t1 / 2. tencere üstünde baharat tutamı, hafif buhar
    - reddedilen t2: pembe buhar (anahtarlama riski) + göz kırpma (ham-taslak/reddedilen/cook_row2_t2.jpg)

## Promptlar (birebir gönderilen)

Master'lar: referans = pilot wizard_master.png, 1:1. Row1: referans = o görünümün seçilen master'ı, 16:9. Row2: referans = master + seçilen row1, 16:9 (istisna: scribe_row2 t4 yalnız master ile).
Bazı denemelerde sona eklenen ek cümle: "The whole image is one single flat magenta colour behind the characters, with no lighter panels, boxes or frames behind the cells." — kullanılan: blacksmith_row1 t4, blacksmith_row2 t2, cook_row1 t4, scribe_row1 t4, scribe_row2 t2

### blacksmith_master
```
Exactly the same style, body, face and proportions as the reference image; only the outfit and the tool change. Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, short dark curly hair, warm brown skin, leather apron over a cream shirt, a small anvil with a glowing orange iron bar on the bench. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### blacksmith_row1
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a small anvil with a glowing orange iron bar. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: hammering, hammer to the left. Cell 2: hammering, hammer to the right. Cell 3: looking up and listening, hammer resting, eyes open. Cell 4: a small nod, eyes closed, gentle smile. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: short dark curly hair, warm brown skin, leather apron over a cream shirt.
```

### blacksmith_row2
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a small anvil with a glowing orange iron bar. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: head tilted, curious, one hand raised a little as if asking a question. Cell 2: holding a small iron bar above the anvil. Cell 3: placing it on the anvil. Cell 4: a few small orange sparks rising, the character smiling. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: short dark curly hair, warm brown skin, leather apron over a cream shirt.
```

### healer_master
```
Exactly the same style, body, face and proportions as the reference image; only the outfit and the tool change. Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, long brown hair under a white headscarf, soft blue dress, a grey stone mortar with green herbs on the bench. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### healer_row1
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a grey stone mortar with green herbs. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: grinding, pestle to the left. Cell 2: grinding, pestle to the right. Cell 3: looking up and listening, pestle resting, eyes open. Cell 4: a small nod, eyes closed, gentle smile. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: long brown hair under a white headscarf, soft blue dress.
```

### healer_row2
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a grey stone mortar with green herbs. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: head tilted, curious, one hand raised a little as if asking a question. Cell 2: holding a leaf above the mortar. Cell 3: dropping it in. Cell 4: a small green sparkle rising, the character smiling. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: long brown hair under a white headscarf, soft blue dress.
```

### scribe_master
```
Exactly the same style, body, face and proportions as the reference image; only the outfit and the tool change. Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, short chestnut hair, thin round brass glasses, dark blue coat with a red collar, an open book and a white quill on the bench. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### scribe_row1
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and an open book and a white quill. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: writing, quill to the left. Cell 2: writing, quill to the right. Cell 3: looking up and listening, quill resting, eyes open. Cell 4: a small nod, eyes closed, gentle smile. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: short chestnut hair, thin round brass glasses, dark blue coat with a red collar, eyes clearly visible through the glasses.
```

### scribe_row2
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and an open book and a white quill. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: head tilted, curious, one hand raised a little as if asking a question. Cell 2: dipping the quill in a small ink pot beside the book. Cell 3: writing with the quill on the book. Cell 4: a tiny ink star rising, the character smiling. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: short chestnut hair, thin round brass glasses, dark blue coat with a red collar, eyes clearly visible through the glasses.
```

### archer_master
```
Exactly the same style, body, face and proportions as the reference image; only the outfit and the tool change. Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, green hood, brown hair, green tunic, a wooden target stump with arrows in it on the bench. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### archer_row1
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a wooden target stump with arrows in it. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: fletching an arrow, arrow to the left. Cell 2: fletching an arrow, arrow to the right. Cell 3: looking up and listening, arrow resting, eyes open. Cell 4: a small nod, eyes closed, gentle smile. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: green hood, brown hair, green tunic.
```

### archer_row2
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a wooden target stump with arrows in it. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: head tilted, curious, one hand raised a little as if asking a question. Cell 2: holding an arrow being fletched above the stump. Cell 3: pushing it into the stump. Cell 4: a few small leaves rising, the character smiling. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: green hood, brown hair, green tunic.
```

### cook_master
```
Exactly the same style, body, face and proportions as the reference image; only the outfit and the tool change. Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, white chef hat, white jacket, a copper pot of orange soup on the bench. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### cook_row1
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a copper pot of orange soup. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: stirring, spoon to the left. Cell 2: stirring, spoon to the right. Cell 3: looking up and listening, spoon resting, eyes open. Cell 4: a small nod, eyes closed, gentle smile. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: white chef hat, white jacket.
```

### cook_row2
```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and a copper pot of orange soup. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: head tilted, curious, one hand raised a little as if asking a question. Cell 2: holding a pinch of spice above the pot. Cell 3: dropping it in. Cell 4: warm steam rising, the character smiling. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background. Look: white chef hat, white jacket.
```

Deneme bazında tam kayıt (prompt + referans + asset sha256 + not): prompts.json, tries.json.

## Ne yapıldı (düzenleme)

- teslim/: JPG çıktısı PNG'ye çevrildi; kenara bağlı macenta-benzeri zemin (R>180, B>180, G<150; hücre arkasındaki açık paneller dahil) birebir #FF00FF yapıldı. Figür içindeki kapalı zemin cepleri (kenara bağlı olmayan) dokunulmadan bırakıldı (en çok demircide: kol–örs arası).
- Panel düzleştirme bir düzenlemedir: scribe_row1/row2 ve blacksmith_row1/row2'deki açık paneller ham görselde vardı, teslimde kaldırıldı. Ham hali ham-taslak/secilen-orijinal/.
- sprites/ (48x48): teslim PNG'den maske → piksel ızgarası tespiti (master pitch ≈9.6–10 px) → blok-medyan → 48x48. Tüm hücreler tezgaha göre ölçeklendi; tezgah alt-ortası x=24, y=47'ye sabitlendi (hücre kayması düzeltildi). Tezgah satırları (37–47) master'dan row hücrelerine kilitlendi. Pembe/kırmızı kenar halesi #3B2A22 kontura çevrildi. Görünüm başına ortak 24 renk palet (k-means; konturla en yakın renk #3B2A22'ye zorlandı). Alfa yalnız 0/255. 1 native piksellik delikler doldu, daha büyük zemin cepleri saydam.
- Göz rötuşu (hafif): kaynakta açık gözler tespit edilip 48px'e eşlendi; yeri koyu değilse 1x2 en koyu palet pikseli kondu (0–4 piksel/sprite). Kapalı göz hücreleri (row1 c4) atlandı.
- sheets/, palettes/, preview/ (4x png + gif + genel önizleme) bu sprite'lardan üretildi.

## Paletler

- blacksmith: #150D0D #251F24 #270F06 #34160A #3B2A22 #3D0D20 #441E0C #4A3F42 #542711 #673217 #695B5B #793D1D #8D4C25 #94837F #A35B2D #AE8456 #BC6933 #C43004 #D2AB7B #E68A4C #F0CD9D #F56705 #FAAC69 #FCBC20
- healer: #0E3C5F #111D38 #175986 #2779AC #281108 #3B2A22 #3C6F09 #3D180D #56270F #5A7B87 #5B4E47 #6B3416 #6BA412 #7E3F1B #867265 #934C21 #A59181 #A85927 #BF6B32 #C8B5A4 #E4D4C3 #E98B4D #FAF2E0 #FCB06B
- scribe: #0E111E #121E38 #1A2D50 #22151F #273E6B #2E1309 #3B180D #3B2A22 #4A2111 #5B2C14 #6C371B #7E4020 #801512 #8D4D26 #A35A2C #A67E56 #B66733 #B7291C #CF7F43 #D8AE7E #E89859 #EDC796 #FBAF6B #FBDEB2
- archer: #1A170A #1D3619 #2C5023 #301509 #3B2A22 #3E0E22 #3E1C0A #3F6629 #4C240E #557B2F #582B12 #633215 #6A8E36 #6F3A19 #7F441F #914F22 #9A795B #A55C29 #BA6C31 #D0803D #E7CE9C #E9974F #F8E9C2 #F9AF66
- cook: #2E1008 #3B2A22 #3E190E #52230E #613017 #624D46 #743C1D #792D0D #894721 #8D7D72 #9E5527 #A23E10 #B0632D #B1A297 #BB521F #C66D31 #CFC0B4 #D95102 #DE7E3A #E9DCCF #F1934E #F88E0D #FCB16B #FCF5E9

## Doğrulama (dogrulama.json)

- blacksmith: 9/9 sprite 48x48 RGBA, alfa 0/255, palet içi, kenara değmiyor, #3B2A22 var, tezgah satırları master ile birebir: EVET; palet 24 renk; teslim kenarları birebir #FF00FF: EVET; göz bulunan (master,r1c1-4,r2c1-4): 2,2,0,2,0,2,2,2,1
- healer: 9/9 sprite 48x48 RGBA, alfa 0/255, palet içi, kenara değmiyor, #3B2A22 var, tezgah satırları master ile birebir: EVET; palet 24 renk; teslim kenarları birebir #FF00FF: EVET; göz bulunan (master,r1c1-4,r2c1-4): 2,2,2,2,0,2,2,2,2
- scribe: 9/9 sprite 48x48 RGBA, alfa 0/255, palet içi, kenara değmiyor, #3B2A22 var, tezgah satırları master ile birebir: EVET; palet 24 renk; teslim kenarları birebir #FF00FF: EVET; göz bulunan (master,r1c1-4,r2c1-4): 2,2,2,2,0,2,2,2,2
- archer: 9/9 sprite 48x48 RGBA, alfa 0/255, palet içi, kenara değmiyor, #3B2A22 var, tezgah satırları master ile birebir: EVET; palet 24 renk; teslim kenarları birebir #FF00FF: EVET; göz bulunan (master,r1c1-4,r2c1-4): 2,2,1,2,0,2,2,2,2
- cook: 9/9 sprite 48x48 RGBA, alfa 0/255, palet içi, kenara değmiyor, #3B2A22 var, tezgah satırları master ile birebir: EVET; palet 24 renk; teslim kenarları birebir #FF00FF: EVET; göz bulunan (master,r1c1-4,r2c1-4): 2,1,1,1,0,2,2,1,2
- GENEL: ALL_OK = True
- Ham row'larda hücre içi tezgah kayması: yatay 4.5–9.2 px, dikey 1.1–7.0 px (kaynak piksel); temiz 48px sürümde tezgah sabitlemesiyle 0.

## Bilinen kusurlar

- Demirci: "warm brown skin" 4 master denemesinde de uygulanmadı; ten açık (referanstaki gibi). Gerekirse elle palet kaydırma ile düzeltilebilir.
- Katip: her iki row'da 4/4 denemede hücre arkası paneller çıktı; en iyi seçildi, paneller teslimde düzleştirildi (düzenleme). Görünüm (yuvarlak gözlük, dağınık saç, kırmızı/mavi) ünlü bir büyücü karakterine benzeyebilir — handout tanımından geliyor, risk olarak not.
- Katip 48px: gözlük çerçevesi bir gözle birleşiyor; gözler koyu nokta olarak görünüyor ama ince.
- Aşçı row1 c3: yukarı bakış zayıf.
- Göz tespiti eksik kalan açık-göz hücreleri (rötuş az/yok, gözler yine de çizimde var): blacksmith r1_c2 (0), r2_c4 (1); archer r1_c2 (1); cook r1_c1–c3 (1), r2_c3 (1).
- Hücreler arasında görünür ince macenta boşluk yok (model çizmedi); hücreler eşit çeyreklerden ayrıştırıldı.
- Kapalı zemin cepleri teslim PNG'de ham macenta tonunda (~235,0,240) kaldı (kenara bağlı değil); anahtarlamada toleranslı seçim gerekir. Temiz sprite'larda saydam.
- 48px'te yüzler küçük; ifade farkları (baş eğme, gülümseme) ince.
- Ham row'larda küçük hücre kayması var (yukarıda); temiz sürümde düzeltildi.

## Kullanılmayanlar

PixelLab, ücretli servis, internete yükleme, kimseye gönderme yok. Üretim: Grok Imagine (GenerateImage).
