#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;
Servo servo5;

int pos1 = 90;
int pos2 = 90;
int pos3 = 90;
int pos4 = 90;
int pos5 = 90;

void setup() {
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9);
  servo4.attach(12);
  servo5.attach(13);

  Serial.begin(9600);
}

void loop() {
  if (Serial.available() >= 10) {
    byte buffer[10];
    Serial.readBytes(buffer, 10);

    pos1 = buffer[0] | (buffer[1] << 8);
    pos2 = buffer[2] | (buffer[3] << 8);
    pos3 = buffer[4] | (buffer[5] << 8);
    pos4 = buffer[6] | (buffer[7] << 8);
    pos5 = buffer[8] | (buffer[9] << 8);

    pos1 = constrain(pos1, 0, 180);
    pos2 = constrain(pos2, 0, 180);
    pos3 = constrain(pos3, 0, 180);
    pos4 = constrain(pos4, 0, 180);
    pos5 = constrain(pos5, 0, 180);

    servo1.write(pos1);
    servo2.write(pos2);
    servo3.write(pos3);
    servo4.write(pos4);
    servo5.write(pos5);
  }
}