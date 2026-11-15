# Listener

Hears the user (local Whisper), asks the apprentice's questions (local Ollama), talks to the app on 127.0.0.1:47613.

Setup on a new PC:

1. `python -m venv .venv` and `.venv\Scripts\pip install -r requirements.lock` (exact versions that work; `requirements.txt` is the loose list).
2. First run downloads the Whisper `small` model (~500 MB) into the Hugging Face cache; without internet that first transcription fails (see `listener.log`).
3. Install Ollama and run `ollama pull qwen2.5:3b` (~2 GB). Without it questions come from the built-in list.
4. Whisper uses the GPU only if CUDA 12 cuBLAS is found; otherwise it runs on the CPU (~2 s per 8 s of speech).

Tools: `python hearing.py` prints 10 s of mic levels; `python ../tools/fake_listener.py` plays the apprentice's scenes without a mic. Errors (never what you said) go to `listener.log`.
