# Local transcription + speaker diarization

Transcribes an audio file (m4a, mp3, wav, ...) locally using Whisper, and
labels each line with which speaker said it using pyannote.audio.

## Setup (already done in this project)

```
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requires `ffmpeg` (installed via `brew install ffmpeg`).

## One-time: Hugging Face token

pyannote's diarization models are gated behind a free license click-through:

1. Create an account at https://huggingface.co/join
2. Accept the terms at:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
3. Create a read token at https://huggingface.co/settings/tokens
4. Either export it (`export HF_TOKEN=hf_yourtokenhere`) or save it to
   `.hf_token` in the project root (git-ignored): `echo hf_yourtokenhere > .hf_token`

## Interactive command (`transcribe` from anywhere)

`bin/transcribe` is a wrapper that prompts for language, number of speakers,
and model size, then runs `transcribe.py` with the project's `.venv`.

Install it by symlinking it into a directory on your `PATH`:

```
chmod +x bin/transcribe
mkdir -p ~/.local/bin
ln -sf "$PWD/bin/transcribe" ~/.local/bin/transcribe
```

If `~/.local/bin` isn't on your `PATH`, add this to `~/.zshrc`:

```
export PATH="$HOME/.local/bin:$PATH"
```

Then, from any directory:

```
transcribe path/to/recording.m4a
```

The token is read from `HF_TOKEN`, or else from `.hf_token` in the project
root. Don't put the token in the script itself — it's tracked by git.

Tip: macOS voice-memo filenames can contain invisible characters; use tab
completion or drag the file into the terminal rather than typing the name.

## Usage (direct)

```
source .venv/bin/activate
python transcribe.py path/to/recording.m4a
```

Options:

- `--model {tiny,base,small,medium,large,large-v3}` — Whisper model size (default `small`). Bigger = more accurate, slower.
- `--language en` — force a language instead of auto-detecting.
- `--min-speakers N` / `--max-speakers N` — bound the number of speakers if known.
- `--output path.txt` — custom output path (default: `<input>.transcript.txt`).
- `--hf-token hf_...` — alternative to the `HF_TOKEN` env var.

Output is a text file with lines like:

```
[00:00:00 - 00:00:04] SPEAKER_00: Hey, how's it going?
[00:00:04 - 00:00:09] SPEAKER_01: Pretty good, thanks for asking.
```
