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
  if (Serial.available() >= 6) { // Ensure there are enough bytes to read
    char buffer[6];
    Serial.readBytes(buffer, 6);

    pos1 = buffer[0] | (buffer[1] << 8);
    pos2 = buffer[2] | (buffer[3] << 8);
    pos3 = buffer[4] | (buffer[5] << 8);

    if (pos1 >= servo1Left && pos1 <= servo1Right) {
      servo1.write(pos1);
    }
    if (pos2 >= servo2Up && pos2 <= servo2Down) {
      servo2.write(pos2);
      pos3 = map(pos2, servo2Up, servo2Down, servo3Min, servo3Max);
      servo3.write(pos3);
    }
  }
}