"""Grok Imagine (or any generator) art -> real pixel apprentice frames and the app's strips.

    python tools/grok_import.py art_src/grok/wizard_master.png art_src/grok/wizard_row1.png \\
        art_src/grok/wizard_row2.png --out art_src/out/wizard [--app app/art] [--size 64] [--colors 24]

Inputs: one image on a flat magenta background each, a single figure (master) or a row of 4 cells
(split on the magenta columns between figures). Steps, all local:
  1. magenta (and the pink fringe JPEG leaves around it) -> transparent
  2. every cell is scaled so its bench is as wide as the first input's bench: one scale for all
  3. the bench legs are cut off under the table top; a 3 px front edge is drawn back in pixel art
  4. box-downscale so the tallest frame fits SIZE x SIZE, bench top on the same row in every frame
  5. one shared palette for every frame (Gizpix apply_palette auto --colors N, at D:\\Claude\\PixTools)
Writes DIR/<input>_<i>.png, DIR/sheet.png (3x review) and, with --app, the strips
apprentice_<state>.png that apprentice.gd loads (frame size = strip height).
The automatic grid guess (pix_snap) was unreliable on Grok rows, so this does not use it.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

GIZPIX = Path(os.environ.get("GIZPIX", r"D:\Claude\PixTools")) / "gizpix.py"
CUT = 0.07  # bench top thickness kept under the widest row, as a share of the cell height
EDGE = 3  # front edge drawn under the table top, art pixels
OUTLINE = (0x3B, 0x2A, 0x22, 255)
# which cells make which strip: (input stem suffix, cell) repeated to keep the app's frame counts/timing
STRIPS = {
    "working": [("row1", 0)] * 4 + [("row1", 1)] * 4,  # 8 frames @ 8 fps: one stir a second
    "listening": [("row1", 2)] * 2,
    "nodding": [("row1", 3), ("row1", 3), ("row1", 2)],
    "asking": [("row2", 0)] * 2,
    "toss": [("row2", 1)] * 3 + [("row2", 2)] * 3 + [("row2", 3)] * 4,
}


def is_key(r: int, g: int, b: int) -> bool:
    """Magenta and its fringe: red and blue both well above green."""
    return r > 150 and b > 80 and g < 0.6 * min(r, b)


def key_out(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and is_key(r, g, b):
                px[x, y] = (0, 0, 0, 0)
    return im


def split(im: Image.Image) -> list:
    """Figures separated by fully transparent columns."""
    alpha = im.getchannel("A")
    filled = [any(alpha.getpixel((x, y)) for y in range(0, im.height, 2)) for x in range(im.width)]
    out, start = [], None
    for x, f in enumerate(filled + [False]):
        if f and start is None:
            start = x
        elif not f and start is not None:
            if x - start > im.width // 20:  # a real figure, not a stray fringe column
                out.append(im.crop((start, 0, x, im.height)))
            start = None
    if len(out) > 1:  # two benches touching: cut a too-wide span at its thinnest middle column
        narrow = min(c.width for c in out)
        for i in reversed(range(len(out))):
            c = out[i]
            if c.width > 1.6 * narrow:
                a = c.getchannel("A")
                fill = [sum(1 for y in range(0, c.height, 2) if a.getpixel((x, y))) for x in range(c.width)]
                cut = min(range(c.width // 3, 2 * c.width // 3), key=fill.__getitem__)
                out[i:i + 1] = [c.crop((0, 0, cut, c.height)), c.crop((cut, 0, c.width, c.height))]
    return out


def bench(cell: Image.Image):
    """(cropped cell, bench top row, bench width, bench centre x): the bench is the widest part."""
    cell = cell.crop(cell.getbbox())
    alpha = cell.getchannel("A")
    widths = [sum(1 for x in range(cell.width) if alpha.getpixel((x, y))) for y in range(cell.height)]
    top = next(y for y, w in enumerate(widths) if w >= 0.9 * max(widths))
    row = [x for x in range(cell.width) if alpha.getpixel((x, top))]
    return cell, top, max(widths), (row[0] + row[-1]) / 2


def front_edge(frame: Image.Image) -> Image.Image:
    """Under the lowest row of the table top: EDGE rows of darker wood, outlined."""
    px = frame.load()
    bottom = max(y for y in range(frame.height) for x in range(frame.width) if px[x, y][3])
    cols = [x for x in range(frame.width) if px[x, bottom][3]]
    x0, x1 = min(cols), max(cols)
    wood = sorted((px[x, bottom - 2][:3] for x in cols if px[x, bottom - 2][3]), key=sum)
    dark = wood[len(wood) // 4] + (255,)  # a shade from the top's own wood, from the palette
    for y in range(bottom, min(frame.height, bottom + EDGE + 1)):
        for x in range(x0, x1 + 1):
            edge = y in (bottom, bottom + EDGE) or x in (x0, x1)
            px[x, y] = OUTLINE if edge else dark
    return frame


def gizpix(*args) -> str:
    r = subprocess.run([sys.executable, str(GIZPIX), *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"gizpix {args[0]} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def frames_from(images, size: int):
    cells = []  # (name, cell, top, bench width, bench centre)
    for src in images:
        found = split(key_out(Image.open(src)))
        cells += [(f"{src.stem}_{i}", *bench(c)) for i, c in enumerate(found)]
    ref = cells[0][3]
    norm = []
    for name, c, top, bw, cx in cells:  # same scale for all: bench as wide as the first input's
        k = ref / bw
        c = c.resize((round(c.width * k), round(c.height * k)), Image.LANCZOS)
        top = round(top * k)
        norm.append((name, c.crop((0, 0, c.width, int(top + CUT * c.height))), top, cx * k))
    above = max(top for _, _, top, _ in norm)
    below = max(c.height - top for _, c, top, _ in norm)
    wide = 2 * max(max(cx, c.width - cx) for _, c, _, cx in norm)  # bench centred, both sides fit
    k = min((size - 2 - EDGE) / (above + below), (size - 2) / wide)
    out = []
    for name, c, top, cx in norm:
        s = c.resize((max(1, round(c.width * k)), max(1, round(c.height * k))), Image.BOX)
        s.putalpha(s.getchannel("A").point(lambda v: 255 if v > 140 else 0))
        f = Image.new("RGBA", (size, size))
        f.alpha_composite(s, (size // 2 - round(cx * k), round(above * k) + 1 - round(top * k)))
        out.append((name, f))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--app", type=Path, help="also write the strips apprentice_<state>.png here")
    ap.add_argument("--colors", type=int, default=24)
    ap.add_argument("--size", type=int, default=64)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    frames = frames_from(a.images, a.size)
    with tempfile.TemporaryDirectory() as tmp:  # one palette for everything: the whole sheet at once
        sheet = Image.new("RGBA", (a.size * len(frames), a.size))
        for k, (_, f) in enumerate(frames):
            sheet.paste(f, (k * a.size, 0))
        sp = Path(tmp) / "sheet.png"
        sheet.save(sp)
        gizpix("apply_palette", "auto", sp, "--colors", a.colors, "--out", Path(tmp) / "pal")
        sheet = Image.open(Path(tmp) / "pal" / "sheet.png").convert("RGBA")
    done = {}
    for k, (name, _) in enumerate(frames):
        f = front_edge(sheet.crop((k * a.size, 0, (k + 1) * a.size, a.size)))
        f.save(a.out / f"{name}.png")
        done[name] = f
        print(name)
    review = Image.new("RGBA", (a.size * len(done) * 3, a.size * 3), (70, 60, 80, 255))
    for k, f in enumerate(done.values()):
        review.alpha_composite(f.resize((a.size * 3, a.size * 3), Image.NEAREST), (k * a.size * 3, 0))
    review.save(a.out / "sheet.png")
    print("review:", a.out / "sheet.png")
    if a.app:
        look = a.images[0].stem.rsplit("_", 1)[0]
        for state, cells in STRIPS.items():
            strip = Image.new("RGBA", (a.size * len(cells), a.size))
            for i, (row, c) in enumerate(cells):
                strip.paste(done[f"{look}_{row}_{c}"], (i * a.size, 0))
            strip.save(a.app / f"apprentice_{state}.png")
        print("strips:", a.app)


if __name__ == "__main__":
    main()
