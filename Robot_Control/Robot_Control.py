import sys, tkinter as tk
from typing import Optional
import struct, serial, serial.tools.list_ports as list_ports
from pynput import mouse
import Hand_Tracker
from logo import ascii_art               # make sure this really contains text!

# ────────────────────────────────────────────────────────────────────────
# 1.  CONSTANTS & PLATFORM CHECK
# ────────────────────────────────────────────────────────────────────────
IS_MAC = sys.platform == "darwin"

BG  = "#000000"     # black
FG  = "#00ff00"     # green
BTN = "#222222"     # dark grey buttons

# ────────────────────────────────────────────────────────────────────────
# 2.  ROBOT STATE
# ────────────────────────────────────────────────────────────────────────
tracking_mouse = False
tracking_hand  = False
claw_grabbing  = False

claw_grab_pos    = (170, 10)
claw_release_pos = (10, 170)

mouse_x = mouse_y = 0
servo1_pos = servo2_pos = servo3_pos = 90

# ────────────────────────────────────────────────────────────────────────
# 3.  SERIAL HELPERS
# ────────────────────────────────────────────────────────────────────────
def find_arduino_port() -> Optional[str]:
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
            print(f"Connected to {port}")
        except Exception as e:
            ser = None
            print(f"Failed to connect: {e}")
    else:
        ser = None
        print("Arduino not found.")

initialize_serial_connection()

# ────────────────────────────────────────────────────────────────────────
# 4.  MAPPING  &  COMMAND
# ────────────────────────────────────────────────────────────────────────
def map_value(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def send_command():
    global ser, servo1_pos, servo2_pos, servo3_pos
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
            print("Serial write failed – reconnecting…")
            initialize_serial_connection()

# ────────────────────────────────────────────────────────────────────────
# 5.  TK WINDOW  (with black “stage” on macOS)
# ────────────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Robot Control")
root.geometry("1280x720")
root.configure(background=BG, highlightthickness=0)

# Full-window black frame so we’re independent of Aqua’s default colours
stage = tk.Frame(root, bg=BG)
stage.place(relwidth=1, relheight=1)

# ────────────────────────────────────────────────────────────────────────
# 6.  BANNER  (appears line-by-line)
# ────────────────────────────────────────────────────────────────────────
if not ascii_art.strip():
    print("⚠️  'ascii_art' appears to be empty!")

banner = tk.Text(stage, bg=BG, fg=FG, bd=0, highlightthickness=0,
                 state="disabled", font=("Courier New", 10),
                 height=12, width=160)
banner.place(relx=0.5, y=10, anchor="n")

def load_banner(lines, idx=0, delay=30):
    if idx < len(lines):
        banner.configure(state="normal")
        banner.insert(tk.END, lines[idx] + "\n")
        banner.configure(state="disabled")
        banner.after(delay, lambda: load_banner(lines, idx+1, delay))

# ────────────────────────────────────────────────────────────────────────
# 7.  CONTROL PANEL
# ────────────────────────────────────────────────────────────────────────
panel = tk.Frame(stage, bg=BG)
panel.pack(pady=160)

def make_button(text, cmd, colour, disabled=False):
    # macOS ignores 'bg'; use highlightbackground as well
    cfg = dict(text=text, command=cmd, fg=FG, bd=0, padx=6, pady=4,
               activeforeground=FG, font=("Consolas", 11))
    if IS_MAC:
        cfg.update(bg=colour, activebackground=colour,
                   highlightbackground=colour, highlightthickness=0, relief="flat")
    else:
        cfg.update(bg=colour, activebackground=colour, highlightthickness=0)
    b = tk.Button(panel, **cfg)
    if disabled:
        b.config(state="disabled")
    b.pack(fill="x", pady=5, padx=20)
    return b

# Forward declarations to satisfy the callbacks
def start_mouse_tracking(): ...
def stop_mouse_tracking(): ...
def start_hand_tracking(): ...
def stop_hand_tracking(): ...

activate_mouse_button   = make_button("Activate Mouse Tracking",
                                      lambda: start_mouse_tracking(),  "#009900")
deactivate_mouse_button = make_button("Deactivate Mouse Tracking",
                                      lambda: stop_mouse_tracking(),   "#990000",
                                      disabled=True)
activate_hand_button    = make_button("Activate Hand Tracking",
                                      lambda: start_hand_tracking(),   "#0055ff")
deactivate_hand_button  = make_button("Deactivate Hand Tracking",
                                      lambda: stop_hand_tracking(),    "#ff8800",
                                      disabled=True)

mouse_pos_label = tk.Label(panel, text="Mouse : (0, 0)",
                           bg=BG, fg=FG, font=("Consolas", 11))
servo_pos_label = tk.Label(panel, text="Servos: (90, 90, 90)",
                           bg=BG, fg=FG, font=("Consolas", 11))
mouse_pos_label.pack(pady=5)
servo_pos_label.pack(pady=5)

# ────────────────────────────────────────────────────────────────────────
# 8.  MOUSE & HAND TRACKING CALLBACKS
# ────────────────────────────────────────────────────────────────────────
def on_move(x, y):
    global mouse_x, mouse_y, servo1_pos, servo2_pos, servo3_pos
    if tracking_mouse:
        mouse_x, mouse_y = x, y
        servo1_pos = map_value(mouse_x, 0, 1920, 10, 170)
        servo2_pos = map_value(mouse_y, 0, 1080, 10, 170)
        servo3_pos = map_value(servo2_pos, 10, 170, 10, 170)
        mouse_pos_label.config(text=f"Mouse : ({mouse_x}, {mouse_y})")
        servo_pos_label.config(text=f"Servos: ({servo1_pos}, {servo2_pos}, {servo3_pos})")
        send_command()

def on_click(_, __, ___, pressed):
    global claw_grabbing
    if pressed:
        claw_grabbing = not claw_grabbing
        send_command()

def start_mouse_tracking():
    global tracking_mouse, listener
    tracking_mouse = True
    listener = mouse.Listener(on_move=on_move, on_click=on_click)
    listener.start()
    activate_mouse_button.config(state="disabled")
    deactivate_mouse_button.config(state="normal")

def stop_mouse_tracking():
    global tracking_mouse, listener
    tracking_mouse = False
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

# ────────────────────────────────────────────────────────────────────────
# 9.  KICK THINGS OFF
# ────────────────────────────────────────────────────────────────────────
root.after(500, lambda: load_banner(ascii_art.splitlines()))
root.mainloop()