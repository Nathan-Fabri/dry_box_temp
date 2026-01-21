#pragma once
#include <Arduino.h>

/**
 * @brief sets PID values
 * 
 * @param vKp Kp Value
 * @param vKi Ki Value
 * @param vKd Kd Value
 */
void setPIDValues(float vKp, float vKi, float vKd);

/**
 * @brief Initializes I2C communication and configures all dimmer channels.
 *
 * Sets up all 4 triac dimmer boards and ensures all channels are initially OFF.
 * Populates the flipped order array for reverse sweep animations.
 */
void setupLightControl();

/**
 * @brief Applies PID-based brightness control based on shell temperature error.
 *
 * Compares the current shell temperature to the target value, and adjusts the light level
 * using a PID controller to maintain thermal balance. Applies deadband filtering based on `delta`.
 *
 * @param currShellTemperature Current measured shell temperature (°C).
 * @param gShellTemp Target shell temperature setpoint (°C).
 * @param delta Acceptable ± tolerance before light control reacts.
 */
void handleLightControl(float currShellTemperature, float gShellTemp, float delta);

/**
 * @brief sets thermal camera PID values
 * 
 * @param vKp Thermal Kp Value
 * @param vKi Thermal Ki Value
 * @param vKd Thermal Kd Value
 */
void setThermalPIDValues(float vKp, float vKi, float vKd);

/**
 * @brief Applies PID-based brightness control based on thermal camera temperature error.
 *
 * Compares the current thermal camera temperature to the target value, and adjusts the light level
 * using a separate PID controller tuned for thermal camera data. Applies deadband filtering based on `delta`.
 *
 * @param currShellTemperature Current measured shell temperature from thermal camera (°C).
 * @param gShellTemp Target shell temperature setpoint (°C).
 * @param delta Acceptable ± tolerance before light control reacts.
 */
void handleLightControlThermalCamera(float currShellTemperature, float gShellTemp, float delta);

/**
 * @brief Debug function to print current thermal camera light control state and PID values
 * 
 * @param currShellTemperature Current measured shell temperature from thermal camera (°C)
 * @param gShellTemp Target shell temperature setpoint (°C)
 * @param error Current temperature error
 * @param pid_output Current PID output
 * @param currentLevel Current dimming level
 */
void debugThermalLightControl(float currShellTemperature, float gShellTemp, float error, float pid_output, float currentLevel);

/**
 * @brief Debug function to print current light control state and PID values
 * 
 * @param currShellTemperature Current measured shell temperature (°C)
 * @param gShellTemp Target shell temperature setpoint (°C)
 * @param error Current temperature error
 * @param pid_output Current PID output
 * @param currentLevel Current dimming level
 */
void debugLightControl(float currShellTemperature, float gShellTemp, float error, float pid_output, float currentLevel);

/**
 * @brief Sets a specific dimmer level for a single light board and channel.
 *
 * @param boardIndex Index of the I2C dimmer board (0–3).
 * @param channelIndex Channel on that board (0–3).
 * @param level Dimmer level (0 = full brightness, 100 = off).
 */
void setLightLevel(uint8_t boardIndex, uint8_t channelIndex, uint8_t level);

/**
 * @brief Sets the brightness of a specific light using a global light index (0–15).
 *
 * Automatically maps the global index to the correct I2C board and channel.
 *
 * @param lightNumber Global light index (0–15).
 * @param level Dimmer level (0 = full brightness, 100 = off).
 */
void setLightByNumber(uint8_t lightNumber, uint8_t level);

/**
 * @brief Runs a light chase pattern where each light turns ON then OFF in a fixed order.
 *
 * Lights sweep on and off one-by-one based on a predefined left-to-right index mapping.
 * Useful for diagnostics or visual confirmation of light placement.
 */
void allONOFF();

/**
 * @brief Turns all lights fully ON (brightness level 0).
 */
void allOn();

/**
 * @brief Turns all lights fully OFF (brightness level 100).
 */
void allOff();

/**
 * @brief Sets all lights to the same dimmer level.
 *
 * @param dimLvl Dimmer level for all lights (0 = full brightness, 100 = off).
 */
void setAllOn(int dimLvl); 