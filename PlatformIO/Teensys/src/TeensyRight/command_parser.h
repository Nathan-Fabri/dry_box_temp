#pragma once

/**
 * @file command_parser.h
 * @brief Parses incoming serial commands for machine control.
 */

#include <Arduino.h>

/**
 * @brief Parse incoming serial data and update control parameters.
 *
 * @param input Raw command string to parse
 * @param ambientTemp [out] Target ambient temperature
 * @param shellTemp [out] Target shell temperature
 * @param humidity [out] Target humidity level
 * @param shellTime [out] Duration of the cycle
 * @param FanSpeed [out] Target fan speed
 * @param machineState [out] Machine state (ON/OFF)
 * @param deltaShellTemperature [out] Shell temperature tolerance
 * @param deltaAirTemperature [out] Air temperature tolerance
 * @param deltaHumidity [out] Humidity tolerance
 * @param deltaShellFanAirFlow [out] Fan airflow tolerance
 * @param currAmbientTemperature [out] Current ambient temperature
 * @param currShellTemperature [out] Current shell temperature
 * @param currHumidity [out] Current humidity
 */
void parseIncomingData(
    String input,
    float& ambientTemp,
    float& shellTemp,
    int& humidity,
    int& shellTime,
    int& FanSpeed,
    bool& machineState,
    float& deltaShellTemperature,
    float& deltaAirTemperature,
    float& deltaHumidity,
    float& deltaShellFanAirFlow,
    float& currmbientTemperature,
    float& currShellTemperature,
    float& currHumidity
); 