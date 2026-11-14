# Çırak: gereken çizimler (Grok Imagine için)

Kısa liste. Önce bir karakter görseli, sonra dört animasyon. Promptlar İngilizce, çünkü üretici İngilizceyi daha iyi takip ediyor. Kopyala, yapıştır.

## Genel kurallar

- **Oyundaki boyut:** 48x48 piksel. Karakter ve kazan birlikte bu kareye sığıyor. Ekranda 3 kat büyük görünüyor (144x144).
- **Arka plan rengi: düz camgöbeği `#00FFFF`.**
  - Neden yeşil değil: iksir yeşil. Yeşil arka planla birlikte silinir.
  - Neden magenta değil: şapka mor. Magentaya çok yakın, kenarları yenir.
  - Camgöbeği karakterde hiç yok. Sarı yıldız, siyah kazan, mor şapka ve yeşil iksir ondan uzak.
  - Grok tam `#00FFFF` vermese de olur. Araç arka plan rengini resmin kenarından kendisi okuyor.
- **Her görselde aynı kalacaklar:** kamera sabit, karakter ortada ve aynı boyutta, ayakları ve kazan aynı yerde. Arka planda başka nesne yok. Yazı yok. Gölge yok, zemin çizgisi yok.
- **Kare oran (1:1)** kullan. Bütün videoları aynı çözünürlükte indir. Araç farklı boyutlu kareleri kabul etmiyor.
- Balon, yazı ya da soru işareti **çizme**. Konuşma balonunu uygulama kendisi çiziyor.

## 1. Karakter görseli (referans)

Bu görsel karakterin görünüşünü sabitliyor. Bütün animasyonlar bu görselden başlıyor. Beğendiğin tek bir tane seç ve hep onu kullan.

```
Pixel art sprite of a tiny fantasy wizard apprentice, front three-quarter view, sitting behind a small black iron cauldron. Purple pointy hat with a single yellow star, small round face, simple robe. He holds a wooden stick in the cauldron, which is filled with bright green bubbling potion. Cute, cozy, calm mood. Chunky low-resolution pixel art, as if drawn on a 48x48 pixel canvas, limited palette of about 16 colours, clean 1-pixel dark outline around everything, no anti-aliasing, no blur, no gradients. Character and cauldron centred, small in the frame with empty space around, cauldron bottom near the lower edge. Flat solid pure cyan #00FFFF background, completely empty: no floor, no shadow, no other objects, no text.
```

## 2. Animasyonlar

Her hal için: referans görseli Grok'a ver, görselden video üret (image to video), sonra videodan kareleri çıkar (aşağıda nasıl yapılacağı yazıyor).

Her prompt'un sonuna aynı kuralları ekledim. Silme, Grok bunları her seferinde duymalı.

| Hal | Ne gösteriyor | Kare | Döngü | Hız |
|---|---|---|---|---|
| `working` | Kazanı karıştırıyor, bir kabarcık patlıyor | 6-8 | evet | 8 fps |
| `listening` | Başını kaldırıp kullanıcıya bakıyor, hafif nefes | 2 | evet | 2 fps |
| `nodding` | Küçük bir baş sallama | 3 | hayır, bir kez | 8 fps |
| `asking` | Elini kaldırıyor ya da başını yana eğiyor, meraklı | 2 | evet | 3 fps |

### working (çalışıyor, varsayılan hal)

6-8 kare, döngü. Çubukla kazanı bir tur karıştırıyor. Bir kabarcık yükselip patlıyor. Son kare ilk kareye yumuşakça bağlanmalı.

```
Using the reference image: the same wizard apprentice slowly stirs the green potion with the wooden stick in one smooth circle, eyes calm and focused on the cauldron. One small green bubble rises from the potion and pops. Gentle, quiet, seamless loop: the last moment matches the first. Same character, same pixel art style, chunky low-resolution pixel art, limited palette, 1-pixel dark outline, no anti-aliasing. Locked static camera, no zoom, no pan, character centred at the same size and position the whole time. Flat solid pure cyan #00FFFF background, empty, no shadow, no text.
```

### listening (dinliyor)

2 kare, döngü. Başını kazandan kaldırıp izleyiciye bakıyor. İki kare arasındaki tek fark küçük bir nefes: omuzlar ya da şapka 1 piksel iniyor, kalkıyor.

```
Using the reference image: the same wizard apprentice stops stirring, keeps the stick in the cauldron, lifts his head and looks straight at the viewer with friendly, attentive eyes. Then he just holds that pose and breathes softly, shoulders rising and falling a tiny bit. Calm, warm, no big movement. Same character, same pixel art style, chunky low-resolution pixel art, limited palette, 1-pixel dark outline, no anti-aliasing. Locked static camera, no zoom, no pan, character centred at the same size and position the whole time. Flat solid pure cyan #00FFFF background, empty, no shadow, no text.
```

Kare seçimi: başı kalkmış ve izleyiciye bakan iki kare al. Biri nefes alırken, biri verirken.

### nodding (baş sallama)

3 kare, bir kez oynuyor. Kullanıcı yazdıktan sonra "okudum" demek için. Kare 1: izleyiciye bakıyor. Kare 2: baş biraz aşağıda. Kare 3: yine bakıyor (kare 1'e çok yakın).

```
Using the reference image: the same wizard apprentice looks at the viewer and gives one small, kind nod, head dipping down slightly and coming back up, with a soft smile. One nod only, then still. Same character, same pixel art style, chunky low-resolution pixel art, limited palette, 1-pixel dark outline, no anti-aliasing. Locked static camera, no zoom, no pan, character centred at the same size and position the whole time. Flat solid pure cyan #00FFFF background, empty, no shadow, no text.
```

### asking (soruyor)

2 kare, döngü. Meraklı, hesap soran değil. Boştaki elini hafifçe kaldırıyor ya da başını yana eğiyor. İki kare arasındaki fark küçük olsun: el ya da baş 1-2 piksel oynuyor.

```
Using the reference image: the same wizard apprentice looks at the viewer with a curious, gentle expression, tilts his head slightly to one side and raises his free hand a little, as if about to ask a friendly question. He holds the pose with a tiny back-and-forth tilt. No speech bubble, no question mark, no text. Same character, same pixel art style, chunky low-resolution pixel art, limited palette, 1-pixel dark outline, no anti-aliasing. Locked static camera, no zoom, no pan, character centred at the same size and position the whole time. Flat solid pure cyan #00FFFF background, empty, no shadow, no text.
```

### İsteğe bağlı: malzeme atma (ucuzsa)

Ara sıra oynayacak ekstra bir hareket: kazana küçük bir malzeme (yaprak ya da kristal) atıyor. **Uygulama şu an bunu kullanmıyor.** Yaparsan `art_in/_extra/toss/` klasörüne koy, sonra bağlarız.

```
Using the reference image: the same wizard apprentice picks a tiny glowing leaf from his robe with his free hand and drops it into the cauldron; the green potion gives a small happy puff of sparkles, then he goes back to stirring. Same character, same pixel art style, chunky low-resolution pixel art, limited palette, 1-pixel dark outline, no anti-aliasing. Locked static camera, no zoom, no pan, character centred at the same size and position the whole time. Flat solid pure cyan #00FFFF background, empty, no shadow, no text.
```

## 3. Videodan karelere

1. Her hal için videoyu indir, örneğin `working.mp4`.
2. Kareleri çıkar. ffmpeg ile (her saniyeden 8 kare):

   ```
   ffmpeg -i working.mp4 -vf fps=8 art_in/working/f_%03d.png
   ```

3. Klasörde sadece gereken kareler kalsın, gerisini sil: `working` için 6-8, `listening` için 2, `nodding` için 3, `asking` için 2.
   - Döngülerde ilk ve son kare birbirine yakın olmalı.
   - Kamerası kaymış ya da karakteri bulanık kareleri atla.
4. Kareler **isim sırasıyla** oynuyor (`f_001`, `f_002`...). Silince numaralar atlasa da olur, sıra önemli.
5. Grok bazen video yerine birkaç görsel verir. O da olur: görselleri sırayla `01.png`, `02.png` diye adlandır.

Kareleri istersen önce Gizpix ile temizleyebilirsin (`align_frames`, `clean`). Şart değil.

## 4. Teslim listesi

Proje klasöründe `art_in/` altına koy:

```
art_in/
  working/     6-8 PNG
  listening/   2 PNG
  nodding/     3 PNG
  asking/      2 PNG
```

- [ ] Referans görsel (istersen `art_in/reference.png`, araç okumuyor, sadece saklamak için)
- [ ] `art_in/working/` 6-8 kare
- [ ] `art_in/listening/` 2 kare
- [ ] `art_in/nodding/` 3 kare
- [ ] `art_in/asking/` 2 kare
- [ ] Bütün kareler aynı çözünürlükte, arka plan camgöbeği

Dosya adları serbest, sadece sıralama doğru olsun. PNG, JPG ve WEBP olur.

Sonra şunu çalıştır:

```
python tools/import_frames.py
```

Araç `app/art/apprentice_<hal>.png` şeritlerini ve kontrol için `app/art/preview.png` dosyasını yazıyor. Önce `preview.png`'ye bak.

- Bir klasör eksikse araç o hali atlıyor. Uygulama o hal için şimdiki geçici çizimi kullanmaya devam ediyor.
- Karakter kenarlarda yenmişse ya da arka plandan parça kalmışsa: `--tol 60` (daha az siler) ya da `--tol 110` (daha çok siler) dene.
- Pikseller kaymış görünürse, kaynak görselde bir pikselin kaç ekran pikseli olduğunu ver: `--cell 12` gibi.
- Bütün hallerdeki karakter aynı boyutta kalıyor, çünkü araç tek bir kırpma kutusunu bütün karelere uyguluyor. Bu yüzden bir videoda karakter çok kayarsa, diğer hallerde de küçülür. Kamera sabit kalsın.
