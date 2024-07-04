#include <Servo.h>

Servo servo1;
Servo servo2;
int pos1 = 90;
int pos2 = 90;

void setup() {
  servo1.attach(11);
  servo2.attach(10);
  servo1.write(pos1);
  servo2.write(pos2);
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
        break;
      case 'D':
        pos2 -= 5;
        if (pos2 < 0) pos2 = 0;
        servo2.write(pos2);
        break;
    }
  }
}