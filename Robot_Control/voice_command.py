"""voice_command.py
Listen through the default microphone, recognise speech with Vosk,
and print partial and final transcripts to stdout in real time.

Usage
-----
    pip install vosk sounddevice

    # download a model once, e.g.
    wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip vosk-model-small-en-us-0.15.zip -d models/

    python voice_command.py models/vosk-model-small-en-us-0.15

Press Ctrl-C to stop recording.
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model

SAMPLE_RATE = 16_000  # Hz – most Vosk models expect 16-kHz mono
BLOCK_LEN = 8_000     # bytes (~0.25 s with int16)
FORMAT = "int16"      # 16-bit signed little-endian

# ── CLI ──────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Live speech-to-text with Vosk")
parser.add_argument(
    "model_dir",
    type=Path,
    help="Path to an unpacked Vosk model directory",
)
args = parser.parse_args()

if not args.model_dir.is_dir():
    sys.exit(f"Model directory '{args.model_dir}' not found.")

# ── Initialisation ───────────────────────────────────────────────────
print("Loading Vosk model…", file=sys.stderr)
model = Model(str(args.model_dir))
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)

audio_q: queue.Queue[bytes] = queue.Queue()

def audio_cb(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_q.put(bytes(indata))

# ── Main loop ────────────────────────────────────────────────────────
try:
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_LEN,
        dtype=FORMAT,
        channels=1,
        callback=audio_cb,
    ):
        print("[Listening – press Ctrl-C to stop]")
        while True:
            block = audio_q.get()
            if rec.AcceptWaveform(block):
                result = json.loads(rec.Result())
                if text := result.get("text"):
                    print(f"\n>> {text}\n")
            else:
                partial_json = json.loads(rec.PartialResult())
                partial = partial_json.get("partial", "")
                if partial:
                    # carriage return lets us overwrite the same line
                    print(f"\r{partial}        ", end="", flush=True)
except KeyboardInterrupt:
    print("\n[stopped]")
except Exception as exc:
    sys.exit(f"Error: {exc}")
