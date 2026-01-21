#include "thermal_camera.h"
#include <Arduino.h>

// Global thermal camera variables
float currentThermalTemp = 0.0;
bool thermalDataAvailable = false;
unsigned long lastThermalUpdate = 0;

void initThermalCamera() {
    // Initialize thermal camera communication
    SerialUSB2.begin(115200);  // SerialUSB2 for thermal data from Raspberry Pi (if04)
    currentThermalTemp = 0.0;
    thermalDataAvailable = false;
    lastThermalUpdate = 0;
    
    SerialUSB1.println("Thermal camera receiver initialized for TeensyRight on SerialUSB2");
}

void checkThermalTemperature() {
    // Check if thermal data is available from Raspberry Pi
    if (SerialUSB2.available()) {
        String tempStr = SerialUSB2.readStringUntil('\n');
        tempStr.trim();  // Remove whitespace
        if (tempStr.length() > 0) {
            float temperature = tempStr.toFloat();
            
            // Basic validation - reasonable temperature range
            if (temperature > -50.0 && temperature < 200.0) {
                currentThermalTemp = temperature;
                thermalDataAvailable = true;
                lastThermalUpdate = millis();
                
                // Debug output in database-parseable format
                SerialUSB1.print("✅ ");
                SerialUSB1.print("ThermalCamera");
                SerialUSB1.print(" | Temp: ");
                SerialUSB1.print(temperature);
                SerialUSB1.println(" °C");
            } else {
                SerialUSB1.print("❌ Temperature out of range: ");
                SerialUSB1.println(temperature);
            }
        } else {
            SerialUSB1.println("❌ Empty string received");
        }
    }
}

float* getCurrentThermalTemp() {
    return &currentThermalTemp;
}

bool isThermalDataAvailable() {
    return thermalDataAvailable;
}

unsigned long getLastThermalUpdate() {
    return lastThermalUpdate;
}

void processThermalCommands() {
    checkThermalTemperature();
}
