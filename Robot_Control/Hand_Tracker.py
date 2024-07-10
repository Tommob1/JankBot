import cv2
import mediapipe as mp
import struct
import serial
import serial.tools.list_ports
import threading

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
tracking = False
cap = None
servo1_pos, servo2_pos, servo3_pos = 90, 90, 90
ser = None
thread = None

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
    else:
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
            initialize_serial_connection()
    else:
        initialize_serial_connection()

def start_hand_tracker():
    global tracking, servo1_pos, servo2_pos, servo3_pos, cap
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return
    tracking = True
    while tracking:
        ret, frame = cap.read()
        if not ret:
            break
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
            break
    cap.release()
    cv2.destroyAllWindows()

def stop_hand_tracker():
    global tracking, cap
    tracking = False
    if cap:
        cap.release()
    cv2.destroyAllWindows()

def start_hand_tracker_thread():
    global thread
    if thread and thread.is_alive():
        return
    thread = threading.Thread(target=start_hand_tracker)
    thread.start()