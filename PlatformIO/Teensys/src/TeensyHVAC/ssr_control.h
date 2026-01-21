#pragma once
#include <Arduino.h>

/**
 * @brief Initializes all SSR pins as outputs and sets them to OFF state.
 * 
 * Must be called once during setup. Configures all SSR pins as outputs
 * and ensures they start in the OFF state for safety.
 */
void setupSSR();

/**
 * @brief Sets the ON/OFF state of Dehumidifier 1 via SSR.
 *
 * @param on True to activate, false to deactivate.
 */
void setDehumidifier1(bool on);

/**
 * @brief Sets the ON/OFF state of Dehumidifier 2 via SSR.
 *
 * @param on True to activate, false to deactivate.
 */
void setDehumidifier2(bool on);

/**
 * @brief Sets the ON/OFF state of Dehumidifier 3 via SSR.
 *
 * @param on True to activate, false to deactivate.
 */
void setDehumidifier3(bool on);

/**
 * @brief Sets the ON/OFF state of the humidifier via SSR.
 *
 * @param on True to activate, false to deactivate.
 */
void setHumidifier(bool on);

/**
 * @brief Sets the ON/OFF state of the heater via SSR.
 *
 * @param on True to activate, false to deactivate.
 */
void setHeater(bool on);

/**
 * @brief Controls Dehumidifier 1 based on current and set humidity.
 *
 * Turns the dehumidifier ON if current humidity exceeds the target by delta,
 * and OFF if it falls below.
 *
 * @param currHumidity Current measured humidity (%)
 * @param humidity Target setpoint humidity (%)
 * @param deltaHumidity Allowed tolerance before switching (%)
 */
void controlDehumidifier1(float currHumidity, int humidity, float deltaHumidity);

/**
 * @brief Controls Dehumidifier 2 based on current and set humidity.
 *
 * @param currHumidity Current measured humidity (%)
 * @param humidity Target setpoint humidity (%)
 * @param deltaHumidity Allowed tolerance before switching (%)
 */
void controlDehumidifier2(float currHumidity, int humidity, float deltaHumidity);

/**
 * @brief Controls Dehumidifier 3 based on current and set humidity.
 *
 * @param currHumidity Current measured humidity (%)
 * @param humidity Target setpoint humidity (%)
 * @param deltaHumidity Allowed tolerance before switching (%)
 */
void controlDehumidifier3(float currHumidity, int humidity, float deltaHumidity);

/**
 * @brief Controls the humidifier based on current and set humidity.
 *
 * Turns ON if humidity is too low, OFF if too high.
 *
 * @param currHumidity Current measured humidity (%)
 * @param humidity Target setpoint humidity (%)
 * @param deltaHumidity Allowed tolerance before switching (%)
 */
void controlHumidifier(int currHumidity, int humidity, float deltaHumidity);

/**
 * @brief Controls the heater based on current and set ambient heat requirement.
 *
 * Turns ON if humidity is too low, OFF if too high.
 *
 * @param currAmbientTemperature current measured ambient temperature (KELVIN?)
 * @param ambientTemperature setpoint that we want the ambient temperature to be at (KELVIN)
 * @param deltaAirTemperature maximum allowed delta
 */
void controlHeater(float currAmbientTemperature, float ambientTemperature, float deltaAirTemperature);

/**
 * @brief Turns every SSR Off
 */
void setAllSSRsOff();