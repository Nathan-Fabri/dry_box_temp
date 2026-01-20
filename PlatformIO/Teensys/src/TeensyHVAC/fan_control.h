#pragma once
#include <Arduino.h>
#include "pinmap.h"

// PWM Configuration
#define FAN_PWM_FREQUENCY 20000  // Try 25kHz instead of 20kHz
#define FAN_PWM_RESOLUTION 12    // 12-bit resolution (0-4095)

// Fan constants - make them extern so they can be accessed from other files
extern const int FANS[2];
extern const int NUM_FANS;

/**
 * @brief Initializes all fan control pins and sets their PWM frequency.
 *
 * This function configures each fan pin as an output, sets the PWM frequency to 20 kHz,
 * and optionally starts the fans at the provided initial speed.
 *
 * @param fanSpeed Initial fan speed percentage (0–100) to apply at startup.
 */
void setupFanControl(int fanSpeed);

/**
 * @brief Sets the speed of a single fan using PWM output.
 *
 * Converts a percentage (0–100%) to a PWM duty cycle (0–255) and writes it
 * to the specified pin. A 0% value is handled as a digital LOW signal.
 *
 * @param pin GPIO pin connected to the fan's PWM input.
 * @param percent Speed percentage (0–100).
 */
void setFanSpeed(int pin, int percent);

/**
 * @brief Turns all fans ON at the specified speed percentage.
 *
 * Uses `setFanSpeed()` for each configured fan pin.
 *
 * @param fanSpeed Speed percentage (0–100) to apply to all fans.
 */
void turnAllFansOn(int fanSpeed);

/**
 * @brief Turns all fans OFF by setting their PWM values to 0%.
 */
void turnAllFansOff();

/**
 * @brief Ramps fans ON one-by-one, then OFF one-by-one for diagnostic or demo purposes.
 *
 * Runs through all fans with timed delays to visually confirm operation and direction.
 * Restores original speed at the end.
 */
void turnFansOnInOrder();

/**
 * @brief Debug function to print current fan control state and PID values
 * 
 * @param ambientTemp Current measured ambient temperature (°C)
 * @param setTemp Target temperature setpoint (°C)
 * @param error Current temperature error
 * @param pid_output Current PID output
 * @param fanPWM Current fan PWM value
 */
void debugFanControl(float ambientTemp, float setTemp, float error, float pid_output, int fanPWM);

/**
 * @brief Converts a desired airflow in CFM to a PWM percentage (0–100).
 *
 * Uses linear scaling relative to the maximum fan CFM.
 *
 * @param desiredCFM Target airflow in cubic feet per minute.
 * @param maxCFM Maximum achievable CFM of the fan (default 265.43).
 * @return int PWM percentage (0–100).
 */
int getPWMFromCFM(float desiredCFM, float maxCFM = 100.0);

/**
 * @brief Applies fan speed control logic based on ambient temperature and setpoint.
 *
 * Uses PID control to adjust fan speed based on the difference between ambient temperature
 * and the target temperature (setTemp - deltaTemp).
 *
 * @param ambientTemp Current ambient temperature reading in °C.
 * @param setTemp Target temperature setpoint in °C.
 * @param deltaTemp Temperature offset from setpoint in °C.
 */
void handleFanControl(float ambientTemp, float setTemp, float deltaTemp);

/**
 * @brief Sets the PID control parameters for fan control
 * 
 * @param kp Proportional gain
 * @param ki Integral gain
 * @param kd Derivative gain
 */
void setFanPIDValues(float kp, float ki, float kd);

/**
 * @brief Controls fan speed based on current ambient temperature and setpoint.
 *
 * Uses a PID controller to maintain the ambient temperature around the setpoint.
 * The fan speed is adjusted to increase cooling when needed, and reduce it when
 * approaching or below the target temperature.
 *
 * @param ambientTemp Current measured ambient temperature (°C).
 * @param setTemp Target temperature setpoint (°C).
 * @param deltaTemp Acceptable ± tolerance before fan control reacts.
 */
