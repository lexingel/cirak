"""Build the release folder and zip other people can run: dist/Cirak/ and dist/Cirak-<version>-win64.zip.

  listener\\.venv\\Scripts\\python tools\\build.py            # Godot from $GODOT, or --godot PATH
  listener\\.venv\\Scripts\\python tools\\build.py --no-zip

Run it with the listener venv's Python: packages are installed for that exact Python (3.12), which
must match the embeddable Python shipped in the zip. No Python on the target PC is needed.

dist/Cirak/
  Cirak.exe                 Godot export
  listener/*.py             the listener code
  listener/python/          python-3.12.10 embeddable (pythonw.exe), ._pth points at ../lib
  listener/lib/             faster-whisper, sounddevice, ... (no anthropic, no pytest)
  README.txt LICENSE LICENSES.txt ART-LICENSE.txt
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUT = DIST / "Cirak"
PY_VER = "3.12.10"
PY_ZIP = f"python-{PY_VER}-embed-amd64.zip"
PY_URL = f"https://www.python.org/ftp/python/{PY_VER}/{PY_ZIP}"
PY_SHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"  # MD5 matched python.org's page
CACHE = ROOT / "tools" / "cache"
SKIP = {"tests", "__pycache__", ".venv", ".pytest_cache", "listener.log"}

README = """Çırak - a tiny wizard apprentice who keeps you company while you work.

Start: double-click Cirak.exe. Windows may say "Windows protected your PC" (the app is not
signed): click "More info", then "Run anyway".

First start downloads the speech model (~460 MB) to %LOCALAPPDATA%\\Cirak\\models; the
apprentice works (typing) meanwhile. Everything you say is turned into text on this PC only.

- Click the apprentice to type, drag to move, right-click for the menu (microphone, language,
  how often it asks, which apps it may open).
- Hold Right Ctrl (or the key you pick in the menu) while speaking to give a command: "next song", "pause", "volume down",
  "open Spotify" (only apps on your list), "ask Claude: ..." (if Claude Code is installed).
  Turkish works too: "sonraki şarkı", "duraklat", "Spotify'ı aç", "Claude'a sor: ...".
- "Apps I may open..." lists a spoken name and the app name (or a full exe path) for each app.
- The command key is not seen while a window running as administrator is in front.
- What leaves this PC: only the words after "ask Claude" (to Anthropic, with your own Claude login),
  a "tell Claude" task (typed into your local Claude Code, sent when you press Enter) and the
  one-time model download. Nothing else you say does.
- Better questions (optional): install Ollama (ollama.com) and run `ollama pull qwen2.5:3b`.
  Without it the apprentice picks from a list of gentle questions.
- A GPU is optional (CUDA 12 + cuDNN 9 are used if installed); otherwise it runs on the CPU.

Files: settings in %APPDATA%\\Godot\\app_userdata\\Cirak, the rest in %LOCALAPPDATA%\\Cirak.
To remove: delete this folder and those two.
"""


def version() -> str:
    m = re.search(r'config/version="([^"]+)"', (ROOT / "app" / "project.godot").read_text(encoding="utf-8"))
    return m.group(1) if m else "0.1"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def embed_python(dest: Path) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    z = CACHE / PY_ZIP
    if not z.exists():
        print("downloading", PY_URL)
        urllib.request.urlretrieve(PY_URL, z)
    if sha256(z) != PY_SHA256:
        z.unlink()
        sys.exit(f"{PY_ZIP}: checksum mismatch, deleted it; run again")
    with zipfile.ZipFile(z) as f:
        f.extractall(dest)
    pth = next(dest.glob("python3*._pth"))
    # no "import site": packages from a Python the user installed must never leak in
    pth.write_text("python312.zip\n.\n..\n..\\lib\n", encoding="utf-8")
    # ctranslate2 (Whisper) and onnxruntime need the C++ runtime; a PC without the VC++ redistributable
    # would start the listener but never transcribe. Microsoft lets apps ship these next to the exe.
    for dll in ("msvcp140.dll", "msvcp140_1.dll"):
        shutil.copy2(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / dll, dest / dll)


def licenses(lib: Path) -> str:
    rows = []
    for meta in sorted(lib.glob("*.dist-info/METADATA")):
        text = meta.read_text(encoding="utf-8", errors="replace")
        head = text.split("\n\n", 1)[0]
        get = lambda k: (re.search(rf"^{k}: (.+)$", head, re.M) or [None, ""])[1].strip()
        lic = get("License-Expression") or get("License")
        if not lic or len(lic) > 60 or lic.lower().startswith("copyright"):  # numpy: first line of its licence text
            lic = ", ".join(c.split(" :: ")[-1] for c in re.findall(r"^Classifier: License :: (.+)$", head, re.M)) or lic[:60]
        rows.append(f"{get('Name')} {get('Version')}: {lic}")
    return ("Third-party software in listener/lib and listener/python\n\n" + "\n".join(rows) +
            "\n\nPython: PSF License (listener/python/LICENSE.txt)\n"
            "msvcp140*.dll: Microsoft Visual C++ Redistributable (redistributable files)\n"
            "av (PyAV) bundles FFmpeg built with GPL parts (x264, x265); its sources: github.com/PyAV-Org/pyav-ffmpeg\n"
            "Whisper 'small' model (downloaded on first run): MIT, Systran/faster-whisper-small\n"
            + GODOT_NOTICE)


GODOT_NOTICE = """
Godot Engine (Cirak.exe), MIT License:
Copyright (c) 2014-present Godot Engine contributors (see AUTHORS.md).
Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Godot's own third-party parts (FreeType, zlib, ...) are listed at godotengine.org/license.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--godot", default=os.environ.get("GODOT"), help="Godot 4.7 executable")
    ap.add_argument("--no-zip", action="store_true")
    o = ap.parse_args()
    if sys.version_info[:2] != (3, 12):
        sys.exit("run this with the listener venv's Python 3.12 (packages must match the shipped Python)")
    if not o.godot or not Path(o.godot).exists():
        sys.exit("set GODOT or pass --godot PATH to Godot_v4.7.2-stable_win64.exe")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "listener").mkdir(parents=True)

    print("exporting the app")
    subprocess.run([o.godot, "--headless", "--path", str(ROOT / "app"), "--export-release",
                    "Windows Desktop", str(OUT / "Cirak.exe")], check=True)
    if not (OUT / "Cirak.exe").exists():
        sys.exit("Godot export made no Cirak.exe (is the export preset there? is Cirak.exe running?)")

    src = ROOT / "listener"
    for p in src.iterdir():
        if p.suffix == ".py" and p.name not in SKIP:
            shutil.copy2(p, OUT / "listener" / p.name)

    print("embedding Python", PY_VER)
    embed_python(OUT / "listener" / "python")

    print("installing packages")
    lib = OUT / "listener" / "lib"
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--target", str(lib), "--only-binary", ":all:",
                    "--no-compile", "-r", str(src / "requirements.dist.txt"), "-c", str(src / "requirements.lock")],
                   check=True)
    shutil.rmtree(lib / "bin", ignore_errors=True)
    for junk in lib.glob("*.whl"):  # pip leaves an empty numpy wheel behind
        junk.unlink()

    print("smoke test: the shipped Python imports everything (no mic opened)")
    subprocess.run([str(OUT / "listener" / "python" / "python.exe"), "-c",  # paths come from the ._pth
                    "import faster_whisper, ctranslate2, onnxruntime, av, sounddevice, pycaw, websockets, keys"],
                   check=True)

    (OUT / "README.txt").write_text(README, encoding="utf-8")
    shutil.copy2(ROOT / "LICENSE", OUT / "LICENSE")
    shutil.copy2(ROOT / "app" / "art" / "LICENSE.txt", OUT / "ART-LICENSE.txt")  # drawings: CC BY 4.0
    (OUT / "LICENSES.txt").write_text(licenses(lib), encoding="utf-8")

    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"dist/Cirak: {size:.0f} MB")
    if not o.no_zip:
        z = DIST / f"Cirak-{version()}-win64"
        shutil.make_archive(str(z), "zip", DIST, "Cirak")
        print(f"{z.name}.zip: {Path(str(z) + '.zip').stat().st_size / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
