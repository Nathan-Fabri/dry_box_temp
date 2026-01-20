#pragma once
#include <Arduino.h>

// Expose necessary variables for access from other files
extern float stepIntervalMicros;
extern int stepPin;
extern int dirPin;
extern bool continuousStepperEnabled;

/**
 * @brief Controls the stepper motor by toggling the step pin based on the desired speed.
 *
 * This function should be called repeatedly in the main loop to drive the stepper
 * at the correct interval calculated via `calculateStepperInterval()`.
 */
void stepMotorControl();

/**
 * @brief Set up continuous motor operation using IntervalTimer (Teensy specific)
 * 
 * This function sets up an interrupt-based timer that will keep the motor running
 * smoothly in the background, regardless of what else the main loop is doing.
 */
void setupContinuousStepper();

/**
 * @brief Start the motor running continuously in the background
 * 
 * This function enables the continuous stepper operation. The motor will continue
 * to run until stopContinuousStepper() is called.
 */
void startContinuousStepper();

/**
 * @brief Stop the continuous motor operation
 * 
 * This function disables the continuous stepper operation.
 */
void stopContinuousStepper();

/**
 * @brief Immediately stops the stepper motor by pulling the step pin LOW.
 *
 * Resets internal state so that stepping resumes correctly next time.
 *
 * @param stepPin The digital output pin connected to the STEP input of the stepper driver.
 */
void stopStepper(int stepPin);

/**
 * @brief Calculates the interval (in microseconds) between step pulses based on desired speed.
 *
 * This sets the global `stepIntervalMicros`, which controls how often the step pin should toggle.
 *
 * @param outputRPM Desired rotation speed in RPM at the output shaft.
 * @param stepsPerRev Number of microsteps per full revolution of the motor.
 * @param gearRatio The gear ratio (motor rotations : output rotations).
 */
void calculateStepperInterval(int outputRPM, int stepsPerRev, float gearRatio);

/**
 * @brief Higher-level motor control function to set speed and direction.
 *
 * @param outputRPM Desired rotation speed in RPM at the output shaft.
 * @param stepsPerRev Number of microsteps per full revolution of the motor.
 * @param gearRatio The gear ratio (motor rotations : output rotations).
 * @param direction Direction of rotation (true = forward, false = reverse).
 */
void controlMotor(int outputRPM, int stepsPerRev, float gearRatio, bool direction);

/**
 * @brief Run the motor continuously for a specific duration in milliseconds.
 * 
 * This is a blocking function that will run the motor for the specified duration.
 * It uses the current stepIntervalMicros value to determine the speed.
 * 
 * @param durationMs The duration to run the motor for, in milliseconds.
 */
void runStepperForDuration(unsigned long durationMs);
