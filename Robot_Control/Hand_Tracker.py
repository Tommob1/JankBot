import cv2
import mediapipe as mp
import numpy as np
import serial
import serial.tools.list_ports
import struct

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
servo1_pos, servo2_pos, servo3_pos = 90, 90, 90
ser = None

claw_grabbing = False
claw_grab_pos = (170, 10)
claw_release_pos = (10, 170)

def is_fist(landmarks):
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]

    def distance(point1, point2):
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    d_thumb = distance(wrist, thumb_tip)
    d_index = distance(wrist, index_tip)
    d_middle = distance(wrist, middle_tip)
    d_ring = distance(wrist, ring_tip)
    d_pinky = distance(wrist, pinky_tip)

    if d_thumb < 0.2 and d_index < 0.2 and d_middle < 0.2 and d_ring < 0.2 and d_pinky < 0.2:
        return True
    return False

def is_hand_open(landmarks):
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]

    def distance(point1, point2):
        return np.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    distances = [
        distance(wrist, index_tip),
        distance(wrist, middle_tip),
        distance(wrist, ring_tip),
        distance(wrist, pinky_tip)
    ]

    average_distance = np.mean(distances)

    if average_distance > 0.3:
        return True
    else:
        return False

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
            print(f"Failed to connect to Arduino: {e}")
    else:
        ser = None
        print("Arduino not found.")

initialize_serial_connection()

def map_value(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def send_command():
    global ser, servo1_pos, servo2_pos, servo3_pos, claw_grabbing
    servo1_pos = max(0, min(servo1_pos, 180))
    servo2_pos = max(0, min(servo2_pos, 180))
    servo3_pos = max(0, min(servo3_pos, 180))

    if claw_grabbing:
        servo4_pos, servo5_pos = 10, 170
    else:
        servo4_pos, servo5_pos = 170, 10

    data = struct.pack('HHHHH', servo1_pos, servo2_pos, servo3_pos, servo4_pos, servo5_pos)
    if ser:
        try:
            ser.write(data)
        except serial.SerialException:
            print("Serial write failed. Reconnecting...")
            initialize_serial_connection()
    else:
        print("Serial connection not initialized. Reconnecting...")
        initialize_serial_connection()
        
def start_hand_tracker():
    global cap, servo1_pos, servo2_pos, servo3_pos, claw_grabbing
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    dial_angle = 0
    baseline_angle = None
    previous_claw_state = None

    while True:
        ret, image = cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        hand_landmarks_list = results.multi_hand_landmarks if results.multi_hand_landmarks else []

        if hand_landmarks_list:
            hand_landmarks = hand_landmarks_list[0].landmark
            hand_open = is_hand_open(hand_landmarks)
            claw_grabbing = not hand_open

            if claw_grabbing != previous_claw_state:
                print(f"Claw state: {'Grabbing' if claw_grabbing else 'Releasing'}")
                previous_claw_state = claw_grabbing

            wrist = hand_landmarks[mp_hands.HandLandmark.WRIST]
            middle_tip = hand_landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            dx = middle_tip.x - wrist.x
            dy = middle_tip.y - wrist.y
            current_angle = np.arctan2(dy, dx) * 180 / np.pi

            if baseline_angle is None:
                baseline_angle = current_angle

            dial_angle = current_angle - baseline_angle
            dial_angle = (dial_angle + 180) % 360 - 180

            center = (int(image.shape[1] * wrist.x), int(image.shape[0] * wrist.y))
            cv2.ellipse(image, center, (50, 50), -90, 0, dial_angle, (255, 0, 0), 5)
            cv2.putText(image, f'{int(dial_angle)}', (center[0], center[1] - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3, cv2.LINE_AA)

            servo1_pos = map_value(dial_angle, -180, 180, 0, 180)
            hand_pos_y = wrist.y * image.shape[0]
            hand_pos_x = middle_tip.x * image.shape[1]
            servo2_pos = map_value(hand_pos_y, 0, image.shape[0], 10, 170)
            servo3_pos = map_value(hand_pos_x, 0, image.shape[1], 170, 10)
            send_command()

            mp_drawing.draw_landmarks(
                image,
                results.multi_hand_landmarks[0],
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=5, circle_radius=5),
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=5))

        cv2.imshow('Hand Tracker', image)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

def stop_hand_tracker():
    global cap
    if cap:
        cap.release()
        cap = None
    cv2.destroyAllWindows()