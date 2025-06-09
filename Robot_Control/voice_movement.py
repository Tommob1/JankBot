"""voice_movement.py  – continuous jog + reset + refined hello

✅ NEW BEHAVIOUR
----------------
* **hello**
    1. Raises the arm (servo 2) and wrist (servo 3) fully up.
    2. **Opens** the claw (release grip) while waving.
    3. Pans ±WAVE_AMPL at WAVE_HZ for WAVE_DURATION seconds.
    4. Returns pan to its original heading; wrist/tilt remain up.

* The module now exports a set `COMMAND_WORDS` so upstream code can
  filter recognised text and print **only real commands**.
  (In your GUI’s `voice_worker`, just keep words that appear in that set
  before printing or calling `handle_command`.)

Other keywords unchanged: left / right / up / down / stop / open / close / grab / release / reset.

Speed‑tuning constants live at the top.
"""

from __future__ import annotations
import argparse, json, queue, struct, sys, threading, time
from pathlib import Path
import serial, serial.tools.list_ports as list_ports
import sounddevice as sd
from vosk import KaldiRecognizer, Model

# ──────────────────────────────────────────────────────────────────────
# Command vocabulary (exported)
# ──────────────────────────────────────────────────────────────────────
COMMAND_WORDS = {
    "left", "right", "up", "down", "stop",
    "open", "release", "close", "grab",
    "reset", "hello",
}

# ──────────────────────────────────────────────────────────────────────
# Tuning constants
# ──────────────────────────────────────────────────────────────────────
SERVO_MIN, SERVO_MAX = 10, 170
STEP_DEG   = 2              # ° per tick for continuous motion
TICK_HZ    = 8              # ticks per second

WAVE_DURATION = 2.0         # s   hello-wave total time
WAVE_HZ       = 3           # pan flips per second
WAVE_AMPL     = 20          # ±° pan amplitude

# ──────────────────────────────────────────────────────────────────────
# Servo state
# ──────────────────────────────────────────────────────────────────────
servo_pan   = 90
servo_tilt  = 90
servo_level = 90  # wrist (servo3)

claw_grab_angles    = (170, 10)
claw_release_angles = (10, 170)
claw_grabbing = False

_dir_x = _dir_y = 0  # continuous motion dir (−1,0,+1)

_move_evt = threading.Event()
_mover_thr: threading.Thread | None = None
_wave_thr:  threading.Thread | None = None

# ──────────────────────────────────────────────────────────────────────
# Serial helpers
# ──────────────────────────────────────────────────────────────────────

def _find_arduino() -> str | None:
    for p in list_ports.comports():
        if "Arduino" in p.description or "usbmodem" in p.device:
            return p.device
    return None

def _open_serial() -> serial.Serial | None:
    port = _find_arduino()
    if port:
        try:
            return serial.Serial(port, 9600)
        except Exception as e:
            print("[Serial]", e, file=sys.stderr)
    else:
        print("[Serial] Arduino not found", file=sys.stderr)
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
        if not (_dir_x or _dir_y):
            _move_evt.clear(); break
        servo_pan  += STEP_DEG * _dir_x
        servo_tilt += STEP_DEG * _dir_y
        _send_angles()
        time.sleep(tick)

# ──────────────────────────────────────────────────────────────────────
# Hello wave thread (pan servo)
# ──────────────────────────────────────────────────────────────────────

def _pan_wave_loop(origin: int):
    """Wave pan servo and open/close claw in sync for WAVE_DURATION seconds."""
    global servo_pan, claw_grabbing
    half_period = 1 / (2 * WAVE_HZ)
    end_time    = time.time() + WAVE_DURATION
    swing_right = True  # True → right swing & claw open

    while time.time() < end_time:
        # pan position
        delta      = WAVE_AMPL if swing_right else -WAVE_AMPL
        servo_pan  = _clamp(origin + delta)
        # claw state (open on right swing)
        claw_grabbing = not swing_right

        _send_angles()
        swing_right = not swing_right
        time.sleep(half_period)

    # restore original pan, leave claw open
    servo_pan      = origin
    claw_grabbing  = False
    _send_angles()
    toggle = not toggle
    time.sleep(half)
    # final pose – original pan, claw open
    servo_pan = origin
    claw_grabbing = False
    _send_angles()
    _send_angles().time() + WAVE_DURATION
    toggle = True
    while time.time() < end:
        servo_pan = _clamp(origin + (WAVE_AMPL if toggle else -WAVE_AMPL))
        _send_angles()
        toggle = not toggle
        time.sleep(half)
    servo_pan = origin
    _send_angles()

# ──────────────────────────────────────────────────────────────────────
# Public entry – called by GUI / recogniser
# ──────────────────────────────────────────────────────────────────────

def handle_command(words: list[str]):
    global _dir_x, _dir_y, claw_grabbing, servo_pan, servo_tilt, servo_level, ser, _mover_thr, _wave_thr

    cmds = [w.lower() for w in words if w.lower() in COMMAND_WORDS]
    if not cmds:
        return  # ignore irrelevant words

    for w in cmds:
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
        elif w == "reset":
            if ser:
                try:
                    ser.setDTR(False); time.sleep(0.1); ser.setDTR(True)
                except serial.SerialException:
                    ser = _open_serial()
            servo_pan = servo_tilt = servo_level = 90
            _dir_x = _dir_y = 0
        elif w == "hello":
            # friendly wave: lift tilt + wrist, open claw, pan wave
            servo_tilt  = SERVO_MIN        # arm up (≈10°)
            servo_level = SERVO_MAX        # wrist up (≈170°)
            claw_grabbing = False          # open claw during wave
            _dir_x = _dir_y = 0            # pause other motion
            if not _wave_thr or not _wave_thr.is_alive():
                origin = servo_pan
                _wave_thr = threading.Thread(target=_pan_wave_loop, args=(origin,), daemon=True)
                _wave_thr.start()

    _send_angles()

    if (_dir_x or _dir_y) and not _move_evt.is_set():
        _move_evt.set(); _mover_thr = threading.Thread(target=_mover_loop, daemon=True); _mover_thr.start()

# ──────────────────────────────────────────────────────────────────────
# Optional standalone recogniser – prints only recognised COMMAND_WORDS
# ──────────────────────────────────────────────────────────────────────
VOICE_RATE, VOICE_BLOCK = 16_000, 8_000
_voice_evt = threading.Event()

def _voice_loop(model_dir: Path):
    mdl = Model(str(model_dir)); rec = KaldiRecognizer(mdl, VOICE_RATE); q: queue.Queue[bytes] = queue.Queue()
    def cb(indata, frames, t, status):
        if status: print(status, file=sys.stderr); q.put(bytes(indata))
    print(f"[Voice] say {' / '.join(sorted(COMMAND_WORDS))}")
    with sd.RawInputStream(samplerate=VOICE_RATE, blocksize=VOICE_BLOCK, dtype="int16", channels=1, callback=cb):
        while _voice_evt.is_set():
            data = q.get()
            if rec.AcceptWaveform(data):
                txt = json.loads(rec.Result()).get("text", "")
                words = [w for w in txt.split() if w in COMMAND_WORDS]
                if words:
                    print(">>", " ".join(words))
                    handle_command(words)

# CLI helper unchanged ...


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
