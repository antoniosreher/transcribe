#!/usr/bin/env python3
"""Transcribe an audio file with speaker diarization.

Usage:
    python transcribe.py path/to/audio.m4a
    python transcribe.py path/to/audio.m4a --model medium --min-speakers 2 --max-speakers 4

Requires a Hugging Face access token with access to the pyannote speaker
diarization models. Set it via the HF_TOKEN environment variable or --hf-token.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def convert_to_wav(input_path: Path) -> Path:
    tmp_wav = Path(tempfile.mkstemp(suffix=".wav")[1])
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(input_path),
            "-ac", "1", "-ar", "16000",
            str(tmp_wav),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return tmp_wav


def format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def assign_speaker(segment_start, segment_end, speaker_turns):
    best_speaker, best_overlap = None, 0.0
    for turn_start, turn_end, speaker in speaker_turns:
        overlap = min(segment_end, turn_end) - max(segment_start, turn_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker
    return best_speaker or "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_file", help="Path to the input audio file (.m4a, .mp3, .wav, ...)")
    parser.add_argument("--model", default="small",
                         choices=["tiny", "base", "small", "medium", "large", "large-v3"],
                         help="Whisper model size (default: small). Larger = more accurate, slower.")
    parser.add_argument("--language", default=None, help="Force a language code (e.g. 'en'). Default: auto-detect.")
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"),
                         help="Hugging Face access token (or set HF_TOKEN env var)")
    parser.add_argument("--min-speakers", type=int, default=None)
    parser.add_argument("--max-speakers", type=int, default=None)
    parser.add_argument("--output", default=None, help="Output .txt path (default: <input>.transcript.txt)")
    args = parser.parse_args()

    if not args.hf_token:
        sys.exit(
            "Error: no Hugging Face token provided. Set HF_TOKEN env var or pass --hf-token.\n"
            "Get one at https://huggingface.co/settings/tokens after accepting the model terms at\n"
            "https://huggingface.co/pyannote/speaker-diarization-3.1"
        )

    input_path = Path(args.audio_file).expanduser().resolve()
    if not input_path.exists():
        sys.exit(f"Error: file not found: {input_path}")

    output_path = Path(args.output) if args.output else input_path.parent / f"{input_path.name.rsplit('.', 1)[0]}.transcript.txt"

    print(f"Converting {input_path.name} to 16kHz mono WAV...")
    wav_path = convert_to_wav(input_path)

    try:
        import torch
        device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading Whisper model '{args.model}' (device={device})...")
        import whisper
        whisper_model = whisper.load_model(args.model, device=device if device != "mps" else "cpu")
        # Whisper's official repo doesn't support MPS reliably; CPU is safer, still fast for small/medium.

        print("Transcribing audio...")
        transcription = whisper_model.transcribe(
            str(wav_path),
            language=args.language,
            verbose=False,
        )
        segments = transcription["segments"]

        print("Loading speaker diarization pipeline (pyannote)...")
        from pyannote.audio import Pipeline
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=args.hf_token,
        )
        if device in ("cuda", "mps"):
            import torch as _torch
            diarization_pipeline.to(_torch.device(device))

        print("Running speaker diarization (this can take a while)...")
        diarization_kwargs = {}
        if args.min_speakers:
            diarization_kwargs["min_speakers"] = args.min_speakers
        if args.max_speakers:
            diarization_kwargs["max_speakers"] = args.max_speakers
        diarization = diarization_pipeline(str(wav_path), **diarization_kwargs)

        speaker_turns = [
            (turn.start, turn.end, speaker)
            for turn, _, speaker in diarization.speaker_diarization.itertracks(yield_label=True)
        ]

        print("Merging transcription with speaker labels...")
        labeled_segments = []
        for seg in segments:
            speaker = assign_speaker(seg["start"], seg["end"], speaker_turns)
            labeled_segments.append((seg["start"], seg["end"], speaker, seg["text"].strip()))

        # Merge consecutive segments from the same speaker into one turn.
        merged = []
        for start, end, speaker, text in labeled_segments:
            if merged and merged[-1][2] == speaker:
                prev_start, prev_end, prev_speaker, prev_text = merged[-1]
                merged[-1] = (prev_start, end, speaker, f"{prev_text} {text}")
            else:
                merged.append((start, end, speaker, text))

        lines = []
        for start, end, speaker, text in merged:
            lines.append(f"[{format_timestamp(start)} - {format_timestamp(end)}] {speaker}: {text}")

        output_text = "\n".join(lines)
        output_path.write_text(output_text + "\n")

        print("\n" + output_text)
        print(f"\nSaved transcript to {output_path}")

    finally:
        wav_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
