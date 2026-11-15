# Listener

Hears the user (local Whisper), asks the apprentice's questions (local Ollama), talks to the app on 127.0.0.1:47613.

Setup on a new PC:

1. Python 3.12 (`py -3.12 -m venv .venv`), then `.venvScriptspip install -r requirements.lock` (exact versions that work; `requirements.txt` is the loose list).
2. First run downloads the Whisper `small` model (~500 MB) into the Hugging Face cache; without internet that first transcription fails (see `listener.log`).
3. Install Ollama and run `ollama pull qwen2.5:3b` (~2 GB). Without it questions come from the built-in list.
4. Whisper uses the GPU only if CUDA 12 cuBLAS is found; otherwise it runs on the CPU (~2 s per 8 s of speech).

Tools: `python hearing.py` prints 10 s of mic levels; `python ../tools/fake_listener.py` plays the apprentice's scenes without a mic. Errors (never what you said) go to `listener.log`.

## Commands

Hold **Right Ctrl** while speaking (push-to-talk: works over music, no wake word), or start with
"Çırak, …" / "Apprentice, …" when it is quiet. Typing them in the text box works too.

- Media: next / previous / pause / play / volume up / down / mute ("sonraki şarkı", "duraklat", "sesi kıs")
- Apps: "Spotify'ı aç" / "open Discord". Only apps listed in `%LOCALAPPDATA%\Cirak\apps.json`
  (right-click → "Apps I may open...") can be opened; the file maps a spoken name to the app name.
- Claude Code (if installed): "Claude'a sor: …" answers in the bubble (no tools, nothing runs);
  "Claude'a iş ver: …" opens Claude Code with the task typed in, sent only when you press Enter.
  Only the words after the command are sent.

Files: `%LOCALAPPDATA%\Cirak\` holds `listener.log`, `apps.json`, `models\` (Whisper, ~460 MB, downloaded on first run) and `last_answer.txt`.
