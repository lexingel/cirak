# Handout for the image agent: Çırak apprentice art

You are making the art for **Çırak**, a small open-source Windows desktop companion. A tiny apprentice sits at a
workbench in the corner of the screen and keeps the user company while they work. The art is shown very small
(48x48 pixels, scaled 3x to about 144 px), next to the user's work. It must stay **calm, warm and readable**, and
must never catch the eye.

Your images are not the final sprites. A local tool keys out the background, snaps every image to a real pixel
grid and locks one shared palette. So what matters most is: **clean shapes, flat colours, a flat magenta
background, and the same character in every image.**

## 1. Rules for every image

- **Style:** pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up.
- **Outline:** 1-pixel **dark warm brown** outline (#3b2a22 or close to it). Never black.
- **Colour:** a soft, muted palette of about 24 colours with hue-shifted shading. No neon, and nothing more
  saturated than a warm storybook.
- **Light:** one light, from the upper left.
- **Never:** anti-aliasing, gradients, blur, glow, texture noise, text, signatures, watermarks, drop shadows, or
  a frame around the image.
- **Background:** solid flat magenta **#FF00FF** and nothing else: no floor, no shadow, no vignette.
- **Size:** square 1:1, highest resolution, figure centred, nothing cut off at the edges.
- **Character body (shared by all six looks):** chibi apprentice, 2.2 heads tall, sitting behind a small wooden
  workbench, three-quarter front view. Big friendly round face with simple dot eyes and a small blush. Only the
  upper body shows above the bench.
- **Every look uses the same body, the same face, the same proportions and the same bench.** Only the
  hair/hat, the outfit, and the tool on the bench change.

## 2. Animation rows

- Some deliverables are a **row of 4 equal square cells** in one image, separated by thin magenta gaps.
- Every cell must show **the same character at the same size and in the same position**: bench and tool fixed,
  only the pose changes.
- Always attach the chosen master image of that look as a reference, and repeat the look description word for
  word.

## 3. Deliverables (file names matter)

### Pilot first: wizard (deliver these three, then wait for feedback)

| File | Content | Reference |
|---|---|---|
| `wizard_master.png` | The wizard. Purple pointed hat with a soft fold, purple robe, stirring a small black iron cauldron of bright green potion that stands on the bench. | none |
| `wizard_row1.png` | Row of 4. 1: stirring, spoon to the left. 2: stirring, spoon to the right. 3: looking up and listening, spoon resting, eyes open. 4: a small nod, eyes closed, gentle smile. | wizard_master |
| `wizard_row2.png` | Row of 4. 1: head tilted, curious, one hand raised a little as if asking a question. 2: holding a tiny green herb above the cauldron. 3: dropping it in. 4: a small soft green puff rising, the character smiling. | wizard_master, wizard_row1 |

### After the pilot is approved: five more looks

Each look needs three files: `<name>_master.png`, then `<name>_row1.png` and `<name>_row2.png`. The rows use
the same four poses as the wizard's, with the tool and item below in place of the cauldron and herb.

Each master uses `wizard_master.png` as its reference, with the instruction: "exactly the same style, body,
face and proportions; only the outfit and the tool change".

| name | Look | Tool / item / puff |
|---|---|---|
| `blacksmith` | short dark curly hair, warm brown skin, leather apron over a cream shirt | a small anvil with a glowing orange iron bar / a small iron bar / orange sparks |
| `healer` | long brown hair under a white headscarf, soft blue dress | a grey stone mortar with green herbs / a leaf / a small green sparkle |
| `scribe` | short chestnut hair, thin round brass glasses, dark blue coat with a red collar | an open book and a white quill / the quill dipped in an ink pot / a tiny ink star |
| `archer` | green hood, brown hair, green tunic | a wooden target stump with arrows in it / an arrow being fletched / a few leaves |
| `cook` | white chef hat, white jacket | a copper pot of orange soup / a pinch of spice / warm steam |

### Extras

| File | Content |
|---|---|
| `icon.png` | Only the wizard's head and hat, front view, filling most of the frame, as if 32x32 pixels. Magenta background. |
| `hero.png` (16:9) | A cozy evening desk corner: a laptop screen glowing on the left, and the wizard on a small wooden shelf beside it, stirring, with a row of small colourful potion jars on the shelf. Warm lamp light. No text. The pixel rules can be a little looser here. |

**Do not make:** the jars, the shelf, the speech bubble or the bench edge on their own. These are drawn in code.

## 4. Prompt templates

**Master**

> Pixel art game sprite, cozy storybook style, chunky square pixels as if drawn at 48x48 and scaled up, 1-pixel dark warm brown outline (not black), soft muted palette of about 24 colours, hue-shifted shading, single light from the upper left, no anti-aliasing, no gradients, no blur, no text. A chibi apprentice, 2.2 heads tall, sitting behind a small wooden workbench, three-quarter front view, big friendly round face with simple dot eyes and a small blush, **[LOOK]**, **[TOOL ON THE BENCH]**. Only the upper body shows above the bench. Solid flat magenta (#FF00FF) background, nothing else, centered, 1:1.

**Row of 4**

> Pixel art sprite strip of the reference character, exactly the same character: same colours, same hair/hat, same face, same proportions, same workbench and **[TOOL]**. Chunky square pixels as if 48x48, 1-pixel dark warm brown outline, no anti-aliasing, no blur, no text. One row of 4 equal square cells separated by thin magenta gaps. Cell 1: **[POSE 1]**. Cell 2: **[POSE 2]**. Cell 3: **[POSE 3]**. Cell 4: **[POSE 4]**. The character, bench and tool have the same size and the same position in every cell. Solid flat magenta (#FF00FF) background.

## 5. Check every image before you hand it over

Make 2-4 tries per file and keep the best one. **Reject** an image if any of these is true:

- [ ] The background is not flat magenta (gradient, floor, shadow, pink haze).
- [ ] There is blur, soft edges, glow, or "painted" texture instead of square pixels.
- [ ] There is text, a logo, a signature or a frame.
- [ ] Any part of the figure is cut off by the edge.
- [ ] The face is not readable at a glance (hidden by hair or glasses, or the eyes are missing).
- [ ] It is a different character from the reference (face, proportions, bench or colours drift).
- [ ] A row has cells of different sizes, or the figure jumps around between cells.
- [ ] The outline is black or missing.

## 6. Hand-over

- Save the files with the names above and hand them over all together.
- For each file, write one line: which try it was, plus anything you noticed (for example "cell 3 hand slightly
  different").
- Keep the exact prompt text you used for each file. It goes into the project's credits as "AI-assisted (Grok
  Imagine), edited by Çırak contributors".
