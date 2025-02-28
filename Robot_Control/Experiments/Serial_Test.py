import serial
import serial.tools.list_ports
from pynput import mouse
import struct
import time
import threading

def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        print(f"Checking port: {port}")
        if 'Arduino' in port.description or 'usbmodem' in port.device or 'Arduino Uno' in port.description:
            print(f"Found Arduino on port: {port.device}")
            return port.device
    return None

def initialize_serial_connection():
    port = find_arduino_port()
    if port:
        try:
            return serial.Serial(port, 9600)
        except Exception as e:
            print(f"Error connecting to {port}: {e}")
    else:
        print("Arduino not found")
    return None

ser = initialize_serial_connection()
mouse_x, mouse_y = 0, 0
servo1_pos, servo2_pos, servo3_pos = 90, 90, 90
listener = None
last_update_time = time.time()

def on_move(x, y):
    global mouse_x, mouse_y, servo1_pos, servo2_pos, servo3_pos, last_update_time
    current_time = time.time()
    if current_time - last_update_time > 0.1:
        mouse_x, mouse_y = x, y
        servo1_pos = int(map_value(mouse_x, 0, 1920, 10, 170))
        servo2_pos = int(map_value(mouse_y, 0, 1080, 10, 170))
        servo3_pos = int(map_value(servo2_pos, 10, 170, 10, 170))
        print(f"Mouse moved to ({mouse_x}, {mouse_y}) -> Servo1: {servo1_pos}, Servo2: {servo2_pos}, Servo3: {servo3_pos}")
        send_command()
        last_update_time = current_time

def send_command():
    global ser
    data = struct.pack('HHH', servo1_pos, servo2_pos, servo3_pos)
    print(f"Sending data: {servo1_pos}, {servo2_pos}, {servo3_pos}")
    if ser:
        try:
            ser.write(data)
            print("Data sent successfully.")
        except serial.SerialException as e:
            print(f"Error sending data: {e}")
            print("Serial connection lost. Reconnecting...")
            ser = initialize_serial_connection()
    else:
        print("Serial connection not initialized.")

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def start_mouse_listener():
    with mouse.Listener(on_move=on_move) as listener:
        print("Starting mouse listener")
        listener.join()

if ser:
    print("Connected to Arduino")
    time.sleep(2)
    ser.write(b'\x5A\x00\x5A\x00\x5A\x00')

    listener_thread = threading.Thread(target=start_mouse_listener)
    listener_thread.start()
else:
    print("Failed to connect to Arduino.")
