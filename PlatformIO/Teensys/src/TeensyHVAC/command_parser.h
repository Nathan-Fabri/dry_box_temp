//command_parser.h
#pragma once
#include <Arduino.h>

/**
 * @brief Parses an incoming command string from the serial interface and updates system state.
 *
 * This function processes HVAC control commands such as "START-" and "ALLOFF", extracting
 * parameters from the formatted string and updating system-wide values for temperature,
 * humidity, airflow, and timing. It also handles "SENSOR-" commands to update current sensor readings.
 *
 * Recognized commands:
 * - "ALLOFF" : Turns off all systems and sets machineState to false.
 * - "SENSOR-CAT:..,CST:..,CH:.." : Updates current ambient/shell temperatures and humidity.
 * - "START-ATEMP:..,STEMP:..,HUM:..,TIME:..,OMEGA:...,FAN:..,DST:..,DAT:..,DH:..,DSFA:.." : Initializes an HVAC run cycle.
 *
 * @param input Raw command string (e.g. from serial input).
 * @param ambientTemp [out] Target ambient temperature.
 * @param shellTemp [out] Target shell temperature.
 * @param humidity [out] Target humidity percentage.
 * @param shellTime [out] Duration of the shelling phase (in minutes).
 * @param gFanSpeed [out] Target fan speed.
 * @param omega [out] Target motor spin speed.
 * @param machineState [out] Boolean flag representing whether machine is active.
 * @param deltaShellTemperature [out] Allowable deviation for shell temperature.
 * @param deltaAirTemperature [out] Allowable deviation for ambient air temperature.
 * @param deltaHumidity [out] Allowable deviation for humidity.
 * @param deltaShellFanAirFlow [out] Allowable deviation for fan airflow.
 * @param currAmbientTemperature [out] Most recent ambient temperature reading (if "SENSOR-" command).
 * @param currShellTemperature [out] Most recent shell temperature reading (if "SENSOR-" command).
 * @param currHumidity [out] Most recent humidity reading (if "SENSOR-" command).
 */
void parseIncomingData(
    String input,
    float& ambientTemp,
    float& shellTemp,
    int& humidity,
    int& shellTime,
    int& gFanSpeed,
    int& omega,
    bool& machineState,
    float& deltaShellTemperature,
    float& deltaAirTemperature,
    float& deltaHumidity,
    float& deltaShellFanAirFlow,
    float& currAmbientTemperature,
    float& currShellTemperature,
    float& currHumidity
);

/**
 * @brief Extracts the value of a specific key from a formatted command string.
 *
 * This helper searches for a pattern like "KEY:value" within the input string and returns the value
 * as a substring. Used internally by `parseIncomingData`.
 *
 * @param data The full formatted string (e.g. "KEY1:val1,KEY2:val2").
 * @param key The key to look for (e.g. "KEY1").
 * @return String The value associated with the key, or empty string if not found.
 */
String getValue(String data, String key);
