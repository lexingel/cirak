"""Grok Imagine (or any generator) art -> real 48x48 apprentice frames.

    python tools/grok_import.py ROW.png [ROW2.png ...] --out DIR [--cells 4] [--colors 24] [--size 48]

Each input is one image on a flat magenta (#FF00FF) background: a single figure (master) or a row of
N cells. Steps, all local (Gizpix does the pixel work, it must be at D:\\Claude\\PixTools or $GIZPIX):
  1. magenta -> transparent (also the pink fringe the generator blurs into the edges)
  2. split into cells: on fully transparent columns, or N equal parts with --cells
  3. each cell: crop to the figure, pix_snap to real pixels, fit into SIZE x SIZE (bottom-centred, so the
     bench/feet line stays put), never upscaled
  4. one shared palette for every cell of every input (apply_palette auto --colors N), then speck_fix
Writes DIR/<input name>_<i>.png (one frame each), DIR/sheet.png (all frames, for review at 3x) and
prints a line per frame. Turning frames into the app's strips is a separate, deliberate copy.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

GIZPIX = Path(os.environ.get("GIZPIX", r"D:\Claude\PixTools")) / "gizpix.py"


def is_key(r: int, g: int, b: int) -> bool:
    """Magenta and its blurred fringe: red and blue both well above green."""
    return r > 150 and b > 150 and g < 0.6 * min(r, b)


def key_out(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and is_key(r, g, b):
                px[x, y] = (0, 0, 0, 0)
    return im


def split(im: Image.Image, cells: int) -> list:
    if cells:
        w = im.width // cells
        return [im.crop((i * w, 0, (i + 1) * w, im.height)) for i in range(cells)]
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
    return out


def gizpix(*args) -> str:
    r = subprocess.run([sys.executable, str(GIZPIX), *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"gizpix {args[0]} failed: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def fit(sprite: Image.Image, size: int) -> Image.Image:
    box = sprite.getbbox()
    if box:
        sprite = sprite.crop(box)
    if sprite.width > size or sprite.height > size:  # snapped a bit too fine: shrink, never blur
        k = min(size / sprite.width, size / sprite.height)
        sprite = sprite.resize((max(1, int(sprite.width * k)), max(1, int(sprite.height * k))), Image.NEAREST)
    canvas = Image.new("RGBA", (size, size))
    canvas.paste(sprite, ((size - sprite.width) // 2, size - sprite.height))
    return canvas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cells", type=int, default=0, help="equal cells per row (default: split on gaps)")
    ap.add_argument("--colors", type=int, default=24)
    ap.add_argument("--size", type=int, default=48)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for src in a.images:
            for i, cell in enumerate(split(key_out(Image.open(src)), a.cells)):
                raw, snapped = tmp / f"{src.stem}_{i}_raw.png", tmp / f"{src.stem}_{i}_snap.png"
                box = cell.getbbox()
                (cell.crop(box) if box else cell).save(raw)
                report = gizpix("pix_snap", raw, snapped)
                frames.append((f"{src.stem}_{i}", fit(Image.open(snapped).convert("RGBA"), a.size), report.splitlines()[-1:]))
        # one palette for everything: palette the whole sheet at once, then cut it back up
        sheet = Image.new("RGBA", (a.size * len(frames), a.size))
        for k, (_, f, _) in enumerate(frames):
            sheet.paste(f, (k * a.size, 0))
        sp = tmp / "sheet.png"
        sheet.save(sp)
        gizpix("apply_palette", "auto", sp, "--colors", a.colors, "--out", tmp / "pal")
        sheet = Image.open(tmp / "pal" / "sheet.png").convert("RGBA")
        for k, (name, _, report) in enumerate(frames):
            p = a.out / f"{name}.png"
            sheet.crop((k * a.size, 0, (k + 1) * a.size, a.size)).save(p)
            gizpix("speck_fix", p, p)
            print(name, *report)
    review = Image.new("RGBA", (a.size * len(frames) * 3, a.size * 3), (70, 60, 80, 255))
    for k, (name, _, _) in enumerate(frames):
        f = Image.open(a.out / f"{name}.png").resize((a.size * 3, a.size * 3), Image.NEAREST)
        review.alpha_composite(f, (k * a.size * 3, 0))
    review.save(a.out / "sheet.png")
    print("review:", a.out / "sheet.png")


if __name__ == "__main__":
    main()
