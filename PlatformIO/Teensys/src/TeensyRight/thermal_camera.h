#ifndef THERMAL_CAMERA_H
#define THERMAL_CAMERA_H

// Thermal camera receiver for TeensyRight
// Receives temperature data from Raspberry Pi thermal camera

// Global variables
extern float currentThermalTemp;
extern bool thermalDataAvailable;
extern unsigned long lastThermalUpdate;

// Function declarations
void initThermalCamera();
void checkThermalTemperature();
void handleTemperatureReading(float temp);
void processThermalCommands();

// Getter functions
float* getCurrentThermalTemp();
bool isThermalDataAvailable();
unsigned long getLastThermalUpdate();

#endif // THERMAL_CAMERA_H
