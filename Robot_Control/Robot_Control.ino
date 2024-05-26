#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3; // Add the third servo

int joyX;
int joyY;
int pot; // Add variable for potentiometer
int servo1Pos;
int servo2Pos;
int servo3Pos; // Add variable for third servo position

int servo1Min = 10;
int servo1Max = 170;
int servo2Min = 10;
int servo2Max = 170;
int servo3Min = 10; // Define min for third servo
int servo3Max = 170; // Define max for third servo

void setup() {
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9); // Attach third servo to pin 9
  Serial.begin(9600);
}

void loop() {
  joyX = analogRead(A0);
  joyY = analogRead(A1);
  pot = analogRead(A2); // Read potentiometer value

  servo1Pos = map(joyX, 0, 1023, servo1Max, servo1Min);
  servo2Pos = map(joyY, 0, 1023, servo2Min, servo2Max);
  servo3Pos = map(pot, 0, 1023, servo3Min, servo3Max); // Map potentiometer value

  servo1.write(servo1Pos);
  servo2.write(servo2Pos);
  servo3.write(servo3Pos); // Write position to third servo

  Serial.print("Servo1 Position: ");
  Serial.println(servo1Pos);
  Serial.print("Servo2 Position: ");
  Serial.println(servo2Pos);
  Serial.print("Servo3 Position: "); // Print third servo position
  Serial.println(servo3Pos);

  delay(15);
}