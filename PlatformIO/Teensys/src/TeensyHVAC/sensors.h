#pragma once

/**
 * @brief Identifiers for individual sensors and their locations.
 */
enum SensorID {
    Exterior,
    Chiller,
    Box_Outlet,
    Box_Inlet,
    Shell,
    Left_Tower,
    Right_Tower,
    SENSORID
};

struct SensorConfig {
    int modbusAddress;
    // Add more metadata if needed (e.g., sensor type, name)
};

// For modbus
extern const SensorConfig sensorconfigs[SENSORID];

// For sensor readings
extern const char* const sensorNames[SENSORID];