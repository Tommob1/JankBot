import serial
from pynput import mouse
import tkinter as tk

# ser = serial.Serial('/dev/tty.usbmodem11401', 9600)  # Update this to your specific port

mouse_x, mouse_y = 0, 0
servo1_pos, servo2_pos = 90, 90  

def on_move(x, y):
    global mouse_x, mouse_y
    mouse_x, mouse_y = x, y
    update_telemetry()

def update_telemetry():
    mouse_pos_label.config(text=f"Mouse Position: ({mouse_x}, {mouse_y})")
    servo_pos_label.config(text=f"Servo Positions: (Servo1: {servo1_pos}, Servo2: {servo2_pos})")

def start_tracking():
    listener.start()
    activate_button.config(state="disabled")
    deactivate_button.config(state="normal")

def stop_tracking():
    listener.stop()
    activate_button.config(state="normal")
    deactivate_button.config(state="disabled")

listener = mouse.Listener(on_move=on_move)

root = tk.Tk()
root.title("Robot Control")
root.configure(bg='black')

activate_button = tk.Button(root, text="Activate", command=start_tracking, bg='green', fg='white')
activate_button.grid(row=0, column=0, padx=10, pady=10, sticky='w')

deactivate_button = tk.Button(root, text="Deactivate", command=stop_tracking, bg='red', fg='white')
deactivate_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')
deactivate_button.config(state="disabled")

mouse_pos_label = tk.Label(root, text="Mouse Position: (0, 0)", bg='black', fg='white')
mouse_pos_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='w')

servo_pos_label = tk.Label(root, text="Servo Positions: (Servo1: 90, Servo2: 90)", bg='black', fg='white')
servo_pos_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='w')

root.mainloop()