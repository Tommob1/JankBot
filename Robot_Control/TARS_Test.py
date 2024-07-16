import os
import time
import tkinter as tk
import pygame
from subprocess import call, CalledProcessError

# Initialize pygame mixer for playing mp3 files
pygame.mixer.init()

# Path to Arduino CLI
ARDUINO_CLI_PATH = "arduino-cli"  # Ensure arduino-cli is in your PATH or provide the full path

# Path to the .ino file
INO_FILE_PATH = "Servo_Joint_Calibration_Test/Servo_Joint_Calibration_Test.ino"

# Arduino board settings
BOARD_TYPE = "arduino:avr:uno"
PORT = "/dev/cu.usbmodem11401"  # Update this to your Arduino's port

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
        # Compile the .ino file
        compile_cmd = f"{ARDUINO_CLI_PATH} compile --fqbn {BOARD_TYPE} {INO_FILE_PATH}"
        call(compile_cmd.split())

        # Upload the compiled sketch to the Arduino
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

    # Play the first MP3 file immediately
    play_mp3("Servo_Joint_Calibration_Test/TARS/Test_Activation.mp3")

    # Wait a short while before starting the upload
    time.sleep(1)

    upload_sketch()

    # Play the second MP3 file after the upload is complete
    play_mp3("Servo_Joint_Calibration_Test/TARS/Moving_Arm.mp3")

    # Wait for a moment to let the Arduino initialize
    time.sleep(12)

    # Play the third MP3 file after a delay
    play_mp3("Servo_Joint_Calibration_Test/TARS/Test_Complete.mp3")

def create_gui():
    root = tk.Tk()
    root.title("Servo Test Interface")

    test_button = tk.Button(root, text="Run Servo Test", command=run_test)
    test_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()