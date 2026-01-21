// MAX485 Pin | Connect To (Teensy 4.1)
// RO | Pin 0 (RX1)
// DI | Pin 1 (TX1)
// RE | Pin 2
// DE | Pin 3
// VCC | 5V (use logic level shifter if Teensy is 3.3V only)
// GND | GND
// A/B | RS485 bus (twisted pair)

#include <ModbusMaster.h>

// Pin definitions for MAX485
#define MAX485_RE_NEG  2
#define MAX485_DE      3

// Use hardware Serial1 on Teensy 4.1 (TX = pin 1, RX = pin 0)
ModbusMaster node;

void preTransmission() {
  digitalWrite(MAX485_RE_NEG, HIGH);
  digitalWrite(MAX485_DE, HIGH);
}

void postTransmission() {
  digitalWrite(MAX485_RE_NEG, LOW);
  digitalWrite(MAX485_DE, LOW);
}

void setup() {
  pinMode(MAX485_RE_NEG, OUTPUT);
  pinMode(MAX485_DE, OUTPUT);
  digitalWrite(MAX485_RE_NEG, LOW);
  digitalWrite(MAX485_DE, LOW);

  Serial.begin(9600);      // Debug output
  Serial1.begin(9600);     // RS485 communication

  node.begin(3, Serial1);  // Slave ID 1, use Serial1 for Modbus
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);
}

void loop() {
  uint8_t result = node.readInputRegisters(0x0001, 2);
  Serial.println("Data Requested");

  if (result == node.ku8MBSuccess) {
    Serial.print("Temperature: ");
    Serial.print(node.getResponseBuffer(0) / 10.0);
    Serial.print("   Humidity: ");
    Serial.println(node.getResponseBuffer(1) / 10.0);
  } else {
    Serial.print("Modbus Error: ");
    Serial.println(result);
  }

  delay(1000);
}
