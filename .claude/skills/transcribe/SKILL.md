---
name: transcribe
description: Transcribe an audio file (m4a, mp3, wav, ...) locally with Whisper and label each line by speaker using pyannote diarization. Use whenever the user asks to transcribe a recording, diarize speakers, or turn an audio file into a labeled text transcript in this project. Handles the Hugging Face token automatically — never ask the user to export HF_TOKEN or paste a token.
---

# Transcribe (Whisper + pyannote diarization)

Runs `transcribe.py` in this project to produce a speaker-labeled transcript
of an audio file. Output lines look like:

```
[00:00:00 - 00:00:04] SPEAKER_00: Hey, how's it going?
```

## Steps

1. **Identify the input file.** Use the file the user named. If they didn't
   name one, look for audio files (`*.m4a`, `*.mp3`, `*.wav`) in the project
   root that don't already have a matching `<name>.transcript.txt`, and ask
   if there's more than one plausible candidate.

2. **Resolve the Hugging Face token — do this automatically, never ask the
   user for it:**
   - If `HF_TOKEN` is already set in the environment, use it.
   - Otherwise read it from `.hf_token` in the project root (a plain-text
     file containing just the token). Export it as `HF_TOKEN` for the
     command in step 4, e.g. `export HF_TOKEN="$(cat .hf_token)"`.
   - If neither exists, tell the user to follow the "One-time: Hugging Face
     token" section of `README.md` — do not proceed without a token.
   - Never print, log, or echo the token value itself.

3. **Make sure the environment is ready.** Check for `.venv`. If it's
   missing, or `source .venv/bin/activate && python -c "import whisper,
   pyannote.audio"` fails (e.g. this is a fresh machine/Cowork VM that
   doesn't have the venv baked in), (re)create it before asking the user to
   wait through a long install:
   ```
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Also confirm `ffmpeg` is on PATH (`ffmpeg -version`); if missing, tell the
   user it's required (`brew install ffmpeg` on macOS) rather than installing
   system packages silently.

4. **Run the transcription:**
   ```
   source .venv/bin/activate
   python transcribe.py "<audio file>" [--model small|medium|large-v3] [--language en] [--min-speakers N] [--max-speakers N]
   ```
   Pick `--model` based on how the user described their needs (default
   `small` is fine unless they ask for higher accuracy or mention it's a
   long/important recording, in which case suggest `medium`). Pass
   `--min-speakers`/`--max-speakers` if the user mentions how many people
   are in the recording.

5. **Report the result:** the transcript is saved to
   `<input>.transcript.txt` next to the audio file. Show the user the output
   path, and the transcript content if it's short enough to be useful inline.

## Notes for running in Cowork / a fresh environment

- `.venv` and `.hf_token` are local, git-ignored artifacts — a fresh Cowork
  VM or clone of this project won't have them. Step 2 and step 3 above exist
  specifically to (re)create both rather than fail with "no token" or
  "module not found".
- If `.hf_token` truly isn't present anywhere (e.g. a brand new VM with no
  access to this machine's files), the token must be supplied via an `HF_TOKEN`
  environment variable/secret configured for that environment — this skill
  can't invent one.
