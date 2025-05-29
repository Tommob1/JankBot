"""voice_movement.py  – continuous robot jog control via Vosk keywords

Public API
~~~~~~~~~~
    handle_command(words: list[str])
        Called by the GUI for each recognised utterance.
        Parses keywords and updates the global *direction state*.

Direction keywords (case-insensitive)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    left  / right   → continuous pan  (servo_pan)
    up    / down    → continuous tilt (servo_tilt)
    stop           → stop all motion (but resend angles once)

Optional extras
~~~~~~~~~~~~~~~
    open  → open claw
    close / grab → close claw

Motion model
~~~~~~~~~~~~
A background thread runs at 10 Hz.  At each tick it nudges the pan/tilt angles
by `STEP_DEG` · direction and sends the 5-value packet.  When both direction
axes are zero the loop exits and the thread stops until a new direction word
is received.

Standalone test
~~~~~~~~~~~~~~~
You can still run this file directly:

    python voice_movement.py models/vosk-model-small-en-us-0.15

Dependencies
~~~~~~~~~~~~
    pip install vosk sounddevice pyserial
"""
from __future__ import annotations
import argparse, json, queue, struct, sys, threading, time
from pathlib import Path

import serial, serial.tools.list_ports as list_ports
import sounddevice as sd
from vosk import KaldiRecognizer, Model

# ──────────────────────────────────────────────────────────────────────
# Servo state & constants
# ──────────────────────────────────────────────────────────────────────
SERVO_MIN, SERVO_MAX = 10, 170
STEP_DEG   = 5              # degrees per tick
TICK_HZ    = 10             # servo update frequency while moving

servo_pan   = 90  # horizontal axis
servo_tilt  = 90  # vertical axis
servo_level = 90  # unchanged

claw_grab_angles    = (170, 10)
claw_release_angles = (10, 170)
claw_grabbing = False

# current motion directions: -1, 0, +1
_dir_x = 0  # -1 = left, +1 = right
_dir_y = 0  # -1 = up,   +1 = down

_move_evt   = threading.Event()  # set while the mover thread should run
_mover_thr: threading.Thread | None = None

# ──────────────────────────────────────────────────────────────────────
# Serial helpers – identical packet format to GUI
# ──────────────────────────────────────────────────────────────────────

def _find_arduino() -> str | None:
    for p in list_ports.comports():
        if "Arduino" in p.description or "usbmodem" in p.device:
            return p.device
    return None

def _open_serial() -> serial.Serial | None:
    port = _find_arduino()
    if not port:
        print("[Serial] Arduino not found", file=sys.stderr)
        return None
    try:
        return serial.Serial(port, 9600)
    except Exception as e:
        print("[Serial]", e, file=sys.stderr)
        return None

ser = _open_serial()


def _clamp(v: int) -> int:
    return max(SERVO_MIN, min(SERVO_MAX, v))

def _send_angles():
    global ser, servo_pan, servo_tilt, servo_level, claw_grabbing
    pkt = struct.pack(
        "HHHHH",
        _clamp(servo_pan),
        _clamp(servo_tilt),
        _clamp(servo_level),
        *(claw_grab_angles if claw_grabbing else claw_release_angles),
    )
    if ser:
        try:
            ser.write(pkt)
        except serial.SerialException:
            ser = _open_serial()

# ──────────────────────────────────────────────────────────────────────
# Continuous mover thread
# ──────────────────────────────────────────────────────────────────────

def _mover_loop():
    global servo_pan, servo_tilt, _dir_x, _dir_y
    tick = 1 / TICK_HZ
    while _move_evt.is_set():
        if _dir_x == 0 and _dir_y == 0:
            _move_evt.clear()
            break
        servo_pan  += STEP_DEG * _dir_x
        servo_tilt += STEP_DEG * _dir_y
        _send_angles()
        time.sleep(tick)

# ──────────────────────────────────────────────────────────────────────
# Public function – call from GUI
# ──────────────────────────────────────────────────────────────────────

def handle_command(words: list[str]):
    """Parse keywords, update direction state, and manage mover thread."""
    global _dir_x, _dir_y, claw_grabbing, _mover_thr

    for w in words:
        w = w.lower()
        if w == "left":
            _dir_x = -1
        elif w == "right":
            _dir_x = 1
        elif w == "up":
            _dir_y = -1
        elif w == "down":
            _dir_y = 1
        elif w == "stop":
            _dir_x = _dir_y = 0
        elif w in {"open", "release"}:
            claw_grabbing = False
        elif w in {"close", "grab"}:
            claw_grabbing = True

    # always send a packet immediately so claw/open/stop act fast
    _send_angles()

    # manage mover thread
    if (_dir_x != 0 or _dir_y != 0) and not _move_evt.is_set():
        _move_evt.set()
        _mover_thr = threading.Thread(target=_mover_loop, daemon=True)
        _mover_thr.start()

# ──────────────────────────────────────────────────────────────────────
# Stand-alone recogniser (optional)
# ──────────────────────────────────────────────────────────────────────
VOICE_RATE, VOICE_BLOCK = 16_000, 8_000
_voice_evt = threading.Event()

def _voice_loop(model_dir: Path):
    mdl = Model(str(model_dir))
    rec = KaldiRecognizer(mdl, VOICE_RATE)
    q: queue.Queue[bytes] = queue.Queue()

    def cb(indata, frames, t, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    print("[Voice] say left/right/up/down/stop/open/close")
    with sd.RawInputStream(samplerate=VOICE_RATE, blocksize=VOICE_BLOCK,
                           dtype="int16", channels=1, callback=cb):
        while _voice_evt.is_set():
            data = q.get()
            if rec.AcceptWaveform(data):
                txt = json.loads(rec.Result()).get("text", "").strip()
                if txt:
                    print(">>", txt)
                    handle_command(txt.split())

# ---------------------------------------------------------------------
# CLI  –  python voice_movement.py model_dir
# ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser("Continuous voice jog controller")
    ap.add_argument("model", type=Path, help="Path to Vosk model directory")
    args = ap.parse_args()
    if not args.model.is_dir():
        sys.exit("Model directory not found")

    _voice_evt.set()
    t = threading.Thread(target=_voice_loop, args=(args.model,), daemon=True)
    t.start()

    try:
        while t.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[stopped]")
        _voice_evt.clear()
        t.join()

if __name__ == "__main__":
    main()
