#include <Servo.h>

Servo servo1;  // Arm servo
Servo servo2;  // Arm servo
Servo servo3;  // Arm servo
Servo servo4;  // Claw servo
Servo servo5;  // Claw servo

int pos1 = 90;
int pos2 = 90;
int pos3 = 90;
int pos4 = 90;  // Claw servo 1 position
int pos5 = 90;  // Claw servo 2 position

int servo1Left = 10;
int servo1Right = 170;
int servo2Up = 10;
int servo2Down = 170;
int servo3Min = 10;
int servo3Max = 170;
int servo4Min = 10;
int servo4Max = 170;
int servo5Min = 10;
int servo5Max = 170;

bool clawClosing = true;
unsigned long lastClawMoveTime = 0;
int clawSpeed = 10; // milliseconds between claw movements

void setup() {
  // Attach all servos
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9);
  servo4.attach(12);  // Claw servo
  servo5.attach(13);  // Claw servo

  // Set initial positions
  servo1.write(pos1);
  servo2.write(pos2);
  servo3.write(pos3);
  servo4.write(pos4);
  servo5.write(pos5);

  Serial.begin(9600);
}

void loop() {
  // Check if serial data is available for controlling the arm
  if (Serial.available() >= 6) {
    char buffer[6];
    Serial.readBytes(buffer, 6);

    // Decode positions from buffer
    pos1 = buffer[0] | (buffer[1] << 8);
    pos2 = buffer[2] | (buffer[3] << 8);
    pos3 = buffer[4] | (buffer[5] << 8);

    // Arm control logic
    if (pos1 >= servo1Left && pos1 <= servo1Right) {
      servo1.write(pos1);
    }
    if (pos2 >= servo2Up && pos2 <= servo2Down) {
      servo2.write(pos2);
      pos3 = map(pos2, servo2Up, servo2Down, servo3Min, servo3Max);
      servo3.write(pos3);
    }
  }

  // Non-blocking claw demo
  unsigned long currentMillis = millis();
  if (currentMillis - lastClawMoveTime >= clawSpeed) {
    lastClawMoveTime = currentMillis;

    // Move claw servos to simulate pinching
    if (clawClosing) {
      pos4 += 1;
      pos5 -= 1;
    } else {
      pos4 -= 1;
      pos5 += 1;
    }

    // Write positions to claw servos
    servo4.write(pos4);
    servo5.write(pos5);

    // Check if the claw has reached its limits
    if (pos4 >= servo4Max || pos5 <= servo5Min) {
      clawClosing = false;  // Start opening the claw
    }
    if (pos4 <= servo4Min || pos5 >= servo5Max) {
      clawClosing = true;  // Start closing the claw
    }
  }
}