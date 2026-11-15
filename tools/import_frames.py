"""Turn raw apprentice frames (Grok Imagine exports) into the strips the Godot app loads.

  python tools/import_frames.py            # art_in/<state>/*.png -> app/art/apprentice_<state>.png (+ art_in/preview.png)
  python tools/import_frames.py --cell 12  # source pixels per art pixel, if auto-detect guesses wrong
  python tools/import_frames.py --selftest

Per frame: the key colour (median of the border pixels, so Grok's off-cyan still works) becomes
transparent. One crop box is computed over ALL frames of ALL states, so the apprentice keeps the same
scale and spot in every state. Output: 48x48 cells, bottom-centred, nearest sampling, alpha on/off.
"""
import argparse, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

STATES = ["working", "listening", "nodding", "asking"]
SIZE = 48
MARGIN = 1          # free cells left/right/top so the outline is never cut
ROOT = Path(__file__).resolve().parent.parent
EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def load_frames(in_dir):
    """{state: [RGBA arrays]} for the state folders that exist and hold images."""
    out = {}
    for st in STATES:
        d = Path(in_dir) / st
        files = sorted(p for p in d.glob("*") if p.suffix.lower() in EXTS) if d.is_dir() else []
        if not files:
            print(f"warning: {d} missing or empty, skipping '{st}' (app keeps its placeholder)")
            continue
        out[st] = [np.array(Image.open(p).convert("RGBA")) for p in files]
    return out


def key_out(rgba, tol):
    """Pixels close to the border colour -> alpha 0."""
    rgb = rgba[..., :3].astype(np.int32)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    key = np.median(border, axis=0)
    far = np.sqrt(((rgb - key) ** 2).sum(-1)) > tol
    out = rgba.copy()
    out[..., 3] = np.where(far & (rgba[..., 3] >= 128), 255, 0)
    return out


def detect_cell(frames):
    """Source pixels per art pixel via perfectPixel's numpy-only grid finder, or None."""
    try:
        sys.path.insert(0, r"D:\Claude\perfectPixel\src")
        from perfect_pixel.perfect_pixel_noCV2 import detect_grid_scale
    except Exception:
        return None
    sizes = []
    for f in frames[:: max(1, len(frames) // 6)]:  # a handful is enough
        a = f[..., 3:4] / 255.0
        rgb = (f[..., :3] * a + 128 * (1 - a)).astype(np.uint8)
        try:
            gw, gh = detect_grid_scale(rgb)
        except Exception:
            gw = None
        if gw:
            sizes.append(f.shape[1] / gw)
    return float(np.median(sizes)) if sizes else None


def shared_box(frames, noise):
    """Union bbox of opaque pixels; rows/cols with fewer than `noise` pixels are ignored (video specks)."""
    m = np.zeros(frames[0].shape[:2], np.int32)
    for f in frames:
        m += f[..., 3] > 0
    m = m > 0
    cols = np.where(m.sum(0) >= noise)[0]
    rows = np.where(m.sum(1) >= noise)[0]
    if not len(cols) or not len(rows):
        sys.exit("no character found: every pixel matched the key colour (try a lower --tol)")
    return cols[0], rows[0], cols[-1] + 1, rows[-1] + 1


def build(in_dir, out_dir, tol=80, cell=None):
    states = load_frames(in_dir)
    if not states:
        print("nothing to import")
        return {}
    shapes = {f.shape for fr in states.values() for f in fr}
    if len(shapes) > 1:
        sys.exit(f"all frames must have the same size (export every video at one resolution), got {shapes}")
    states = {st: [key_out(f, tol) for f in fr] for st, fr in states.items()}
    every = [f for fr in states.values() for f in fr]

    x0, y0, x1, y1 = shared_box(every, noise=3)
    fit = SIZE - 2 * MARGIN
    need = max(x1 - x0, (y1 - y0) * fit / (SIZE - MARGIN)) / fit  # source px per output px to fit
    cell = cell or detect_cell(every)
    if cell and need / cell < 8:  # sane grid: art is at most 8x too big for 48 px
        step = cell * max(1, int(np.ceil(need / cell - 1e-6)))  # whole art pixels per output pixel
        print(f"pixel grid: {cell:.2f} src px per art px, step {step:.2f}")
    else:
        # ponytail: no usable grid, plain nearest resample at a fractional step; edges may jitter
        # by 1 px between frames. Fix with --cell N or by cleaning frames in Gizpix first.
        step = need
        print(f"no pixel grid found, fitting with step {step:.2f}")

    # grid anchored on the box's left/bottom edges (cell boundaries for clean art), bottom-centred
    pad = int(round((SIZE * step - (x1 - x0)) / step / 2))
    left = x0 - pad * step
    top = y1 - SIZE * step
    centers = (np.arange(SIZE) + 0.5) * step
    xs, ys = np.floor(left + centers).astype(int), np.floor(top + centers).astype(int)
    h, w = every[0].shape[:2]
    okx, oky = (xs >= 0) & (xs < w), (ys >= 0) & (ys < h)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    strips = {}
    for st, fr in states.items():
        strip = np.zeros((SIZE, SIZE * len(fr), 4), np.uint8)
        for i, f in enumerate(fr):
            cellimg = np.zeros((SIZE, SIZE, 4), np.uint8)
            cellimg[np.ix_(oky, okx)] = f[np.ix_(ys[oky], xs[okx])]
            strip[:, i * SIZE:(i + 1) * SIZE] = cellimg
        Image.fromarray(strip).save(out_dir / f"apprentice_{st}.png")
        strips[st] = strip
        print(f"{st}: {len(fr)} frames -> apprentice_{st}.png ({strip.shape[1]}x{SIZE})")

    # review sheet: strips stacked at 3x on a dark background
    S = 3
    pw = max(s.shape[1] for s in strips.values()) * S
    prev = Image.new("RGBA", (pw + 16, len(strips) * (SIZE * S + 8) + 8), (30, 28, 36, 255))
    for r, s in enumerate(strips.values()):
        im = Image.fromarray(s).resize((s.shape[1] * S, SIZE * S), Image.NEAREST)
        prev.alpha_composite(im, (8, 8 + r * (SIZE * S + 8)))
    prev.save(Path(in_dir) / "preview.png")  # next to the input, not app/art: it would end up inside the exe
    return strips


def selftest():
    K = 8  # art drawn at 8x, like a clean upscale
    rng = np.random.default_rng(1)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        n = {"working": 4, "listening": 2, "nodding": 3}  # 'asking' left out on purpose
        for st, cnt in n.items():
            (tmp / "in" / st).mkdir(parents=True)
            for i in range(cnt):
                img = np.zeros((60 * K, 60 * K, 3), np.uint8)
                img[:] = (0, 255, 255)
                img += rng.integers(0, 12, img.shape, dtype=np.uint8) * (img < 240)  # video-ish noise
                cx, cy = 10 + 3 * i + (st == "nodding") * 2, 20 + 2 * i  # art-pixel offset
                img[cy * K:(cy + 30) * K, cx * K:(cx + 20) * K] = (200, 40, 120)      # 20x30 body
                img[(cy + 30) * K:(cy + 34) * K, cx * K:(cx + 20) * K] = (20, 20, 20)  # 4-row base
                Image.fromarray(img).save(tmp / "in" / st / f"{i:02d}.png")
        strips = build(tmp / "in", tmp / "out", cell=K)
        assert set(strips) == set(n), strips.keys()
        sizes = set()
        for st, s in strips.items():
            assert s.shape == (SIZE, SIZE * n[st], 4), (st, s.shape)
            assert (tmp / "out" / f"apprentice_{st}.png").exists()
            for i in range(n[st]):
                f = s[:, i * SIZE:(i + 1) * SIZE]
                assert f[0, 0, 3] == 0 and f[0, -1, 3] == 0, "key colour not removed"
                assert set(np.unique(f[..., 3])) <= {0, 255}
                ys, xs = np.where(f[..., 3] > 0)
                sizes.add((xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
                assert (f[f[..., 3] > 0][:, :3] != (0, 255, 255)).any(-1).all(), "key pixels left"
        assert len(sizes) == 1, f"shape size differs between frames: {sizes}"
        assert (tmp / "in" / "preview.png").exists() and not (tmp / "out" / "preview.png").exists()
        assert not (tmp / "out" / "apprentice_asking.png").exists()
    print(f"selftest OK: 3 states, 9 frames, shape {sizes.pop()} in every frame")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="src", default=str(ROOT / "art_in"))
    p.add_argument("--out", default=str(ROOT / "app" / "art"))
    p.add_argument("--tol", type=float, default=80, help="RGB distance from the key colour that still counts as key")
    p.add_argument("--cell", type=float, help="source px per art px (skips auto-detect)")
    p.add_argument("--selftest", action="store_true")
    o = p.parse_args()
    selftest() if o.selftest else build(o.src, o.out, o.tol, o.cell)
