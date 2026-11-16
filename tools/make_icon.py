"""Makes app/art/icon.ico (Cirak.exe and the installer) from the Grok icon art_src/grok/icon.png.

  python tools/make_icon.py

The source is a ~28x28 pixel drawing upscaled to 1024 on magenta: key the magenta out (grok_import),
snap it back to real pixels (Gizpix pix_snap, at $GIZPIX or D:\\Claude\\PixTools), centre it on a
24x24 canvas, then 256 = 10x (+8 px margin), 48 = 2x, 32/16 = smooth downscales.
An .ico here is just a header plus PNG images (Windows Vista+).
"""
import io
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import grok_import  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ART = 24  # art pixels per side
SIZES = [256, 48, 32, 16]


def pack(pngs: list) -> bytes:
    """[(size, png bytes)] -> .ico bytes."""
    head = struct.pack("<HHH", 0, 1, len(pngs))
    offset = 6 + 16 * len(pngs)
    entries, data = b"", b""
    for size, png in pngs:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    return head + entries + data


def frames(src: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        keyed, snap = Path(tmp) / "keyed.png", Path(tmp) / "snap.png"
        grok_import.key_out(Image.open(src)).save(keyed)
        grok_import.gizpix("pix_snap", keyed, snap, "--cells", 28, 28, "--tol", 1)
        art = Image.open(snap).convert("RGBA")
    art = art.crop(art.getbbox())
    assert art.width <= ART and art.height <= ART, art.size
    small = Image.new("RGBA", (ART, ART))
    small.paste(art, ((ART - art.width) // 2, (ART - art.height) // 2))
    big = Image.new("RGBA", (256, 256))
    big.paste(small.resize((ART * 10, ART * 10), Image.NEAREST), (8, 8))
    return {256: big, 48: small.resize((48, 48), Image.NEAREST),
            32: big.resize((32, 32), Image.LANCZOS), 16: big.resize((16, 16), Image.LANCZOS)}


def main():
    pngs = []
    for size, img in frames(ROOT / "art_src" / "grok" / "icon.png").items():
        buf = io.BytesIO()
        img.save(buf, "PNG")
        pngs.append((size, buf.getvalue()))
    out = ROOT / "app" / "art" / "icon.ico"
    out.write_bytes(pack(pngs))
    print(out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    assert pack([(256, b"x")])[:6] == b"\0\0\1\0\1\0" and pack([(256, b"x")])[6] == 0  # 256 is written as 0
    main()
