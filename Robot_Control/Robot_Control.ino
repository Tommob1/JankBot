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

const int numReadings = 10;
int readings[numReadings];
int readIndex = 0;
int total = 0;
int average = 0;

void setup() {
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9);
  Serial.begin(9600);

  for (int i = 0; i < numReadings; i++) {
    readings[i] = 0;
  }
}

void loop() {
  joyX = analogRead(A0);
  joyY = analogRead(A1);

  pot = analogRead(A2);

  total = total - readings[readIndex];
  readings[readIndex] = pot;
  total = total + readings[readIndex];
  readIndex = readIndex + 1;

  if (readIndex >= numReadings) {
    readIndex = 0;
  }

  average = total / numReadings;

  servo1Pos = map(joyX, 0, 1023, servo1Max, servo1Min);
  servo2Pos = map(joyY, 0, 1023, servo2Min, servo2Max);
  servo3Pos = map(average, 0, 1023, servo3Min, servo3Max);

  servo1.write(servo1Pos);
  servo2.write(servo2Pos);
  servo3.write(servo3Pos);

  Serial.print("Servo1 Position: ");
  Serial.println(servo1Pos);
  Serial.print("Servo2 Position: ");
  Serial.println(servo2Pos);
  Serial.print("Servo3 Position: ");
  Serial.println(servo3Pos);

  delay(15);
}