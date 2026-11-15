"""Makes app/art/icon.ico for Cirak.exe from the apprentice's first listening frame.

  listener\\.venv\\Scripts\\python tools\\make_icon.py      # Godot from $GODOT

An .ico here is just a header plus PNG images (Windows Vista+), so no image library is needed.
"""
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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


def main():
    godot = os.environ.get("GODOT") or sys.exit("set GODOT to the Godot 4.7 executable")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([godot, "--headless", "--path", str(ROOT / "app"), "-s", "../tools/make_icon.gd", "--", tmp],
                       check=True)
        pngs = [(s, (Path(tmp) / f"icon_{s}.png").read_bytes()) for s in SIZES]
    out = ROOT / "app" / "art" / "icon.ico"
    out.write_bytes(pack(pngs))
    print(out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    assert pack([(256, b"x")])[:6] == b"\0\0\1\0\1\0" and pack([(256, b"x")])[6] == 0  # 256 is written as 0
    main()
