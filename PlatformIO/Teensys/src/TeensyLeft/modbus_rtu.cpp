#include "modbus_rtu.h"
#include <ModbusMaster.h>
#include "pinmap.h"

ModbusMaster node;

// --- RS485 Transceiver Control ---
void preTransmission() {
  digitalWrite(PIN_MODBUS_RE, HIGH);
  digitalWrite(PIN_MODBUS_DE, HIGH);
}

void postTransmission() {
  digitalWrite(PIN_MODBUS_RE, LOW);
  digitalWrite(PIN_MODBUS_DE, LOW);
}

// --- Setup Modbus for CT-N Sensor ---
void setupModbus() {
  pinMode(PIN_MODBUS_RE, OUTPUT);
  pinMode(PIN_MODBUS_DE, OUTPUT);
  postTransmission();  // Start in receive mode

  Serial1.begin(19200);      // UART to sensor
  node.begin(1, Serial1);    // Modbus slave ID = 1 (change if needed)
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);

  delay(1000); // Let sensor boot up
  Serial.println("CT-N Sensor Modbus Reader Ready");
}

// --- Read CT-N Sensor (object & ambient temperature) ---
bool readModbusSensor(uint8_t address, float& objectTemp, float& ambientTemp) {
  node.begin(address, Serial1); // Set slave address if needed

  delay(30); // Wait for sensor to stabilize

  uint8_t result = node.readHoldingRegisters(0x9C42, 2); // Read object & ambient temp

  if (result == node.ku8MBSuccess) {
    objectTemp = node.getResponseBuffer(0) / 10.0;
    ambientTemp = node.getResponseBuffer(1) / 10.0;
    return true;
  } else {
    Serial.print("Modbus Error: ");
    Serial.println(result);
    objectTemp = -999;
    ambientTemp = -999;
    return false;
  }
}

// Add static variables for timing control
static unsigned long lastDebugPrintTime = 0;
static const unsigned long DEBUG_PRINT_INTERVAL_ms = 1000; // 1 Hz

// --- Example: Print sensor values (call in loop or as needed) ---
void debugPrintCTNSensor() {
  unsigned long currentTime = millis();
  
  // Exit early if method shouldn't run yet (1 Hz control)
  if (!(currentTime - lastDebugPrintTime >= DEBUG_PRINT_INTERVAL_ms)) {
    return;
  }
  
  float objectTemp = 0.0, ambientTemp = 0.0;
  if (readModbusSensor(1, objectTemp, ambientTemp)) {
    SerialUSB1.print("✅ ");
    SerialUSB1.print("Left Tower Infrared Sensor");
    SerialUSB1.print(" | Object Temp: ");
    SerialUSB1.print(objectTemp);
    SerialUSB1.print(" °C | Ambient Temp: ");
    SerialUSB1.print(ambientTemp);
    SerialUSB1.println(" °C");
  } else {
    SerialUSB1.println("❌ ");
    SerialUSB1.println("Left Tower Infrared Sensor");
    SerialUSB1.println(" | Error reading sensor data");
  }
  
  lastDebugPrintTime = currentTime;
}