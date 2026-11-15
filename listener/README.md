# Listener

Hears the user (local Whisper), asks the apprentice's questions (local Ollama), talks to the app on 127.0.0.1:47613.

Setup on a new PC:

1. Python 3.12 (`py -3.12 -m venv .venv`), then `.venv\Scripts\pip install -r requirements.lock` (exact versions that work; `requirements.txt` is the loose list).
2. First run downloads the Whisper `small` model (~460 MB) into `%LOCALAPPDATA%\Cirak\models` (the apprentice says so);
   without internet it says it can't load the model, and typing still works.
3. Optional: install Ollama; the app's menu then offers to download `qwen2.5:1.5b` (~1 GB, Apache 2.0;
   another model: put its name in `%LOCALAPPDATA%\Cirak\model.txt`). Without it questions come from the built-in list.
4. Whisper uses the GPU only if CUDA 12 cuBLAS is found; otherwise it runs on the CPU (~2 s per 8 s of speech).

Tools: `python hearing.py` prints 10 s of mic levels; `python ../tools/fake_listener.py` plays the apprentice's scenes without a mic. Errors (never what you said) go to `listener.log`.

## Commands

Hold the command key (**Right Ctrl** by default; right-click menu → "Command key" to pick another) while speaking (push-to-talk: works over music, no wake word), or start with
"Çırak, …" / "Apprentice, …" when it is quiet. Typing them in the text box works too.

- Media: next / previous / pause / play / volume up / down / mute / unmute ("sonraki şarkı", "duraklat",
  "sesi kıs", "sesi geri aç"). Pause and play press the same play/pause key.
- Apps: "Spotify'ı aç" / "open Discord". Only apps listed in `%LOCALAPPDATA%\Cirak\apps.json`
  (right-click → "Apps I may open...") can be opened; the file maps a spoken name to an app name
  or a full exe path. If Whisper keeps writing a name its own way ("ispotifay"), add that spelling
  as another key.
- Claude Code (if installed): "Claude'a sor: …" answers in the bubble (no tools, nothing runs);
  "Claude'a iş ver: …" opens Claude Code with the task typed in, sent only when you press Enter.
  Only the words after the command are sent.
- The command key is not seen while a window running as administrator is in front (a Windows rule).

What leaves this PC: only the words after "Claude'a sor" (to Anthropic, through your own Claude
login), the "Claude'a iş ver" task (typed into your local Claude Code, sent when you press Enter),
and the one-time Whisper model download from huggingface.co. What you say otherwise never does.

Files: `%LOCALAPPDATA%\Cirak\` holds `listener.log`, `apps.json`, `models\` (Whisper, ~460 MB, downloaded on first run) and `last_answer.txt`.
