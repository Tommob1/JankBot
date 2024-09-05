#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;  // Claw servo
Servo servo5;  // Claw servo

int pos1 = 90;
int pos2 = 90;
int pos3 = 90;
int pos4 = 90;  // Claw servo 1 position
int pos5 = 90;  // Claw servo 2 position

void setup() {
  // Attach all the servos to the corresponding pins
  servo1.attach(11);  // Arm servo 1
  servo2.attach(10);  // Arm servo 2
  servo3.attach(9);   // Arm servo 3
  servo4.attach(12);  // Claw servo 1
  servo5.attach(13);  // Claw servo 2

  // Initialize the serial connection
  Serial.begin(9600);
}

void loop() {
  // Ensure that the Arduino reads 10 bytes (2 bytes for each of the 5 servos)
  if (Serial.available() >= 10) {
    // Prepare a buffer for the incoming data
    byte buffer[10];
    Serial.readBytes(buffer, 10);  // Read the 10 bytes from serial

    // Unpack 16-bit values for each servo position
    pos1 = buffer[0] | (buffer[1] << 8);
    pos2 = buffer[2] | (buffer[3] << 8);
    pos3 = buffer[4] | (buffer[5] << 8);
    pos4 = buffer[6] | (buffer[7] << 8);
    pos5 = buffer[8] | (buffer[9] << 8);

    // Ensure positions are clamped within the servo's movement range
    pos1 = constrain(pos1, 0, 180);
    pos2 = constrain(pos2, 0, 180);
    pos3 = constrain(pos3, 0, 180);
    pos4 = constrain(pos4, 0, 180);
    pos5 = constrain(pos5, 0, 180);

    // Write the positions to the respective servos
    servo1.write(pos1);
    servo2.write(pos2);
    servo3.write(pos3);
    servo4.write(pos4);  // Claw servo
    servo5.write(pos5);  // Claw servo
  }
}