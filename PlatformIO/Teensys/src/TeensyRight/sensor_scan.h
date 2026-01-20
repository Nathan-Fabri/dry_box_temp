#pragma once

/**
 * @brief Polls the CT-N Modbus temperature sensor at address 1.
 *
 * Updates the global shellTemperature variable with the latest reading.
 * If the sensor fails to respond, shellTemperature is set to -999.
 */
void scanAllSensors();

/**
 * @brief Returns a pointer to the latest shell temperature reading.
 *
 * @return float* Pointer to shellTemperature.
 */
float* getShellTemperature(); 