import serial
from pynput import mouse
import tkinter as tk
import struct
from logo import ascii_art

ser = serial.Serial('/dev/tty.usbmodem11401', 9600)
mouse_x, mouse_y = 0, 0
servo1_pos, servo2_pos, servo3_pos = 90, 90, 90
listener = None

def on_move(x, y):
    global mouse_x, mouse_y, servo1_pos, servo2_pos, servo3_pos
    mouse_x, mouse_y = x, y
    servo1_pos = int(map_value(mouse_x, 0, 1920, 10, 170))
    servo2_pos = int(map_value(mouse_y, 0, 1080, 10, 170))
    servo3_pos = int(map_value(servo2_pos, 10, 170, 10, 170))
    update_telemetry()
    send_command()

def send_command():
    data = struct.pack('HHH', servo1_pos, servo2_pos, servo3_pos)
    ser.write(data)

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def update_telemetry():
    mouse_pos_label.config(text=f"Mouse Position: ({mouse_x}, {mouse_y})")
    servo_pos_label.config(text=f"Servo Positions: (Servo1: {servo1_pos}, Servo2: {servo2_pos}, Servo3: {servo3_pos})")

def start_tracking():
    global listener
    listener = mouse.Listener(on_move=on_move)
    listener.start()
    activate_button.config(state="disabled")
    deactivate_button.config(state="normal")

def stop_tracking():
    global listener
    if listener:
        listener.stop()
    activate_button.config(state="normal")
    deactivate_button.config(state="disabled")

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

text_color = "#00ff00"
button_color = "#333333"
border_color = "#555555"
font_style = ("Consolas", 12)

title_label = tk.Label(root, font=("Courier New", 10), bg='black', fg=text_color, anchor='center', justify='center')
title_label.pack(padx=10, pady=10)

activate_button = tk.Button(root, text="Activate", command=start_tracking, bg='green', fg='black')
activate_button.pack(pady=10, padx=10)

deactivate_button = tk.Button(root, text="Deactivate", command=stop_tracking, bg='red', fg='black')
deactivate_button.pack(pady=10, padx=10)
deactivate_button.config(state="disabled")

mouse_pos_label = tk.Label(root, text="Mouse Position: (0, 0)", bg='black', fg=text_color)
mouse_pos_label.pack(pady=10)

servo_pos_label = tk.Label(root, text="Servo Positions: (Servo1: 90, Servo2: 90, Servo3: 90)", bg='black', fg=text_color)
servo_pos_label.pack(pady=10)

root.after(1000, lambda: load_text_character_by_character(title_label, ascii_art, 0, 1))

root.mainloop()