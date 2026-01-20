#include "stepper.h"
#include "pinmap.h"
#include <Arduino.h>
#include <IntervalTimer.h>

// Define stepper control pins
int stepPin = PIN_STEPPER_STEP;
int dirPin = PIN_STEPPER_DIR;

// State variables
bool stepState = LOW;
unsigned long lastStepTime = 0;
float stepsPerSec = 0.0;
float stepIntervalMicros = 0.0;
bool continuousStepperEnabled = false;
IntervalTimer stepperTimer;
unsigned long stepCount = 0;

// Helper function for the stepper timer interrupt
void stepMotorISR() {
  if (!continuousStepperEnabled || stepIntervalMicros <= 0) return;
  
  // Toggle the step pin (create a square wave)
  stepState = !stepState;
  digitalWrite(stepPin, stepState);
  
  // Count steps (only on rising edge)
  if (stepState) {
    stepCount++;
  }
}

void setupContinuousStepper() {
  // Set up the step and direction pins
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  digitalWrite(dirPin, HIGH); // Set initial direction
  
  // Initialize pins to known state
  digitalWrite(stepPin, LOW);
  stepState = LOW;
  
  // Motor is initially disabled
  continuousStepperEnabled = false;
  stepCount = 0;
}

void startContinuousStepper() {
  if (stepIntervalMicros <= 0) return;
  
  // Only start if not already running
  if (!continuousStepperEnabled) {
    // Reset step counter
    stepCount = 0;
    
    // Start the timer to toggle step pin at the correct frequency
    // The stepMotorISR will be called every stepIntervalMicros microseconds
    // We need one step toggle every stepIntervalMicros for the correct frequency
    stepperTimer.begin(stepMotorISR, stepIntervalMicros);
    
    continuousStepperEnabled = true;
  }
}

void stopContinuousStepper() {
  if (continuousStepperEnabled) {
    // Stop the timer
    stepperTimer.end();
    
    // Reset pin state
    digitalWrite(stepPin, LOW);
    stepState = LOW;
    
    continuousStepperEnabled = false;
  }
}

void calculateStepperInterval(int outputRPM, int stepsPerRev, float gearRatio) {
    // Ensure non-zero RPM to avoid division by zero
    if (outputRPM <= 0) {
        stepsPerSec = 0.0;
        stepIntervalMicros = 0.0;
        return;
    }
    
    // Calculate motor RPM (faster than output due to gear reduction)
    float motorRPM = outputRPM * gearRatio;
    
    // Calculate steps per second
    stepsPerSec = (motorRPM * stepsPerRev) / 60.0;
    
    // Calculate time in microseconds between step toggles (half of full step cycle)
    stepIntervalMicros = 1000000.0 / stepsPerSec / 2;
    
    // Setup both pins
    pinMode(stepPin, OUTPUT);
    pinMode(dirPin, OUTPUT);
    digitalWrite(dirPin, HIGH); // Set direction (HIGH or LOW depending on desired direction)
}

void stepMotorControl() {
    if (stepIntervalMicros <= 0) return;
    
    // Execute a fixed number of steps each time (like a burst)
    const int STEPS_PER_BURST = 100;
    
    // Run a fixed number of steps
    for (int i = 0; i < STEPS_PER_BURST; i++) {
        digitalWrite(stepPin, HIGH);
        delayMicroseconds(stepIntervalMicros);
        digitalWrite(stepPin, LOW);
        delayMicroseconds(stepIntervalMicros);
    }
}

void runStepperForDuration(unsigned long durationMs) {
    if (stepIntervalMicros <= 0) return;
    
    unsigned long startTime = millis();
    
    // Run the motor for the specified duration
    while (millis() - startTime < durationMs) {
        digitalWrite(stepPin, HIGH);
        delayMicroseconds(stepIntervalMicros);
        digitalWrite(stepPin, LOW);
        delayMicroseconds(stepIntervalMicros);
    }
}

void stopStepper(int stepPin) {
    // Stop continuous operation if it's running
    if (continuousStepperEnabled) {
        stopContinuousStepper();
    }
    
    // Also handle the traditional stop case
    digitalWrite(stepPin, LOW);
    stepState = LOW;
    lastStepTime = micros();
}

void controlMotor(int outputRPM, int stepsPerRev, float gearRatio, bool direction) {
    // Set direction
    digitalWrite(dirPin, direction ? HIGH : LOW);
    
    // Calculate step interval based on desired output RPM
    calculateStepperInterval(outputRPM, stepsPerRev, gearRatio);
}