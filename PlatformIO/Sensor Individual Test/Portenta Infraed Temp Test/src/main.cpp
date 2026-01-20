#include <Arduino_PortentaMachineControl.h>

// ==== Function Declarations ====
void readTemperatures();
uint16_t calculateCRC(uint8_t *data, uint8_t length);
bool verifyCRC(uint8_t *data, uint8_t len, uint8_t crcLow, uint8_t crcHigh);

// ==== Constants ====
#define SLAVE_ID 1
#define REGISTER_START 0x9C42  // Register 40002
#define NUM_REGISTERS 2

// ==== Globals ====
unsigned long lastRead = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("Initializing RS-485 interface...");
  MachineControl_RS485Comm.begin(19200, 0, 500); // 19200 bps, 0ms pre, 500µs post
  MachineControl_RS485Comm.receive();
  delay(1000); // Let sensor boot
  Serial.println("Ready to read from CT-N sensor.");
}

void loop() {
  if (millis() - lastRead > 500) {
    lastRead = millis();
    readTemperatures();
  }
}

// ==== Function Definitions ====

void readTemperatures() {
  uint8_t request[] = {
    SLAVE_ID,       // Device ID
    0x03,           // Function code: Read Holding Registers
    highByte(REGISTER_START),
    lowByte(REGISTER_START),
    0x00, NUM_REGISTERS // Number of registers
  };

  uint16_t crc = calculateCRC(request, 6);
  request[6] = crc & 0xFF;
  request[7] = crc >> 8;

  // Transmit
  MachineControl_RS485Comm.noReceive();
  MachineControl_RS485Comm.beginTransmission();
  MachineControl_RS485Comm.write(request, 8);
  MachineControl_RS485Comm.endTransmission();
  MachineControl_RS485Comm.receive();

  delay(10); // Wait for sensor reply

  uint8_t response[9];
  int len = MachineControl_RS485Comm.readBytes(response, 9);

  if (len == 9 && verifyCRC(response, 7, response[7], response[8])) {
    int16_t object = (response[3] << 8) | response[4];
    int16_t ambient = (response[5] << 8) | response[6];
    Serial.print("Object Temp: ");
    Serial.print(object / 10.0, 1);
    Serial.print(" °C   Ambient Temp: ");
    Serial.println(ambient / 10.0, 1);
  } else {
    Serial.println("No response or CRC error.");
  }
}

uint16_t calculateCRC(uint8_t *data, uint8_t length) {
  uint16_t crc = 0xFFFF;
  for (uint8_t i = 0; i < length; i++) {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++) {
      crc = (crc & 1) ? (crc >> 1) ^ 0xA001 : crc >> 1;
    }
  }
  return crc;
}

bool verifyCRC(uint8_t *data, uint8_t len, uint8_t crcLow, uint8_t crcHigh) {
  uint16_t crc = calculateCRC(data, len);
  return (crc & 0xFF) == crcLow && (crc >> 8) == crcHigh;
}
