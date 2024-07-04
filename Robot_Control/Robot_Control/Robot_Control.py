import serial
from pynput.mouse import Listener
import time

# Replace with your identified serial port
ser = serial.Serial('/dev/tty.usbmodem11401', 9600)  # Update this to your specific port
last_time = time.time()

def on_move(x, y):
    global last_time
    current_time = time.time()
    if current_time - last_time > 0.01:  # 100 ms debounce
        if x > 500:
            ser.write(b'D')
        elif x < 300:
            ser.write(b'A')
        if y > 500:
            ser.write(b'S')
        elif y < 300:
            ser.write(b'W')
        last_time = current_time

def on_click(x, y, button, pressed):
    pass

def on_scroll(x, y, dx, dy):
    pass

# Set up the mouse listener
listener = Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)

# Function to start the mouse listener
def start_control():
    listener.start()

# Create a simple GUI
import tkinter as tk
root = tk.Tk()
root.title("Robot Control")

start_button = tk.Button(root, text="Start Control", command=start_control)
start_button.pack(pady=20)

root.mainloop()