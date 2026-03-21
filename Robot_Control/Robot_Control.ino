#include <Servo.h>

Servo wristServo;
Servo clawServo;

int wristPos = 90;
int clawPos = 140;  // start open

void setup() {
  wristServo.attach(11);  // wrist/spin servo
  clawServo.attach(12);   // claw servo

  wristServo.write(wristPos);
  clawServo.write(clawPos);

  Serial.begin(9600);
}

void loop() {
  // Expect exactly 2 unsigned short values = 4 bytes total
  if (Serial.available() >= 4) {
    byte buffer[4];
    Serial.readBytes(buffer, 4);

    wristPos = buffer[0] | (buffer[1] << 8);
    clawPos  = buffer[2] | (buffer[3] << 8);

    wristPos = constrain(wristPos, 0, 180);
    clawPos  = constrain(clawPos, 0, 180);

    wristServo.write(wristPos);
    clawServo.write(clawPos);
  }
}