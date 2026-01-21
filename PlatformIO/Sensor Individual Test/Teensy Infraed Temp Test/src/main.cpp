// CT-N Sensor Wire | Signal | MAX485 Pin | Teensy 4.1 Pin | Notes
// Red | VDD (5V) | VCC | VIN or External 5V | Power supply (5V), ensure common ground
// Yellow/Black | GND | GND | GND | Connect all GNDs together
// Blue or Green | RS485 D+ | A | — | RS-485 bus line A
// White | RS485 D− | B | — | RS-485 bus line B
// — (no wire) | — | — | — | Not used
// — | — | RO | Pin 0 (RX1) | Connect through level shifter (3.3V safe)
// — | — | DI | Pin 1 (TX1) | RS-485 transmit line
// — | — | RE | Pin 2 | Set LOW to receive
// — | — | DE | Pin 3 | Set HIGH to transmit

#include <ModbusMaster.h>

// RS485 Transceiver control pins
#define MAX485_RE_NEG 2  // Receiver Enable
#define MAX485_DE     3  // Driver Enable

// Create ModbusMaster object using Serial1
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
  Serial.begin(115200);        // Debug output
  Serial1.begin(19200);        // Modbus communication

  pinMode(MAX485_RE_NEG, OUTPUT);
  pinMode(MAX485_DE, OUTPUT);
  postTransmission();          // Start in receive mode

  node.begin(1, Serial1);      // Modbus slave ID = 1
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);

  delay(1000);                 // Let sensor boot up
  Serial.println("CT-N Sensor Modbus Reader Ready");
}

void loop() {
  uint8_t result;
  uint16_t data[2];

  result = node.readHoldingRegisters(0x9C42, 2); // Read object & ambient temperature

  if (result == node.ku8MBSuccess) {
    float objectTemp = node.getResponseBuffer(0) / 10.0;
    float ambientTemp = node.getResponseBuffer(1) / 10.0;

    Serial.print("Object Temp: ");
    Serial.print(objectTemp);
    Serial.print(" °C\tAmbient Temp: ");
    Serial.print(ambientTemp);
    Serial.println(" °C");
  } else {
    Serial.print("Modbus Error: ");
    Serial.println(result);
  }

  delay(500);  // ≥100 ms between requests
}
