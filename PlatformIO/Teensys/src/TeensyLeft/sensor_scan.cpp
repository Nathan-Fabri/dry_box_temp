#include "modbus_rtu.h"

float shellTemps = 25.0; // Initialize with a reasonable default
float lastValidReading = 25.0; // Keep track of last valid reading

void scanAllSensors() {
    float temp = 0.0;
    float hum = 0.0; // Not used, but required by readModbusSensor signature

    bool success = readModbusSensor(1, temp, hum);  // Only read from sensor at address 1
    if (success && temp > -100 && temp < 200) {  // Basic sanity check
        shellTemps = temp;
        lastValidReading = temp;  // Update last valid reading
    } else {
        shellTemps = lastValidReading;  // Use last valid reading instead of -999
    }
}

float* getShellTemperature() {
    return &shellTemps;
} 