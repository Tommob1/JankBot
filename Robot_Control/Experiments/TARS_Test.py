import time
import tkinter as tk
import pygame
from subprocess import call, CalledProcessError

pygame.mixer.init()
ARDUINO_CLI_PATH = "arduino-cli"
INO_FILE_PATH = "Servo_Joint_Calibration_Test/Servo_Joint_Calibration_Test.ino"
BOARD_TYPE = "arduino:avr:uno"
PORT = "/dev/cu.usbmodem1201"

def check_arduino_cli():
    try:
        result = call([ARDUINO_CLI_PATH, "version"])
        if result != 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print("Error: arduino-cli not found. Please ensure it is installed and in your PATH.")
        return False
    return True

def upload_sketch():
    try:
        compile_cmd = f"{ARDUINO_CLI_PATH} compile --fqbn {BOARD_TYPE} {INO_FILE_PATH}"
        call(compile_cmd.split())
        upload_cmd = f"{ARDUINO_CLI_PATH} upload -p {PORT} --fqbn {BOARD_TYPE} {INO_FILE_PATH}"
        call(upload_cmd.split())
        print("Sketch uploaded successfully!")
    except CalledProcessError as e:
        print(f"Error: Failed to upload sketch: {e}")
    except Exception as e:
        print(f"Error: An unexpected error occurred: {e}")

def play_mp3(file):
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()

def run_test():
    if not check_arduino_cli():
        return
    play_mp3("Servo_Joint_Calibration_Test/TARS/Test_Activation.mp3")
    time.sleep(1)
    upload_sketch()
    play_mp3("Servo_Joint_Calibration_Test/TARS/Moving_Arm.mp3")
    time.sleep(12)
    play_mp3("Servo_Joint_Calibration_Test/TARS/Test_Complete.mp3")

def create_gui():
    root = tk.Tk()
    root.title("Servo Test Interface")
    test_button = tk.Button(root, text="Run Servo Test", command=run_test)
    test_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()