#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

int pos1 = 90;
int pos2 = 90;
int pos3 = 90;

int servo1Left = 10;
int servo1Right = 170;
int servo2Up = 10;
int servo2Down = 170;
int servo3Min = 10;
int servo3Max = 170;

void setup() {
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9);
  servo1.write(pos1);
  servo2.write(pos2);
  servo3.write(pos3);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    switch (command) {
      case 'W':
        pos1 += 5;
        if (pos1 > 180) pos1 = 180;
        servo1.write(pos1);
        break;
      case 'S':
        pos1 -= 5;
        if (pos1 < 0) pos1 = 0;
        servo1.write(pos1);
        break;
      case 'A':
        pos2 += 5;
        if (pos2 > 180) pos2 = 180;
        servo2.write(pos2);
        pos3 = map(pos2, servo2Up, servo2Down, servo3Min, servo3Max);
        servo3.write(pos3);
        break;
      case 'D':
        pos2 -= 5;
        if (pos2 < 0) pos2 = 0;
        servo2.write(pos2);
        pos3 = map(pos2, servo2Down, servo2Up, servo3Max, servo3Min);
        servo3.write(pos3);
        break;
    }
  }
}