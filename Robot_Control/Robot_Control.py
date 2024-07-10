import cv2
import mediapipe as mp
import struct
import serial
import serial.tools.list_ports
import tkinter as tk
from customtkinter import *
from logo import ascii_art

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
tracking = False
cap = None

servo1_pos, servo2_pos, servo3_pos = 90, 90, 90

def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        print(f"Checking port: {port}")
        if 'Arduino' in port.description or 'usbmodem' in port.device:
            print(f"Found Arduino on port: {port.device}")
            return port.device
    return None

def initialize_serial_connection():
    global ser
    port = find_arduino_port()
    if port:
        try:
            ser = serial.Serial(port, 9600)
            print(f"Connected to Arduino on port: {port}")
        except Exception as e:
            print(f"Error connecting to {port}: {e}")
            ser = None
    else:
        print("Arduino not found")
        ser = None

initialize_serial_connection()

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def send_command():
    global ser, servo1_pos, servo2_pos, servo3_pos
    data = struct.pack('HHH', servo1_pos, servo2_pos, servo3_pos)
    if ser:
        try:
            ser.write(data)
        except serial.SerialException:
            print("Serial connection lost. Reconnecting...")
            initialize_serial_connection()
    else:
        print("Serial connection not initialized.")

def process_hand_tracking():
    global servo1_pos, servo2_pos, servo3_pos, cap
    if tracking:
        if cap is None:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Could not open webcam.")
                cap = None
                return

        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            return
        
        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=5, circle_radius=5),
                                          mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=5))

                hand_pos_x = hand_landmarks.landmark[0].x * frame.shape[1]
                hand_pos_y = hand_landmarks.landmark[0].y * frame.shape[0]
                servo1_pos = int(map_value(hand_pos_x, 0, frame.shape[1], 10, 170))
                servo2_pos = int(map_value(hand_pos_y, 0, frame.shape[0], 10, 170))
                servo3_pos = int(map_value(servo2_pos, 10, 170, 10, 170))
                send_command()

        cv2.imshow('Handtracker', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_hand_tracker()
    root.after(10, process_hand_tracking)

def start_hand_tracker():
    global tracking
    tracking = True
    process_hand_tracking()

def stop_hand_tracker():
    global tracking, cap
    tracking = False
    if cap:
        cap.release()
        cap = None
    cv2.destroyAllWindows()

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

activate_button = tk.Button(root, text="Activate Mouse Tracking", command=start_hand_tracker, bg='green', fg='black')
activate_button.pack(pady=10, padx=10)

deactivate_button = tk.Button(root, text="Deactivate Mouse Tracking", command=stop_hand_tracker, bg='red', fg='black')
deactivate_button.pack(pady=10, padx=10)

mouse_pos_label = tk.Label(root, text="Mouse Position: (0, 0)", bg='black', fg=text_color)
mouse_pos_label.pack(pady=10)

servo_pos_label = tk.Label(root, text="Servo Positions: (Servo1: 90, Servo2: 90, Servo3: 90)", bg='black', fg=text_color)
servo_pos_label.pack(pady=10)

root.after(1000, lambda: load_text_character_by_character(title_label, ascii_art, 0, 1))

root.mainloop()