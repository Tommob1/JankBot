from __future__ import annotations
import argparse
import json
import queue
import sys
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model

SAMPLE_RATE = 16_000
BLOCK_LEN = 8_000
FORMAT = "int16"

parser = argparse.ArgumentParser(description="Live speech-to-text with Vosk")
parser.add_argument(
    "model_dir",
    type=Path,
    help="Path to an unpacked Vosk model directory",
)
args = parser.parse_args()

if not args.model_dir.is_dir():
    sys.exit(f"Model directory '{args.model_dir}' not found.")

print("Loading Vosk model…", file=sys.stderr)
model = Model(str(args.model_dir))
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)

audio_q: queue.Queue[bytes] = queue.Queue()

def audio_cb(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_q.put(bytes(indata))

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
                    print(f"\r{partial}        ", end="", flush=True)
except KeyboardInterrupt:
    print("\n[stopped]")
except Exception as exc:
    sys.exit(f"Error: {exc}")
