#pragma once
#include <Arduino.h>

// Fan constants - make them extern so they can be accessed from other files
extern const int FANS[4];
extern const int NUM_FANS;

/**
 * @brief Initializes PWM control for all fans.
 *
 * Must be called once during setup. Configures PWM frequency and resolution
 * for all fan control pins and initializes fans to OFF state.
 *
 * @param fanSpeed Initial fan speed (0-100%)
 */
void setupFanControl(int fanSpeed);

/**
 * @brief Sets the speed for a specific fan.
 *
 * @param pin Fan control pin number
 * @param percent Desired speed (0-100%)
 */
void setFanSpeed(int pin, int percent);

/**
 * @brief Sets all fans to the same speed.
 *
 * @param fanSpeed Desired speed (0-100%)
 */
void turnAllFansOn(int fanSpeed);

/**
 * @brief Stops all fans (sets speed to 0%).
 */
void turnAllFansOff();

/**
 * @brief Runs a diagnostic sequence turning fans on and off in order.
 */
void turnFansOnInOrder();

/**
 * @brief Converts desired airflow to PWM percentage.
 *
 * @param desiredFtMin Target airflow in cubic feet per minute
 * @param maxFtMin Maximum fan airflow capability
 * @return int PWM percentage (0-100)
 */
int getPWMFromFtMin(float desiredFtMin, float maxFtMin);

/**
 * @brief Main fan control function based on airflow demand.
 *
 * @param fanSpeed Target fan speed value
 */
void handleFanControl(int& fanSpeed); 