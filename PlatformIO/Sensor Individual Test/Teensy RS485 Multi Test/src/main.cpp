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

// List of sensor Modbus addresses to query
const uint8_t sensorAddresses[] = {2, 3};  // Add more (e.g., 4, 5, ..., 10) as needed
const int numSensors = sizeof(sensorAddresses) / sizeof(sensorAddresses[0]);

void preTransmission() {
  digitalWrite(MAX485_RE_NEG, HIGH);
  digitalWrite(MAX485_DE, HIGH);
}

void postTransmission() {
  digitalWrite(MAX485_RE_NEG, LOW);
  digitalWrite(MAX485_DE, LOW);
}

void setup() {
  delay(5000); // Wait for the serial monitor to open
  pinMode(MAX485_RE_NEG, OUTPUT);
  pinMode(MAX485_DE, OUTPUT);
  digitalWrite(MAX485_RE_NEG, LOW);
  digitalWrite(MAX485_DE, LOW);

  Serial.begin(9600);      // Debug output
  Serial1.begin(9600);     // RS485 communication

  node.begin(1, Serial1);  // Placeholder ID (will change per request)
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);
}

void loop() {
  for (int i = 0; i < numSensors; i++) {
    uint8_t address = sensorAddresses[i];
    node.setSlave(address);
    
    Serial.print("Requesting from sensor address: ");
    Serial.println(address);

    uint8_t result = node.readInputRegisters(0x0001, 2); // Temp & Humidity

    if (result == node.ku8MBSuccess) {
      float temperature = node.getResponseBuffer(0) / 10.0;
      float humidity = node.getResponseBuffer(1) / 10.0;

      Serial.print("Sensor ");
      Serial.print(address);
      Serial.print(" - Temp: ");
      Serial.print(temperature);
      Serial.print(" C   Humidity: ");
      Serial.print(humidity);
      Serial.println(" %");
    } else {
      Serial.print("Sensor ");
      Serial.print(address);
      Serial.print(" - Modbus Error: ");
      Serial.println(result);
    }

    delay(500);  // Small delay between sensor polls
  }

  Serial.println("--- End of Polling Cycle ---\n");
  delay(3000); // Wait before starting next polling round
}
