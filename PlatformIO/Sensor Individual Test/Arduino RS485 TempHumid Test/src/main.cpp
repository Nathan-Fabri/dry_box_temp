#include <ModbusMaster.h>

// Waveshare ESP32-S3-Relay-6CH RS485 Pins
#define RS485_RX 18
#define RS485_TX 17

uint16_t adds[] = {0x0000, 0x0001, 0x0002, 0x0003, 0x0004, 0x0004, 0x0005, 0x0006, 0x0007, 0x0008, 0x0009};
uint8_t idsToTest[] = {1, 0, 2, 3}; // Testing ID 1, Broadcast 0, and common backups

ModbusMaster node;

// We use the built-in Hardware Serial1
// Note: We do NOT need "SoftwareSerial RS485Serial" anymore.

void setup() {
  Serial.begin(9600); // PC Debugging
  
  // Initialize Hardware Serial 1 with the Waveshare pins
  Serial1.begin(9600, SERIAL_8N1, RS485_RX, RS485_TX);

  // Tell ModbusMaster to use Serial1
  node.begin(1, Serial1);
  
  Serial.println("System Initialized. Probing sensor...");
}

void loop() {
  // Test ID 1 (Standard) and ID 0 (Broadcast)
  uint8_t idsToTest[] = {1, 0};

  for (int idIdx = 0; idIdx < 2; idIdx++) {
    uint8_t currentID = idsToTest[idIdx];
    node.begin(currentID, Serial1);
    
    Serial.print("--- Testing ID: ");
    Serial.println(currentID);

    for (int i = 0; i <= 9; i++) {
      uint16_t currentReg = adds[i];
      
      // Try Read Input Register (0x04)
      uint8_t result = node.readHoldingRegisters(currentReg, 2);
      
      Serial.print("Testing Reg 0x");
      Serial.print(currentReg, HEX);
      Serial.print(": ");

      if (result == node.ku8MBSuccess) {
        Serial.println("SUCCESS!");
        Serial.print("Temp: ");
        Serial.print(node.getResponseBuffer(0) / 10.0);
        Serial.print(" | Hum: ");
        Serial.println(node.getResponseBuffer(1) / 10.0);
        
        while(1); // Stop scanning once we find it
      } else {
        Serial.print("Error ");
        Serial.println(result);
      }
      delay(200); // Short delay between registers
    }
  }
  
  Serial.println("Scan finished. Waiting 5 seconds...");
  delay(5000);
}