#pragma once
#include <Arduino.h>
#include "sensors.h"

/**
 * @brief Global array of sensor configurations indexed by SensorID.
 */
extern const SensorConfig sensorconfigs[SENSORID];

/**
 * @brief Wrapper for ModbusMaster library to handle Modbus communication.
 */
bool readSensor(SensorID id, float& temperature, float& humidity);

/**
 * @brief Global array of object temperatures (indexed by sensor position).
 *
 * Should be defined and initialized elsewhere (e.g. in sensor_scan.cpp).
 */
extern float objectTemps[];

/**
 * @brief Global array of ambient temperatures (indexed by sensor position).
 *
 * Should be defined and initialized elsewhere (e.g. in sensor_scan.cpp).
 */
extern float ambientTemps[];

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
 * @brief Reads temperature and humidity from a single Modbus sensor.
 *
 * Sends a request to the sensor with the given slave address and attempts to read
 * two consecutive 16-bit input registers (temperature and humidity).
 *
 * @param address The Modbus slave ID of the sensor.
 * @param temperature [out] Measured temperature (°C).
 * @param humidity [out] Measured relative humidity (%RH).
 * @return true if data was successfully read; false otherwise.
 */
bool readModbusSensor(uint8_t address, float& temperature, float& humidity);

/**
 * @brief Modbus scanner
 */
 void scanModbusBus();  // Scans addresses 1–20 and prints responses

 /**
  * @brief Changes modbus sensor baud rate
  */
 void changeBaudRate(uint8_t address, uint16_t newBaudValue);
