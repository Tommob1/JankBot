from __future__ import annotations
import argparse
import json
import queue
import sys
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model

SAMPLE_RATE = 16_000
BLOCK_LEN   = 8_000          # try 4096 or None if your device complains
FORMAT      = "int16"

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "models" / "vosk-model-small-en-us-0.15"

parser = argparse.ArgumentParser(description="Live speech-to-text with Vosk")
parser.add_argument(
    "model_dir",
    nargs="?",
    type=Path,
    default=DEFAULT_MODEL,
    help="Path to an unpacked Vosk model directory (defaults to ./models/vosk-model-small-en-us-0.15)",
)
parser.add_argument(
    "--device",
    help="Input device name or index for microphone (use --list-devices to see options)",
)
parser.add_argument(
    "--list-devices",
    action="store_true",
    help="List audio devices and exit",
)
args = parser.parse_args()

if args.list_devices:
    print(sd.query_devices())
    sys.exit(0)

model_dir = Path(args.model_dir).resolve()
print(f"[Vosk] using model: {model_dir}")
if not model_dir.is_dir():
    sys.exit(f"Model directory '{model_dir}' not found.")

# Configure input device if provided
if args.device is not None:
    try:
        # Allow passing either index or name
        dev = int(args.device) if args.device.isdigit() else args.device
        sd.default.device = (None, dev)  # (playback, recording)
    except Exception as e:
        sys.exit(f"Invalid --device '{args.device}': {e}")

print("[Audio] default devices:", sd.default.device)

print("Loading Vosk model…", file=sys.stderr)
model = Model(str(model_dir))
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)

audio_q: queue.Queue[bytes] = queue.Queue(maxsize=20)

def audio_cb(indata, frames, t, status):
    if status:
        # Common: Input overflow/underflow; not fatal
        print("[Audio][STATUS]", status, file=sys.stderr)
    try:
        audio_q.put_nowait(bytes(indata))
    except queue.Full:
        # Drop if we're lagging; recognizer will catch up next block
        pass

def open_stream():
    """Open the mic stream; try given BLOCK_LEN, fall back to None if needed."""
    try:
        return sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_LEN,
            dtype=FORMAT,
            channels=1,
            callback=audio_cb,
        )
    except Exception as e:
        print(f"[Audio] Could not open stream with blocksize={BLOCK_LEN}: {e}", file=sys.stderr)
        print("[Audio] Retrying with blocksize=None…", file=sys.stderr)
        return sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=None,
            dtype=FORMAT,
            channels=1,
            callback=audio_cb,
        )

try:
    with open_stream() as stream:
        print("[Listening – press Ctrl-C to stop]")
        print("[Audio] stream opened:", stream)
        while True:
            try:
                block = audio_q.get(timeout=2.0)
            except queue.Empty:
                print("[Audio] no audio blocks received (2s)… still waiting.")
                continue

            if rec.AcceptWaveform(block):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print(f"\n>> {text}\n")
            else:
                partial = json.loads(rec.PartialResult()).get("partial", "")
                if partial:
                    print(f"\r{partial}        ", end="", flush=True)
except KeyboardInterrupt:
    print("\n[stopped]")
except Exception as exc:
    sys.exit(f"Error: {exc}")