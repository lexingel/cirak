# Code signing policy

Windows releases of Çırak (`Cirak.exe` and `Cirak-<version>-setup.exe`) are built from this
repository by GitHub Actions ([.github/workflows/build.yml](.github/workflows/build.yml)) and
signed only there, from a `v*` tag.

Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by
[SignPath Foundation](https://signpath.org/). *(Application in progress: releases before the
first signed one are unsigned.)*

## Team roles

- Committers and reviewers: [lexingel](https://github.com/lexingel)
- Approvers (sign releases): [lexingel](https://github.com/lexingel)

Every team member uses multi-factor authentication on GitHub and SignPath.

## What gets signed

Only programs built from this repository: the Çırak app (`Cirak.exe`, a Godot export) and its
Inno Setup installer. Third-party files shipped inside the release (the embedded Python, its
packages, the Microsoft C++ runtime files) keep their own signatures or none; they are listed in
`LICENSES.txt` in each release.

## Privacy

Çırak does not send what you say anywhere: speech is turned into text on your PC. It connects to
other systems only in these cases:

- On first start it downloads the Whisper speech model from huggingface.co (nothing about you is sent).
- When you choose a question model in the menu, Ollama on your PC downloads it from ollama.com.
- When you say "ask Claude: …", only the words after the command go to Anthropic, through your
  own Claude Code login.
- "Get Ollama" in the menu opens ollama.com in your browser.

Nothing else leaves your PC, and there is no telemetry.
