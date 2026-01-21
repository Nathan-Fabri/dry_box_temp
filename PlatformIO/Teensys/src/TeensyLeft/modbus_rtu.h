#pragma once
#include <Arduino.h>

/**
 * @brief Initializes Modbus communication and configures GPIO pins for RS-485 control.
 *
 * Sets the RE/DE pins for direction control and begins communication on Serial1.
 * Also attaches pre/post-transmission callbacks for proper RS-485 bus usage.
 *
 * Must be called once in `setup()`.
 */
void setupModbus();

/**
 * @brief Reads object and ambient temperature from a CT-N Modbus sensor.
 *
 * Sends a request to the sensor with the given slave address and attempts to read
 * two consecutive 16-bit input registers (object and ambient temperature).
 *
 * @param address The Modbus slave ID of the sensor.
 * @param objectTemp [out] Measured object temperature (°C).
 * @param ambientTemp [out] Measured ambient temperature (°C).
 * @return true if data was successfully read; false otherwise.
 */
bool readModbusSensor(uint8_t address, float& objectTemp, float& ambientTemp);

/**
 * @brief Debug function to read and print CT-N sensor values.
 */
void debugPrintCTNSensor(); 