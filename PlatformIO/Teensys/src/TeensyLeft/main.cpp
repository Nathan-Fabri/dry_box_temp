// main.cpp

#include <Arduino.h>
#include "pinmap.h"
#include "command_parser.h"
#include "fan_control.h"
#include "light_control.h"
#include "sensor_scan.h"
#include "modbus_rtu.h"
#include "thermal_camera.h"
#include "thermal_camera.h"

// -------------------------
// Machine Control
// -------------------------
bool machineState = false;             // Set to true when START command is received

// -------------------------
// Control thresholds (± tolerance)
// -------------------------
float deltaShellTemperature = 2.0; // Allowed deviation for shell temp (°C)
float deltaAirTemperature = 2.0; // Allowed deviation for ambient air temp (°C)
float deltaHumidity = 5.0; // Allowed deviation for humidity (% RH)
float deltaShellFanAirFlow = 5.0; // Allowed deviation for fan airflow (%)

// -------------------------
// Target values from command
// -------------------------
float ambientTemperature = 0.0;
float shellTemperature = 0;
int humidity = 0;
int shellTime = 0;
int FanSpeed = 10;
float currAmbientTemperature = 0.0;
float currShellTemperature = 0.0;
float currHumidity = 0.0;

// -------------------------
// Live sensor readings
// -------------------------
// Pointer to the infrared shell temperature reading
float* currShellTemperatureReadingInfrared = getShellTemperature();
float* currShellTemperatureReadingThermalCamera = getCurrentThermalTemp();

// -------------------------
// Serial input buffer
// -------------------------
String setCommand = "";

/**
 * @brief Arduino setup function.
 *
 * Initializes serial communication and hardware peripherals including:
 * - Fan PWM setup
 * - I2C light control setup
 */
void setup() {
  // Initalize subsystems
  setupFanControl(FanSpeed);
  setupLightControl();     
  setupModbus();
  initThermalCamera();

}

void loop() {
  // Process thermal camera data from Serial3
  processThermalCommands();
  
  // Debug: Print thermal status every 5 seconds
  static unsigned long lastThermalDebug = 0;
  if (millis() - lastThermalDebug > 5000) {
    SerialUSB1.print("🌡️ Thermal Status - Available: ");
    SerialUSB1.print(isThermalDataAvailable() ? "YES" : "NO");
    SerialUSB1.print(" | Temp: ");
    SerialUSB1.print(*getCurrentThermalTemp());
    SerialUSB1.print(" °C | Last Update: ");
    SerialUSB1.print(getLastThermalUpdate());
    SerialUSB1.print(" ms | SerialUSB2 available: ");
    SerialUSB1.println(SerialUSB2.available());
    lastThermalDebug = millis();
  }
  
  // Read and assemble command from serial input (line-based)
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      if (setCommand.length() > 0) {
        parseIncomingData(
          setCommand,
          ambientTemperature, shellTemperature, humidity,
          shellTime, FanSpeed, machineState,
          deltaShellTemperature, deltaAirTemperature,
          deltaHumidity, deltaShellFanAirFlow,
          currAmbientTemperature, currShellTemperature, currHumidity
        );
      }
      setCommand = "";
    } else {
      setCommand += c;
    }
  }

  // Control Loop (active only if machineState == true)
  if (machineState) {
    // Read sensors and update current values
    scanAllSensors();

    turnAllFansOn(FanSpeed); // Ensure fans are running at the set speed

    handleLightControlThermalCamera(*currShellTemperatureReadingThermalCamera, shellTemperature, deltaShellTemperature);
  }
}

