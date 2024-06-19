#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

int joyX;
int joyY;
int pot;
int servo1Pos;
int servo2Pos;
int servo3Pos;

int servo1Min = 10;
int servo1Max = 200;
int servo2Min = 10;
int servo2Max = 200;
int servo3Min = 10;
int servo3Max = 200;

const int numReadings = 10;
int readings[numReadings];
int readIndex = 0;
int total = 0;
int average = 0;

const int buttonPin = 13;
bool servosActive = true;
bool lastButtonState = LOW;
bool currentButtonState = LOW;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

void setup() {
  pinMode(buttonPin, INPUT);
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9);
  Serial.begin(9600);

  for (int i = 0; i < numReadings; i++) {
    readings[i] = 0;
  }
}

void loop() {
  int buttonReading = digitalRead(buttonPin);

  if (buttonReading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (buttonReading != currentButtonState) {
      currentButtonState = buttonReading;

      if (currentButtonState == HIGH) {
        servosActive = !servosActive;
      }
    }
  }

  lastButtonState = buttonReading;

  if (servosActive) {
    joyX = analogRead(A0);
    joyY = analogRead(A1);

    pot = analogRead(A2);

    total = total - readings[readIndex];
    readings[readIndex] = pot;
    total = total + readings[readIndex];
    readIndex = readIndex + 1;

    if (readIndex >= numReadings) {
      readIndex = 0;
    }

    average = total / numReadings;

    servo1Pos = map(joyX, 200, 823, servo1Max, servo1Min);
    servo2Pos = map(joyY, 200, 823, servo2Min, servo2Max);

    servo1.write(servo1Pos);
    servo2.write(servo2Pos);

    if (servo2Pos < 90) {
      servo3Pos = map(servo2Pos, servo2Min, 90, servo3Min, (servo3Min + servo3Max) / 2);
    } else {
      servo3Pos = map(servo2Pos, 90, servo2Max, (servo3Min + servo3Max) / 2, servo3Max);
    }

    servo3.write(servo3Pos);

    Serial.print("Servo1 Position: ");
    Serial.println(servo1Pos);
    Serial.print("Servo2 Position: ");
    Serial.println(servo2Pos);
    Serial.print("Servo3 Position: ");
    Serial.println(servo3Pos);
  }

  delay(15);
}