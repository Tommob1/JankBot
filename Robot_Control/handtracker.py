import cv2
import mediapipe as mp
import struct
import serial
import serial.tools.list_ports
import threading

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
tracking = False

servo1_pos, servo2_pos, servo3_pos = 90, 90, 90
ser = None  # Placeholder for the serial object
thread = None

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
    else:
        print("Arduino not found")
    return ser

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

def start_hand_tracker():
    global tracking, servo1_pos, servo2_pos, servo3_pos
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands()

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    tracking = True
    while tracking:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            break
        
        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=5, circle_radius=5),
                                          mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=5))
                
                # Map hand position to robot control
                hand_pos_x = hand_landmarks.landmark[0].x * frame.shape[1]
                hand_pos_y = hand_landmarks.landmark[0].y * frame.shape[0]
                servo1_pos = int(map_value(hand_pos_x, 0, frame.shape[1], 10, 170))
                servo2_pos = int(map_value(hand_pos_y, 0, frame.shape[0], 10, 170))
                servo3_pos = int(map_value(servo2_pos, 10, 170, 10, 170))
                send_command()
        
        cv2.imshow('Handtracker', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def stop_hand_tracker():
    global tracking, thread
    tracking = False
    if thread:
        thread.join()
    print("Hand tracker stopped.")

def start_hand_tracker_thread():
    global thread
    if thread and thread.is_alive():
        print("Hand tracker is already running.")
        return
    thread = threading.Thread(target=start_hand_tracker)
    thread.start()