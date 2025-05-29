import tkinter as tk
from logo import ascii_art
import Hand_Tracker
from pynput import mouse
import struct, serial
import serial.tools.list_ports as list_ports
from typing import Optional           # <── added

# ───────────── robot-state flags ─────────────
tracking_mouse = False
tracking_hand  = False
claw_grabbing  = False

claw_grab_pos    = (170, 10)
claw_release_pos = (10, 170)

mouse_x, mouse_y               = 0, 0
servo1_pos, servo2_pos, servo3_pos = 90, 90, 90

# ───────────── serial helpers ────────────────
def find_arduino_port() -> Optional[str]:       # <── changed
    for port in list_ports.comports():
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

# ───────────── mapping & comms ───────────────
def map_value(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def send_command():
    global ser, servo1_pos, servo2_pos, servo3_pos, claw_grabbing

    servo1_pos = max(0, min(servo1_pos, 180))
    servo2_pos = max(0, min(servo2_pos, 180))
    servo3_pos = max(0, min(servo3_pos, 180))

    servo4_pos, servo5_pos = (claw_grab_pos if claw_grabbing else claw_release_pos)
    data = struct.pack('HHHHH', servo1_pos, servo2_pos, servo3_pos,
                                    servo4_pos, servo5_pos)
    if ser:
        try:
            ser.write(data)
        except serial.SerialException:
            print("Serial write failed. Re-connecting…")
            initialize_serial_connection()
    else:
        print("Serial not initialised. Re-connecting…")
        initialize_serial_connection()

# ───────────── mouse callbacks ───────────────
def on_move(x, y):
    global mouse_x, mouse_y, servo1_pos, servo2_pos, servo3_pos
    if tracking_mouse:
        mouse_x, mouse_y = x, y
        servo1_pos = map_value(mouse_x, 0, 1920, 10, 170)
        servo2_pos = map_value(mouse_y, 0, 1080, 10, 170)
        servo3_pos = map_value(servo2_pos, 10, 170, 10, 170)
        update_telemetry()
        send_command()

def on_click(_, __, ___, pressed):
    global claw_grabbing
    if pressed:
        claw_grabbing = not claw_grabbing
        print(f"Claw state: {'Grabbing' if claw_grabbing else 'Releasing'}")
        send_command()

# ───────────── telemetry & toggles ───────────
def update_telemetry():
    mouse_pos_label.config(text=f"Mouse Position : ({mouse_x}, {mouse_y})")
    servo_pos_label.config(
        text=f"Servo Positions : (S1:{servo1_pos}  S2:{servo2_pos}  S3:{servo3_pos})"
    )

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

# ───────────── ASCII banner animation ────────
def load_banner_line_by_line(widget, lines, idx=0, delay=30):
    if idx < len(lines):
        widget.configure(state="normal")
        widget.insert(tk.END, lines[idx] + "\n")
        widget.configure(state="disabled")
        widget.after(delay, lambda: load_banner_line_by_line(widget, lines,
                                                             idx + 1, delay))

# ───────────── UI constants & build ──────────
BG, FG, BTN = "#000000", "#00ff00", "#222222"

root = tk.Tk()
root.title("Robot Control")
root.geometry("1280x720")
root.configure(bg=BG, highlightthickness=0)

# banner
title = tk.Text(root, bg=BG, fg=FG, font=("Courier New", 10),
                state="disabled", bd=0, highlightthickness=0,
                height=12, width=160)
title.place(relx=0.5, y=10, anchor="n")

# control panel
panel = tk.Frame(root, bg=BG)
panel.pack(pady=160)

def make_button(text, cmd, colour):
    return tk.Button(panel, text=text, command=cmd,
                     bg=colour, fg=BG, activebackground=colour,
                     activeforeground=FG, bd=0, highlightthickness=0,
                     font=("Consolas", 11), padx=6, pady=4)

activate_mouse_button   = make_button("Activate Mouse Tracking",
                                      start_mouse_tracking,  "#009900")
deactivate_mouse_button = make_button("Deactivate Mouse Tracking",
                                      stop_mouse_tracking,   "#990000")
activate_hand_button    = make_button("Activate Hand Tracking",
                                      start_hand_tracking,   "#0055ff")
deactivate_hand_button  = make_button("Deactivate Hand Tracking",
                                      stop_hand_tracking,    "#ff8800")

for b in (activate_mouse_button, deactivate_mouse_button,
          activate_hand_button,  deactivate_hand_button):
    b.pack(fill="x", pady=5, padx=20)

deactivate_mouse_button.config(state="disabled")
deactivate_hand_button.config(state="disabled")

mouse_pos_label = tk.Label(panel, text="Mouse Position : (0, 0)",
                           bg=BG, fg=FG, font=("Consolas", 11))
servo_pos_label = tk.Label(panel, text="Servo Positions : (90, 90, 90)",
                           bg=BG, fg=FG, font=("Consolas", 11))
mouse_pos_label.pack(pady=5)
servo_pos_label.pack(pady=5)

# kick off banner animation
root.after(500, lambda: load_banner_line_by_line(title, ascii_art.splitlines()))
root.mainloop()