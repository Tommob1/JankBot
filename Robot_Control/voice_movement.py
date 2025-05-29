"""voice_movement.py – control the robot arm with voice keywords

Keywords recognised (case-insensitive):
    "left"   – pan servo1  −5° (min 10°)
    "right"  – pan servo1  +5° (max 170°)
    "up"     – tilt servo2 −5° (min 10°)
    "down"   – tilt servo2 +5° (max 170°)
    "stop"   – sends the current servo angles again (acts as a no-op / brake)

The script runs standalone.  It opens the same Arduino serial interface your
main GUI uses.

Run
----
    python voice_movement.py models/vosk-model-small-en-us-0.15

Requirements
------------
    pip install vosk sounddevice pyserial
"""
from __future__ import annotations
import argparse, json, queue, struct, sys, threading, time
from pathlib import Path

import sounddevice as sd
from vosk import Model, KaldiRecognizer
import serial, serial.tools.list_ports as list_ports

SAMPLE_RATE   = 16_000
BLOCK_LEN     = 8_000  # bytes
FORMAT        = "int16"
STEP_DEG      = 5       # degrees per voice step
SERVO_MIN     = 10
SERVO_MAX     = 170

# global servo angles
s1 = 90  # pan
s2 = 90  # tilt
s3 = 90  # (kept level)
SER_CLAMP = lambda v: max(SERVO_MIN, min(SERVO_MAX, v))

# ----------------------------------------------------------------------------
# Serial helpers
# ----------------------------------------------------------------------------

def find_arduino() -> str | None:
    for p in list_ports.comports():
        if "Arduino" in p.description or "usbmodem" in p.device:
            return p.device
    return None

def open_serial() -> serial.Serial | None:
    port = find_arduino()
    if not port:
        print("[Serial] Arduino not found", file=sys.stderr)
        return None
    try:
        return serial.Serial(port, 9600)
    except Exception as e:
        print("[Serial]", e, file=sys.stderr)
        return None

ser = open_serial()


def send_angles():
    global s1, s2, s3, ser
    s1c, s2c, s3c = map(SER_CLAMP, (s1, s2, s3))
    pkt = struct.pack("HHH", s1c, s2c, s3c)
    if ser:
        try:
            ser.write(pkt)
        except serial.SerialException:
            ser = open_serial()

# ----------------------------------------------------------------------------
# Voice recogniser thread
# ----------------------------------------------------------------------------

def voice_loop(model_path: Path):
    model = Model(str(model_path))
    rec   = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(False)
    q_audio: queue.Queue[bytes] = queue.Queue()

    def audio_cb(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        q_audio.put(bytes(indata))

    print("[Voice] model loaded – say 'up', 'down', 'left', 'right', or 'stop'")
    with sd.RawInputStream(samplerate=SAMPLE_RATE,
                           blocksize=BLOCK_LEN,
                           dtype=FORMAT,
                           channels=1,
                           callback=audio_cb):
        while True:
            data = q_audio.get()
            if rec.AcceptWaveform(data):
                cmd = json.loads(rec.Result()).get("text", "").lower()
                if cmd:
                    handle_command(cmd.split())

# ----------------------------------------------------------------------------
# Command handler
# ----------------------------------------------------------------------------

def handle_command(words: list[str]):
    global s1, s2
    for w in words:
        if w == "left":
            s1 -= STEP_DEG
            print("[CMD] left →", s1)
        elif w == "right":
            s1 += STEP_DEG
            print("[CMD] right →", s1)
        elif w == "up":
            s2 -= STEP_DEG
            print("[CMD] up →", s2)
        elif w == "down":
            s2 += STEP_DEG
            print("[CMD] down →", s2)
        elif w == "stop":
            print("[CMD] stop (hold position)")
    send_angles()

# ----------------------------------------------------------------------------
# Main entry-point
# ----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Voice-controlled robot pan/tilt")
    parser.add_argument("model", type=Path, help="Path to Vosk model directory")
    args = parser.parse_args()

    if not args.model.is_dir():
        sys.exit("Model directory not found")

    t = threading.Thread(target=voice_loop, args=(args.model,), daemon=True)
    t.start()

    try:
        while t.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[stopped]")
        sys.exit(0)

if __name__ == "__main__":
    main()
