#include <Arduino.h>

// Define stepper motor parameters
const int stepPin = 3;         // Pin for the step signal
const int dirPin = 4;          // Pin for the direction signal

const int pulsesPerRevolution = 25000;  // Motor's pulses per revolution
const float stepAngle = 1.8;            // Step angle in degrees (1.8 degrees per step for your motor)
const float gearRatio = 50.0;           // Gearbox ratio (50:1)

int motorSpeed = 1000; // Steps per second (Adjust this to control speed)
unsigned long duration = 5000; // Run motor for 5 seconds

bool motorRunning = false; // Tracks whether the motor is running

void setup() {
  // Set pins as OUTPUT
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);

  // Set initial motor direction (can be HIGH or LOW)
  digitalWrite(dirPin, HIGH);  // Change to LOW for the opposite direction

  // Set initial motor speed and duration
  Serial.begin(9600);  // Optional, for debugging or monitoring
}

void loop() {
  // Check if data is available from Serial
  if (Serial.available() > 0) {
    char input = Serial.read();

    if (input == '8') {
      // Toggle motor state
      motorRunning = !motorRunning;

      if (motorRunning) {
        Serial.println("Motor STARTED");
      } else {
        Serial.println("Motor STOPPED");
      }
    }
  }

  // If the motor is running, generate pulses
  if (motorRunning) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(1000000 / motorSpeed / 2);  // Half of the step pulse time
    digitalWrite(stepPin, LOW);
    delayMicroseconds(1000000 / motorSpeed / 2);  // Half of the step pulse time
  }
}