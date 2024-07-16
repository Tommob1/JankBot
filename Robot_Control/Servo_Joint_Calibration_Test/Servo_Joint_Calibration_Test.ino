#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

int servo1Pos;
int servo2Pos;
int servo3Pos;

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
  Serial.begin(9600);
}

void loop() {
  // Test Servo 1
  for (servo1Pos = servo1Left; servo1Pos <= servo1Right; servo1Pos += 1) {
    servo1.write(servo1Pos);
    delay(10);  // Adjust delay as needed for desired speed
  }
  for (servo1Pos = servo1Right; servo1Pos >= servo1Left; servo1Pos -= 1) {
    servo1.write(servo1Pos);
    delay(10);  // Adjust delay as needed for desired speed
  }

  delay(1000); // Add a delay before moving to the next servo

  // Test Servo 2
  for (servo2Pos = servo2Up; servo2Pos <= servo2Down; servo2Pos += 1) {
    servo2.write(servo2Pos);
    delay(10);  // Adjust delay as needed for desired speed
  }
  for (servo2Pos = servo2Down; servo2Pos >= servo2Up; servo2Pos -= 1) {
    servo2.write(servo2Pos);
    delay(10);  // Adjust delay as needed for desired speed
  }

  delay(1000); // Add a delay before moving to the next servo

  // Test Servo 3
  for (servo3Pos = servo3Min; servo3Pos <= servo3Max; servo3Pos += 1) {
    servo3.write(servo3Pos);
    delay(10);  // Adjust delay as needed for desired speed
  }
  for (servo3Pos = servo3Max; servo3Pos >= servo3Min; servo3Pos -= 1) {
    servo3.write(servo3Pos);
    delay(10);  // Adjust delay as needed for desired speed
  }

  delay(1000); // Add a delay after all tests are done

  // Reset all servos to their initial positions
  servo1.write(servo1Left);
  servo2.write(servo2Up);
  servo3.write(servo3Min);

  delay(1000); // Wait for a while before ending the loop

  // Stop the loop to prevent continuous execution
  while (true);
}