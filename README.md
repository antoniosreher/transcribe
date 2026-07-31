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
4. Export it: `export HF_TOKEN=hf_yourtokenhere`

## Usage

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
