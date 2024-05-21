#include <Servo.h>

Servo servo1;
Servo servo2;

int joyX;
int joyY;
int servo1Pos;
int servo2Pos;

int servo1Min = 10;
int servo1Max = 170;
int servo2Min = 10;
int servo2Max = 170;

void setup() {
  servo1.attach(11);
  servo2.attach(10);

  Serial.begin(9600);
}

void loop() {
  joyX = analogRead(A0);
  joyY = analogRead(A1);

  servo1Pos = map(joyX, 0, 1023, servo1Max, servo1Min);
  servo2Pos = map(joyY, 0, 1023, servo2Min, servo2Max);

  servo1.write(servo1Pos);
  servo2.write(servo2Pos);

  Serial.print("Servo1 Position: ");
  Serial.print(servo1Pos);
  Serial.print("\tServo2 Position: ");
  Serial.println(servo2Pos);

  delay(15);
}