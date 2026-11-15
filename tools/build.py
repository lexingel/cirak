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
RCEDIT_URL = "https://github.com/electron/rcedit/releases/download/v2.0.0/rcedit-x64.exe"
RCEDIT_SHA256 = "3e7801db1a5edbec91b49a24a094aad776cb4515488ea5a4ca2289c400eade2a"  # unsigned upstream: pin it
SKIP = {"tests", "__pycache__", ".venv", ".pytest_cache", "listener.log"}

README = """Çırak - a tiny wizard apprentice who keeps you company while you work.

Start: run Cirak-<version>-setup.exe (no admin needed; it can start Çırak with Windows), or
unzip the zip and double-click Cirak.exe. Windows may say "Windows protected your PC" (the app is not
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
- Better questions (optional, free, stays on this PC): the right-click menu shows
  "Better questions: get Ollama..." (opens ollama.com) and then "download the model (~1 GB)".
  Without it the apprentice picks from a list of gentle questions.
- A GPU is optional (CUDA 12 + cuDNN 9 are used if installed); otherwise it runs on the CPU.

Files: settings in %APPDATA%\\Godot\\app_userdata\\Cirak, the rest in %LOCALAPPDATA%\\Cirak.
To remove: Settings > Apps > Çırak (setup), or delete this folder and those two (zip).
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
    with zipfile.ZipFile(cached(PY_URL, PY_SHA256)) as f:
        f.extractall(dest)
    pth = next(dest.glob("python3*._pth"))
    # no "import site": packages from a Python the user installed must never leak in
    pth.write_text("python312.zip\n.\n..\n..\\lib\n", encoding="utf-8")
    # ctranslate2 (Whisper) and onnxruntime need the C++ runtime; a PC without the VC++ redistributable
    # would start the listener but never transcribe. Microsoft lets apps ship these next to the exe.
    for dll in ("msvcp140.dll", "msvcp140_1.dll"):
        shutil.copy2(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / dll, dest / dll)


def cached(url: str, sha: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / url.rsplit("/", 1)[1]
    if not f.exists():
        print("downloading", url)
        urllib.request.urlretrieve(url, f)
    if sha256(f) != sha:
        f.unlink()
        sys.exit(f"{f.name}: checksum mismatch, deleted it; run again")
    return f


def stamp_exe(exe: Path) -> None:
    """The apprentice icon and name/version in the exe's properties (Godot's own otherwise)."""
    v = version()
    subprocess.run([str(cached(RCEDIT_URL, RCEDIT_SHA256)), str(exe), "--set-icon", str(ROOT / "app" / "art" / "icon.ico"),
                    "--set-file-version", v, "--set-product-version", v,
                    "--set-version-string", "ProductName", "Çırak",
                    "--set-version-string", "FileDescription", "Çırak - body-double companion",
                    "--set-version-string", "CompanyName", "Çırak contributors",
                    "--set-version-string", "LegalCopyright", "MIT (code), CC BY 4.0 (drawings)",
                    "--set-version-string", "OriginalFilename", "Cirak.exe"], check=True)


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
    # CI signs Cirak.exe between the two halves, so the zip and the installer carry the signed exe
    ap.add_argument("--folder-only", action="store_true", help="dist/Cirak only, no zip or installer")
    ap.add_argument("--package-only", action="store_true", help="zip + installer from an existing dist/Cirak")
    o = ap.parse_args()
    if not o.package_only:
        build_folder(o)
    if not o.folder_only:
        package(o.no_zip)


def build_folder(o):
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
    stamp_exe(OUT / "Cirak.exe")

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


def package(no_zip=False):
    if not (OUT / "Cirak.exe").exists():
        sys.exit("no dist/Cirak/Cirak.exe: build the folder first")
    if not no_zip:
        z = DIST / f"Cirak-{version()}-win64"
        shutil.make_archive(str(z), "zip", DIST, "Cirak")
        print(f"{z.name}.zip: {Path(str(z) + '.zip').stat().st_size / 1e6:.0f} MB")
    iscc = Path(os.environ.get("ISCC", Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Inno Setup 6/ISCC.exe"))
    if not iscc.exists():
        print("no Inno Setup (set ISCC): skipped the installer")
        return
    print("building the installer")
    subprocess.run([str(iscc), "/Q", f"/DAppVersion={version()}", f"/DSrc={OUT}", f"/DOut={DIST}",
                    str(ROOT / "tools" / "cirak.iss")], check=True)
    setup = DIST / f"Cirak-{version()}-setup.exe"
    print(f"{setup.name}: {setup.stat().st_size / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
