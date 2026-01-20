/*
  This code demonstrates how to interact with an Arduino Mega 2560 and
  a Modbus RTU temperature and humidity sensor (SHT20). It reads the
  temperature and humidity values every 1 seconds and display data to
  the serial monitor.

  Note: Serial Port 0 is not used to connect the RS485 Converter (MAX485)
  because its used for debugging. The Serial Port 1 (TX1, RX1) is used
  for ModBus communication interface.

  Wiring of Sensor, Arduino, and MAX485 TTL to RS485 Converter:
  ___________________________________________________________________________________________
  | Sensor (SHT20)   |   MAX485 TTL to RS485 Converter
  |  A (Yellow)      |        A (Terminal block)
  |  B (White)       |        B (Terminal block)
  |  GND (Black)     |       GND (External Supply)
  |  Vs (Red)        |      9-30V (External Supply)
  ___________________________________________________________________________________________
  | MAX485 TTL to RS485 Converter  |  Arduino (Hardware Serial)  |  Arduino (Software Serial)
  |     RO (Reciever Output)       |        D19 (RX1)            |          D9 (RX)
  |     RE (Reciever Enable)       |        D2                   |          D2
  |     DE (Driver Enable)         |        D3                   |          D3
  |     DI (Driver Input)          |        D18 (TX1)            |          D10 (TX)
  ___________________________________________________________________________________________
*/

// MAX485 Pin | Connected To
// RO | D9 (RX)
// DI | D10 (TX)
// RE | D2
// DE | D3
// VCC | 5V
// GND | GND

#include <ModbusMaster.h>
#include <SoftwareSerial.h>

#define MAX485_RE_NEG  2
#define MAX485_DE      3
#define SSERIAL_RX_PIN 9
#define SSERIAL_TX_PIN 10

SoftwareSerial RS485Serial(SSERIAL_RX_PIN, SSERIAL_TX_PIN);
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

  Serial.begin(9600);
  RS485Serial.begin(9600);

  node.begin(1, RS485Serial);
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
