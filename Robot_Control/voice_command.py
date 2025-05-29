"""voice_command.py
Listen through the default microphone, recognise speech with Vosk,
and print the partial and final transcripts to stdout in real-time.

Requirements:
    pip install vosk sounddevice

You also need a local Vosk model.  Download one (≈50–150 MB) from
https://alphacephei.com/vosk/models and unzip it somewhere, e.g.:
    models/vosk-model-small-en-us-0.15

Then run:
    python voice_command.py models/vosk-model-small-en-us-0.15

Press Ctrl-C to stop recording.
"""

import argparse
import json
import queue
import sys
from pathlib import Path

import sounddevice as sd
from vosk import Model, KaldiRecognizer

# ---------------------------------------------------------------------------
# Audio + Vosk parameters
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16_000      # Hz – most Vosk models expect 16 kHz mono
BLOCK_LEN  = 8_000       # bytes of raw audio per callback (~0.25 s)
FORMAT     = "int16"     # 16-bit signed little-endian samples

# ---------------------------------------------------------------------------
# Parse command-line
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Live speech-to-text with Vosk")
parser.add_argument("model_dir", type=Path, help="Path to an unpacked Vosk model directory")
args = parser.parse_args()

if not args.model_dir.is_dir():
    sys.exit(f"Model directory '{args.model_dir}' not found or not a directory.")

# ---------------------------------------------------------------------------
# Initialise recogniser
# ---------------------------------------------------------------------------
print("Loading model… this can take a few seconds…", file=sys.stderr)
model = Model(str(args.model_dir))
rec   = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)  # include word-level timing in JSON result (optional)

# Thread-safe queue to hold audio blocks from the callback
q: queue.Queue[bytes] = queue.Queue()

def audio_callback(indata, frames, time, status):
    """sounddevice callback – push raw bytes into Queue."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# ---------------------------------------------------------------------------
# Open the input stream and start recognition loop
# ---------------------------------------------------------------------------
try:
    with sd.RawInputStream(samplerate=SAMPLE_RATE,
                           blocksize=BLOCK_LEN,
                           dtype=FORMAT,
                           channels=1,
                           callback=audio_callback):
        print("[Listening – press Ctrl-C to stop]")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                # Final result for this utterance
                result = json.loads(rec.Result())
                if text := result.get("text"):
                    print(f"\n>> {text}\n")
            else:
                # Partial result – overwrite the same line
                partial = json.loads(rec.Partial()).get("partial", "")
                if partial:
                    print(f"\r{partial}", end="", flush=True)
except KeyboardInterrupt:
    print("\n[stopped]")
except Exception as e:
    sys.exit(f"Error: {e}")

