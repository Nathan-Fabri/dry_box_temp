#include "modbus_rtu.h"
#include <ModbusMaster.h>
#include "pinmap.h"
#include "sensors.h"

ModbusMaster node;

void preTransmission() {
  digitalWrite(PIN_MODBUS_RE, HIGH);
  digitalWrite(PIN_MODBUS_DE, HIGH);
}

void postTransmission() {
  digitalWrite(PIN_MODBUS_RE, LOW);
  digitalWrite(PIN_MODBUS_DE, LOW);
}

void setupModbus() {
  pinMode(PIN_MODBUS_RE, OUTPUT);
  pinMode(PIN_MODBUS_DE, OUTPUT);
  postTransmission();  // Start with transceiver in receive mode

  Serial1.begin(9600);      // UART to sensor
  node.begin(1, Serial1);   // Placeholder ID, we override in `readModbusSensor`

  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);
}

bool readSensor(SensorID id, float& temperature, float& humidity) {
    return readModbusSensor(sensorconfigs[id].modbusAddress, temperature, humidity);
}

bool readModbusSensor(uint8_t address, float& temperature, float& humidity) {
  node.begin(address, Serial1);

  // This function is now mainly for testing/debugging - use non-blocking version in production
  uint8_t result = node.readInputRegisters(0x0001, 2);
  if (result != node.ku8MBSuccess) {
    SerialUSB1.print("Sensor ");
    SerialUSB1.print(address);
    SerialUSB1.print(" - Read error: ");
    SerialUSB1.println(result);
    return false;
  }

  temperature = node.getResponseBuffer(0) / 10.0;  // First register (temp)
  humidity = node.getResponseBuffer(1) / 10.0;     // Second register (humidity)
  return true;
}

// Non-blocking modbus functions
void scanModbusBus() {
  SerialUSB1.println("Starting Modbus scan (addresses 1–20)...");

  for (uint8_t addr = 1; addr <= 20; addr++) {
    node.begin(addr, Serial1);  // Change node address dynamically
    uint8_t result = node.readInputRegisters(0x0001, 1);  // Read temperature register

    SerialUSB1.print("Address ");
    SerialUSB1.print(addr);
    SerialUSB1.print(": ");
    if (result == node.ku8MBSuccess) {
      SerialUSB1.println("✅ Responded");
    } else {
      SerialUSB1.print("❌ No response (error ");
      SerialUSB1.print(result);
      SerialUSB1.println(")");
    }

    delay(200);  // Optional: prevent overwhelming the bus
  }
}

void changeBaudRate(uint8_t address, uint16_t newBaudValue) {
  node.begin(address, Serial1);

  SerialUSB1.print("Changing baud rate for sensor ");
  SerialUSB1.print(address);
  SerialUSB1.print(" to register value 0x");
  SerialUSB1.println(newBaudValue, HEX);

  uint8_t result = node.writeSingleRegister(0x0102, newBaudValue);

  if (result == node.ku8MBSuccess) {
    SerialUSB1.println("✅ Baud rate change command sent successfully.");
  } else {
    SerialUSB1.print("❌ Failed to change baud rate. Error code: ");
    SerialUSB1.println(result);
  }
}