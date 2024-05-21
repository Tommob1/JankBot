#include <Servo.h>

Servo servo1;
Servo servo2;

void setup() {
  servo1.attach(10);
  servo2.attach(11);
}

void loop() {
  for (int pos1 = 0; pos1 <= 180; pos1 += 1) {
    servo1.write(pos1);
    delay(15);
  }

  for (int pos2 = 0; pos2 <= 180; pos2 += 1) {
    servo2.write(pos2);
    delay(5);
  }

  for (int pos1 = 180; pos1 >= 0; pos1 -= 1) {
    servo1.write(pos1);
    delay(15);
  }

  for (int pos2 = 180; pos2 >= 0; pos2 -= 1) {
    servo2.write(pos2);
    delay(5);
  }
}
