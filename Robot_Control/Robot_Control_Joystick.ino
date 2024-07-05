#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

int joyX;
int joyY;
int pot;
int targetServo1Pos;
int targetServo2Pos;
int targetServo3Pos;
int currentServo1Pos;
int currentServo2Pos;
int currentServo3Pos;

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

int speedFactor = 5;

void setup() 
{
  pinMode(buttonPin, INPUT);
  servo1.attach(11);
  servo2.attach(10);
  servo3.attach(9);
  Serial.begin(9600);

  for (int i = 0; i < numReadings; i++) 
  {
    readings[i] = 0;
  }

  currentServo1Pos = servo1.read();
  currentServo2Pos = servo2.read();
  currentServo3Pos = servo3.read();
}

void loop() 
{
  int buttonReading = digitalRead(buttonPin);

  if (buttonReading != lastButtonState) 
  {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) 
  {
    if (buttonReading != currentButtonState) 
    {
      currentButtonState = buttonReading;

      if (currentButtonState == HIGH) 
      {
        servosActive = !servosActive;
      }
    }
  }

  lastButtonState = buttonReading;

  if (servosActive) 
  {
    joyX = analogRead(A0);
    joyY = analogRead(A1);

    pot = analogRead(A2);

    total = total - readings[readIndex];
    readings[readIndex] = pot;
    total = total + readings[readIndex];
    readIndex = readIndex + 1;

    if (readIndex >= numReadings) 
    {
      readIndex = 0;
    }

    average = total / numReadings;

    targetServo1Pos = map(joyX, 200, 823, servo1Max, servo1Min);
    targetServo2Pos = map(joyY, 200, 823, servo2Min, servo2Max);

    if (targetServo2Pos < 90) 
    {
      targetServo3Pos = map(targetServo2Pos, servo2Min, 90, servo3Min, (servo3Min + servo3Max) / 2);
    } 
    else 
    {
      targetServo3Pos = map(targetServo2Pos, 90, servo2Max, (servo3Min + servo3Max) / 2, servo3Max);
    }

    currentServo1Pos = moveServo(currentServo1Pos, targetServo1Pos, speedFactor);
    currentServo2Pos = moveServo(currentServo2Pos, targetServo2Pos, speedFactor);
    currentServo3Pos = moveServo(currentServo3Pos, targetServo3Pos, speedFactor);

    servo1.write(currentServo1Pos);
    servo2.write(currentServo2Pos);
    servo3.write(currentServo3Pos);

    Serial.print("Servo1 Position: ");
    Serial.println(currentServo1Pos);
    Serial.print("Servo2 Position: ");
    Serial.println(currentServo2Pos);
    Serial.print("Servo3 Position: ");
    Serial.println(currentServo3Pos);
  }

  delay(15);
}

int moveServo(int currentPos, int targetPos, int speed) 
{
  if (currentPos < targetPos) 
  {
    currentPos += speed;
    if (currentPos > targetPos) 
    {
      currentPos = targetPos;
    }
  } else if (currentPos > targetPos) 
  {
    currentPos -= speed;
    if (currentPos < targetPos) 
    {
      currentPos = targetPos;
    }
  }
  return currentPos;
}