#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

int joyX;
int joyY;
int pot;
int servo1Pos;
int servo2Pos;
int servo3Pos;

int servo1Min = 10;
int servo1Max = 170;
int servo2Min = 10;
int servo2Max = 170;
int servo3Min = 10;
int servo3Max = 170;

const int numReadings = 10; // Number of readings to average
int readings[numReadings];  // Array to store readings
int readIndex = 0;          // Current reading index
int total = 0;              // Sum of readings
int average = 0;            // Average of readings

void setup() {
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9);
  Serial.begin(9600);

  // Initialize all readings to 0
  for (int i = 0; i < numReadings; i++) {
    readings[i] = 0;
  }
}

void loop() {
  joyX = analogRead(A0);
  joyY = analogRead(A1);

  // Read the potentiometer
  pot = analogRead(A2);

  // Subtract the last reading
  total = total - readings[readIndex];
  // Add the new reading
  readings[readIndex] = pot;
  total = total + readings[readIndex];
  // Advance to the next position in the array
  readIndex = readIndex + 1;

  // If at the end of the array, wrap around to the beginning
  if (readIndex >= numReadings) {
    readIndex = 0;
  }

  // Calculate the average
  average = total / numReadings;

  // Map the average value to the servo position
  servo1Pos = map(joyX, 0, 1023, servo1Max, servo1Min);
  servo2Pos = map(joyY, 0, 1023, servo2Min, servo2Max);
  servo3Pos = map(average, 0, 1023, servo3Min, servo3Max);

  // Write the positions to the servos
  servo1.write(servo1Pos);
  servo2.write(servo2Pos);
  servo3.write(servo3Pos);

  // Print positions for debugging
  Serial.print("Servo1 Position: ");
  Serial.println(servo1Pos);
  Serial.print("Servo2 Position: ");
  Serial.println(servo2Pos);
  Serial.print("Servo3 Position: ");
  Serial.println(servo3Pos);

  delay(15);
}