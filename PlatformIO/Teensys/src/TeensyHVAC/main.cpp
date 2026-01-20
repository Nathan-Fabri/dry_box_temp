// main.cpp
#include <Arduino.h>
#include "pinmap.h"
#include "stepper.h"
#include "fan_control.h"
#include "ssr_control.h"
#include "command_parser.h"
#include "send_readings.h"
#include "relay_control.h"
#include "modbus_rtu.h"
#include "sensor_scan.h"
#include "global.h"
#include "load_cell.h"

// Machine Control
bool machineState = false;  // Set to true when START command is received

// Control thresholds (± tolerance)
float deltaShellTemperature = 1.0;  // Allowed deviation for shell temp (°C)
float deltaAirTemperature = 0.5;    // Allowed deviation for ambient air temp (°C)
float deltaHumidity = 5.0;          // Allowed deviation for humidity (% RH)
float deltaShellFanAirFlow = 5.0;   // Allowed deviation for fan airflow (%)

// Target values from command
float ambientTemperature = 0;   
float shellTemperature = 0.0;
int humidity = 0;            
int shellTime = 0;
int omega = 0;                    
int fanSpeed = 10;                 
float currAmbientTemperature = 0.0;
float currShellTemperature = 0.0;
float currHumidity = 0.0;
float currShellWeight = 0.0;

// Test Sensor Readings
float currHumidityReadingTest = 99.0; // Test value for humidity reading
float currAmbientTemperatureReadingTest = 25.0; // Test value for ambient temperature reading

// Serial input buffer
String setCommand = "";

void setup() {
  // Initialize subsystems
  setupRelays();
  setupFanControl(fanSpeed);
  setupSSR();
  analogWriteResolution(12); 
  setupModbus();
  setupLoadCell();
  
  // Initialize sensor scanning
  initNonBlockingSensorScan();
  
  // Initialize stepper motor
  setupContinuousStepper();
}

void loop() {
  //scanModbusBus();
  // Serial Command Parser
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      if (setCommand.length() > 0) {
        parseIncomingData(
          setCommand,
          ambientTemperature,
          shellTemperature,
          humidity,
          shellTime,
          fanSpeed,
          omega,
          machineState,
          deltaShellTemperature,
          deltaAirTemperature,
          deltaHumidity,
          deltaShellFanAirFlow,
          currAmbientTemperature,
          currShellTemperature,
          currHumidity
        );
      }
      setCommand = "";
    } else {
      setCommand += c;
    }
  }
  
  // Sensor scanning runs always (independent of machine state)
  serviceNonBlockingSensorScan();     // Update sensors one at a time (non-blocking)
  
  // Control Loop (active only if machineState == true)
  static bool debugStarted = false;

  if (machineState) {
    // Control functions - these run every loop cycle with latest sensor data
    controlDehumidifier1(Chiller_RH, humidity, deltaHumidity);
    controlDehumidifier2(Chiller_RH, humidity, deltaHumidity);
    handleFanControl(Chiller_Temp, ambientTemperature, deltaAirTemperature);
    debugPrintLoadCell();
  } else {
    debugStarted = false; // Reset flag when machine turns off
  }
}