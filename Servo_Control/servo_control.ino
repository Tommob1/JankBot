#include <Servo.h>

Servo servo1;
Servo servo2;

int joyX;
int joyY;
int servo1Pos;
int servo2Pos;

// Define the range of your servos if they can't reach the full 0 to 180 degrees
int servo1Min = 10;  // replace with the minimum angle your servo1 can safely turn to
int servo1Max = 170; // replace with the maximum angle your servo1 can safely turn to
int servo2Min = 10;  // replace with the minimum angle your servo2 can safely turn to
int servo2Max = 170; // replace with the maximum angle your servo2 can safely turn to

void setup() {
  servo1.attach(10);
  servo2.attach(11);

  Serial.begin(9600); // Start serial communication at 9600 baud rate
}

void loop() {
  joyX = analogRead(A0);
  joyY = analogRead(A1);

  // Map the joystick values to the servo values within the calibrated range
  servo1Pos = map(joyX, 0, 1023, servo1Min, servo1Max);
  servo2Pos = map(joyY, 0, 1023, servo2Min, servo2Max);

  // Update the servo positions
  servo1.write(servo1Pos);
  servo2.write(servo2Pos);

  // Output the positions to the serial monitor for debugging
  Serial.print("Servo1 Position: ");
  Serial.print(servo1Pos);
  Serial.print("\tServo2 Position: ");
  Serial.println(servo2Pos);

  delay(15); // Delay to reduce jitter
}

