import serial
from pynput import mouse
import tkinter as tk

# Replace with your identified serial port
ser = serial.Serial('/dev/tty.usbmodem11401', 9600)

# Initialize global variables
mouse_x, mouse_y = 0, 0
servo1_pos, servo2_pos = 90, 90  # Assuming initial positions
listener = None

# Function to update mouse position
def on_move(x, y):
    global mouse_x, mouse_y
    mouse_x, mouse_y = x, y
    update_telemetry()

# Function to update telemetry data
def update_telemetry():
    mouse_pos_label.config(text=f"Mouse Position: ({mouse_x}, {mouse_y})")
    servo_pos_label.config(text=f"Servo Positions: (Servo1: {servo1_pos}, Servo2: {servo2_pos})")

# Function to start tracking
def start_tracking():
    global listener
    listener = mouse.Listener(on_move=on_move)
    listener.start()
    activate_button.config(state="disabled")
    deactivate_button.config(state="normal")

# Function to stop tracking
def stop_tracking():
    global listener
    if listener:
        listener.stop()
    activate_button.config(state="normal")
    deactivate_button.config(state="disabled")

# Create the Tkinter GUI
root = tk.Tk()
root.title("Robot Control")
root.configure(bg='black')

# Create and place the activate/deactivate buttons
activate_button = tk.Button(root, text="Activate", command=start_tracking, bg='green', fg='black')
activate_button.grid(row=0, column=0, padx=10, pady=10, sticky='w')

deactivate_button = tk.Button(root, text="Deactivate", command=stop_tracking, bg='red', fg='black')
deactivate_button.grid(row=0, column=1, padx=10, pady=10, sticky='w')
deactivate_button.config(state="disabled")

# Create and place the telemetry data labels
mouse_pos_label = tk.Label(root, text="Mouse Position: (0, 0)", bg='black', fg='white')
mouse_pos_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='w')

servo_pos_label = tk.Label(root, text="Servo Positions: (Servo1: 90, Servo2: 90)", bg='black', fg='white')
servo_pos_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='w')

# Run the Tkinter main loop
root.mainloop()