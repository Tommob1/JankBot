import tkinter as tk
#from customtkinter import CTk
from logo import ascii_art
import Hand_Tracker
from pynput import mouse
import struct
import serial
import threading, queue, json, sounddevice as sd
from vosk import Model, KaldiRecognizer
from voice_movement import handle_command
import threading, queue, json, sounddevice as sd
from vosk import Model, KaldiRecognizer

#import Remote_Access

tracking_mouse = False
tracking_hand = False
claw_grabbing = False

claw_grab_pos = (100, 45)
claw_release_pos = (1000, 150)

mouse_x, mouse_y = 0, 0
servo1_pos, servo2_pos, servo3_pos = 90, 90, 90

def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if 'Arduino' in port.description or 'usbmodem' in port.device:
            return port.device
    return None

def initialize_serial_connection():
    global ser
    port = find_arduino_port()
    if port:
        try:
            ser = serial.Serial(port, 9600)
        except Exception as e:
            ser = None
            print(f"Failed to connect to Arduino: {e}")
    else:
        ser = None
        print("Arduino not found.")

initialize_serial_connection()

def map_value(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def send_command():
    global ser, servo1_pos, servo2_pos, servo3_pos, claw_grabbing
    servo1_pos = max(0, min(servo1_pos, 180))
    servo2_pos = max(0, min(servo2_pos, 180))
    servo3_pos = max(0, min(servo3_pos, 180))

    if claw_grabbing:
        servo4_pos, servo5_pos = claw_grab_pos
    else:
        servo4_pos, servo5_pos = claw_release_pos

    data = struct.pack('HHHHH', servo1_pos, servo2_pos, servo3_pos, servo4_pos, servo5_pos)
    if ser:
        try:
            ser.write(data)
        except serial.SerialException:
            print("Serial write failed. Reconnecting...")
            initialize_serial_connection()
    else:
        print("Serial connection not initialized. Reconnecting...")
        initialize_serial_connection()

def on_move(x, y):
    global mouse_x, mouse_y, servo1_pos, servo2_pos, servo3_pos
    if tracking_mouse:
        mouse_x, mouse_y = x, y
        servo1_pos = int(map_value(mouse_x, 0, 1920, 10, 170))
        servo2_pos = int(map_value(mouse_y, 0, 1080, 10, 170))
        servo3_pos = int(map_value(servo2_pos, 10, 170, 10, 170))
        update_telemetry()
        send_command()

def on_click(x, y, button, pressed):
    global claw_grabbing
    if pressed:
        claw_grabbing = not claw_grabbing
        print(f"Claw state: {'Grabbing' if claw_grabbing else 'Releasing'}")
        send_command()

def update_telemetry():
    mouse_pos_label.config(text=f"Mouse Position: ({mouse_x}, {mouse_y})")
    servo_pos_label.config(text=f"Servo Positions: (Servo1: {servo1_pos}, {servo2_pos}, {servo3_pos})")

def start_mouse_tracking():
    global listener, tracking_mouse
    tracking_mouse = True
    listener = mouse.Listener(on_move=on_move, on_click=on_click)
    listener.start()
    activate_mouse_button.config(state="disabled")
    deactivate_mouse_button.config(state="normal")

def stop_mouse_tracking():
    global listener, tracking_mouse
    tracking_mouse = False
    if listener:
        listener.stop()
    activate_mouse_button.config(state="normal")
    deactivate_mouse_button.config(state="disabled")

def start_hand_tracking():
    global tracking_hand
    tracking_hand = True
    Hand_Tracker.start_hand_tracker()
    activate_hand_button.config(state="disabled")
    deactivate_hand_button.config(state="normal")

def stop_hand_tracking():
    global tracking_hand
    tracking_hand = False
    Hand_Tracker.stop_hand_tracker()
    activate_hand_button.config(state="normal")
    deactivate_hand_button.config(state="disabled")

def load_text_character_by_character(widget, text, index=0, delay=50):
    if index < len(text):
        if isinstance(widget, tk.Text):
            widget.configure(state='normal')
            widget.insert(tk.END, text[index])
            widget.configure(state='disabled')
        elif isinstance(widget, tk.Label):
            current_text = widget.cget("text")
            widget.configure(text=current_text + text[index])
        widget.see(tk.END) if isinstance(widget, tk.Text) else None
        widget.after(delay, lambda: load_text_character_by_character(widget, text, index + 1, delay))

root = tk.Tk()
root.title("Robot Control")
root.geometry("1280x720")
root.configure(bg='black')

voice_thread   = None
voice_running  = threading.Event()
VOICE_SAMPLE_RATE = 16_000
VOICE_BLOCK_LEN  = 8_000
VOICE_MODEL_DIR  = "models/vosk-model-small-en-us-0.15"

def voice_worker():
    """Background thread: listen and forward final commands to handle_command."""
    model = Model(VOICE_MODEL_DIR)
    rec   = KaldiRecognizer(model, VOICE_SAMPLE_RATE)
    rec.SetWords(True)

    q_audio: queue.Queue[bytes] = queue.Queue()

    def audio_cb(indata, frames, time, status):
        if status:
            print(status)
        q_audio.put(bytes(indata))

    print("[Voice] model loaded – listening (say left / right / up / down / stop)")
    try:
        with sd.RawInputStream(
            samplerate=VOICE_SAMPLE_RATE,
            blocksize=VOICE_BLOCK_LEN,
            dtype="int16",
            channels=1,
            callback=audio_cb,
        ):
            while voice_running.is_set():
                data = q_audio.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text   = result.get("text", "").strip()
                    if text:
                        print(f">> {text}")
                        handle_command(text.split())
    except Exception as e:
        print("[Voice] error:", e)
    print("[Voice] stopped")

def start_voice():
    global voice_thread
    if voice_thread and voice_thread.is_alive():
        return
    voice_running.set()
    voice_thread = threading.Thread(target=voice_worker, daemon=True)
    voice_thread.start()
    activate_voice_btn.config(state="disabled")
    deactivate_voice_btn.config(state="normal")

def stop_voice():
    voice_running.clear()
    activate_voice_btn.config(state="normal")
    deactivate_voice_btn.config(state="disabled")

activate_voice_btn = tk.Button(root,
    text="Activate Voice Cmd",
    command=start_voice,
    bg="green", fg="black")
activate_voice_btn.pack(pady=10, padx=10)

deactivate_voice_btn = tk.Button(root,
    text="Stop Voice Cmd",
    command=stop_voice,
    bg="orange", fg="black")
deactivate_voice_btn.pack(pady=10, padx=10)
deactivate_voice_btn.config(state="disabled")

text_color = "#00ff00"
button_color = "#333333"
border_color = "#555555"
font_style = ("Consolas", 12)

title_label = tk.Label(root, font=("Courier New", 10), bg='black', fg=text_color, anchor='center', justify='center')
title_label.pack(padx=10, pady=10)

activate_mouse_button = tk.Button(root, text="Activate Mouse Tracking", command=start_mouse_tracking, bg='green', fg='black')
activate_mouse_button.pack(pady=10, padx=10)

deactivate_mouse_button = tk.Button(root, text="Deactivate Mouse Tracking", command=stop_mouse_tracking, bg='red', fg='black')
deactivate_mouse_button.pack(pady=10, padx=10)
deactivate_mouse_button.config(state="disabled")

activate_hand_button = tk.Button(root, text="Activate Hand Tracking", command=start_hand_tracking, bg='blue', fg='black')
activate_hand_button.pack(pady=10, padx=10)

deactivate_hand_button = tk.Button(root, text="Deactivate Hand Tracking", command=stop_hand_tracking, bg='orange', fg='black')
deactivate_hand_button.pack(pady=10, padx=10)
deactivate_hand_button.config(state="disabled")

mouse_pos_label = tk.Label(root, text="Mouse Position: (0, 0)", bg='black', fg=text_color)
mouse_pos_label.pack(pady=10)

servo_pos_label = tk.Label(root, text="Servo Positions: (Servo1: 90, Servo2: 90, Servo3: 90)", bg='black', fg=text_color)
servo_pos_label.pack(pady=10)

root.after(1000, lambda: load_text_character_by_character(title_label, ascii_art, 0, 1))

root.mainloop()