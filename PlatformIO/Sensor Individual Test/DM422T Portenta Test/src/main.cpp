#include <Arduino.h>
#include <Arduino_PortentaMachineControl.h>

// Define the pins connected to the DM542T stepper controller
#define stepPin 1 // Pin for the step signal
#define dirPin 2  // Pin for the direction signal

// Define the number of pulses per revolution
const int pulsesPerRevolution = 800; 

// Set the speed of the motor (steps per second)
const int speed = 4000; // Adjust this to your desired speed (in steps per second)

// Set the duration of the movment 
const int duration = 5000;

void setup() {
  // Initalizes the Digital Outputs
  MachineControl_DigitalOutputs.begin();

  // Turn all channels off at startup
  MachineControl_DigitalOutputs.writeAll(0);

  // Set the direction of rotation (can be HIGH or LOW)
  MachineControl_DigitalOutputs.write(dirPin, LOW);
}

void loop() {
  // Time to rotate the motor (5 seconds)
  unsigned long startTime = millis();
  while (millis() - startTime < duration) {
    // Generate a pulse for each step
    MachineControl_DigitalOutputs.write(stepPin, LOW);
    delayMicroseconds(1000000 / speed / 2);  // Half of the step pulse time
    MachineControl_DigitalOutputs.write(stepPin, HIGH);
    delayMicroseconds(1000000 / speed / 2);  // Half of the step pulse time
  }

  MachineControl_DigitalOutputs.write(stepPin, LOW);
}
