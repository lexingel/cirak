# Grok Imagine prompt'ları: "Çırağın tezgâhı"

## Her çizim için

- Kare oran (1:1) seç.
- En büyük çözünürlüğü seç.
- Çıktıyı yandaki **dosya adıyla** kaydet.
- **Ref:** satırında yazanları referans görsel olarak ekle.

Dosyaları şu klasöre koy, ben oradan alıp piksel ızgarasına oturturum:

```
D:\Claude\body_double\art_src\grok\
```

Her prompt için 2-4 deneme üret ve en iyisini seç. İstersen birkaçını da ver; ben de bakarım.

Bir çıktıyı şu durumlarda **at**:

- yumuşak geçişler ya da bulanıklık var
- zemin düz magenta değil
- yazı ya da imza çıkmış
- figür kesilmiş

---

## PİLOT: büyücü (önce yalnız bunlar)

### P1: büyücü ana çizimi → `wizard_master.png`

Ref: yok (istersen bugünkü büyücünün ekran görüntüsünü ekleyebilirsin).

```
Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice wizard, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, purple pointed hat with a soft fold, purple robe, stirring a small black iron cauldron with bright green potion that stands on the bench. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

### P2: çalışma ve dinleme pozları → `wizard_row1.png`

Ref: P1'in seçtiğin çıktısı.

```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hat, same face, same proportions, same workbench and cauldron. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: stirring the cauldron, spoon to the left. Cell 2: stirring, spoon to the right. Cell 3: looking up and listening, spoon resting, eyes open. Cell 4: a small nod, eyes closed, gentle smile. The character, bench and cauldron have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background.
```

### P3: soru ve malzeme atma → `wizard_row2.png`

Ref: P1 ve P2'nin seçtiğin çıktıları.

```
Pixel art sprite strip of the reference character, exactly the same character: same colours, same hat, same face, same proportions, same workbench and cauldron. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: head tilted, curious look, one hand raised a little as if asking a question. Cell 2: holding a tiny green herb above the cauldron. Cell 3: dropping the herb into the cauldron. Cell 4: a small soft green puff rising from the cauldron, the character smiling. Same size and same position in every cell. Solid flat magenta (#FF00FF) background.
```

Pilot bu üçü. Bana verince ben:

- ızgaraya oturtup paleti kilitlerim,
- uygulamada 3x boyutta gösteririm,
- tezgâhı ve kavanoz rafını kodla eklerim.

Beğenirsen aşağıdakilere geçeriz.

---

## SONRA: diğer beş görünüm

Her görünüm için üç çizim var: ana çizim, sonra 1. ve 2. satır.

**Ana çizim** → `<ad>_master.png`. Ref: `wizard_master.png`. Bu, ortak gövdeyi tutar.

```
Pixel art game sprite in exactly the same style, body, face and proportions as the reference character; only the outfit and the tool change. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice sitting behind the same small wooden workbench, three-quarter front view, [LOOK]. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.
```

**1. ve 2. satırlar** → `<ad>_row1.png`, `<ad>_row2.png`.

- P2 ve P3'ün aynısını kullan.
- Ref olarak o görünümün master'ını ekle.
- "cauldron" kelimesini o görünümün aletiyle, "herb" kelimesini o görünümün malzemesiyle değiştir (aşağıdaki tabloya bak).

| ad | [LOOK] | alet / malzeme |
|---|---|---|
| `blacksmith` | short dark curly hair, warm brown skin, leather apron over a cream shirt, hammering a glowing orange iron bar on a small anvil | anvil / a small iron bar, puff = orange sparks |
| `healer` | long brown hair under a white headscarf, soft blue dress, grinding green herbs in a grey stone mortar | mortar / a leaf, puff = a small green sparkle |
| `scribe` | short chestnut hair, thin round brass glasses, dark blue coat with a red collar, writing with a white quill in an open book | open book / a quill dip in an ink pot, puff = a tiny ink star |
| `archer` | green hood, brown hair, green tunic, fletching an arrow beside a wooden target stump with arrows in it | target stump / an arrow, puff = a few leaves |
| `cook` | white chef hat, white jacket, stirring a copper pot of orange soup | copper pot / a pinch of spice, puff = warm steam |

---

## Ek olarak (istersen)

### İkon → `icon.png`. Ref: `wizard_master.png`.

```
Pixel art icon of the reference wizard apprentice's head and hat only, front view, big friendly face, chunky square pixels as if 32x32, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. The head fills most of the frame, centered. Solid flat magenta (#FF00FF) background, 1:1.
```

### README görseli → `hero.png`, 16:9. Ref: `wizard_master.png`.

```
Cozy pixel art scene, 16:9: the corner of a desk at evening with a laptop screen glowing on the left, and on a small wooden shelf beside it the reference wizard apprentice stirring a cauldron, with a row of small colourful potion jars on the shelf behind. Warm lamp light, soft muted palette, chunky pixels, no text.
```

---

## Çizdirmenden önce

- **Lisans:** xAI'nin güncel kullanım şartlarını oku. Özellikle iki maddeye bak: çıktılarla başka model eğitme yasağı ve atıf.
- **Kodla çizeceklerim:** kavanoz, raf, balon ve tezgâh kenarı. Bunları Grok'tan isteme.
