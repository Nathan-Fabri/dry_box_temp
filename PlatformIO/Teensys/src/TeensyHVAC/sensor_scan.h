#pragma once
#include "sensors.h"
#include <cstddef>

/**
 * @brief Begins printing all sensors in non-blocking mode.
 */
void debugPrintAllSensors();

/**
 * @brief Begins printing a custom list of sensors in non-blocking mode.
 * @param ids Pointer to an array of SensorID values to read.
 * @param count Number of sensors in the array.
 */
void debugPrintSensors(const SensorID* ids, size_t count);

/**
 * @brief Call this periodically from loop() to drive non-blocking debug printing.
 */
void serviceSensorDebugPrint();

/**
 * @brief Non-blocking sensor scanning service - call every loop cycle
 * 
 * This function implements a state machine that reads one sensor at a time
 * without blocking the main loop. It automatically cycles through all sensors
 * and updates global variables.
 */
void serviceNonBlockingSensorScan();

/**
 * @brief Check if sensor scanning is currently active
 * 
 * @return true if currently scanning sensors, false if idle
 */
bool isSensorScanningActive();

/**
 * @brief Get the index of the sensor currently being scanned
 * 
 * @return int Current sensor index (0-5)
 */
int getCurrentSensorIndex();

/**
 * @brief Update global sensor variables for a specific sensor
 * 
 * @param id Sensor ID
 * @param temp Temperature reading
 * @param hum Humidity reading
 */
void updateGlobalSensorVariables(SensorID id, float temp, float hum);

/**
 * @brief Update sensor averages from current readings
 */
void updateSensorAverages();

/**
 * @brief Initialize non-blocking sensor scanning system
 */
void initNonBlockingSensorScan();

