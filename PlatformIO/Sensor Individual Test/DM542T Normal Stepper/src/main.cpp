#include <Arduino.h>

// Define the pins connected to the DM542T stepper controller
const int stepPin = 3;  // Pin for the step signal
const int dirPin = 4;   // Pin for the direction signal

// Define the number of pulses per revolution
const int pulsesPerRevolution = 800; 

// Set the speed of the motor (steps per second)
const int speed = 4000; // Adjust this to your desired speed (in steps per second)

// Set the duration of the movment 
const int duration = 5000;

void setup() {
  // Initialize the pins
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);

  // Set the direction of rotation (can be HIGH or LOW)
  digitalWrite(dirPin, HIGH);  // Change to LOW for the opposite direction
}

void loop() {
  // Time to rotate the motor (5 seconds)
  unsigned long startTime = millis();
  while (millis() - startTime < duration) {
    // Generate a pulse for each step
    digitalWrite(stepPin, LOW);
    delayMicroseconds(1000000 / speed / 2);  // Half of the step pulse time
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(1000000 / speed / 2);  // Half of the step pulse time
  }
  
  digitalWrite(stepPin, LOW);
}
