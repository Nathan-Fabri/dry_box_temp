#include <Arduino.h>
//----------------------------------------------------
#include <Wire.h>

bool fanOn = true;     // Keeps track of whether the fan is on
int fanSpeed = 100;    // Default fan speed (1 to 100)
int lightLevel = 100;  // Default light level 100 = off (0% brightness), 0 = full on (100% brightness)

// LEFT FANS
#define FAN_1 3
#define FAN_2 4
#define FAN_3 5
#define FAN_4 7

//---------------------------------------------------
// I2C addresses for the 4 triacs
const uint8_t DIMMER_ADDRESSES[4] = {0x27, 0x26, 0x25, 0x24};
const uint8_t CHANNELS[4] = {0x80, 0x81, 0x82, 0x83};  // Channel select bytes
const int DELAY_TIME = 100;  // ms between dimming steps

void setFanSpeed(int percent, int pin) {
  // Clamp input to 0-100
  percent = constrain(percent, 0, 100);
  int pwmValue = map(percent, 0, 100, 0, 255);
  analogWrite(pin, pwmValue);
}

//---------------------------------------------
void sendDimmerCommand(uint8_t address, uint8_t channel, uint8_t level) {
  Wire.beginTransmission(address);
  Wire.write(channel);
  Wire.write(level);
  Wire.endTransmission();
}

void setup() {
  pinMode(FAN_1, OUTPUT);
  pinMode(FAN_2, OUTPUT);
  pinMode(FAN_3, OUTPUT);
  pinMode(FAN_4, OUTPUT);

  Serial.begin(9600);

  // Set initial speed for all fans
  setFanSpeed(fanSpeed, FAN_1);
  setFanSpeed(fanSpeed, FAN_2);
  setFanSpeed(fanSpeed, FAN_3);
  setFanSpeed(fanSpeed, FAN_4);

  //----------------------------------------------

  Wire.begin();
  Serial.begin(115200);
  delay(5000);
  Serial.println("4-Channel I2C AC Dimmer Demo Starting...");

  // Initialize all channels on all triacs to fully OFF (dimming level 100)
  Serial.println("Initializing all channels to OFF...");
  for (int addr = 0; addr < 4; addr++) {
    for (int ch = 0; ch < 4; ch++) {
      sendDimmerCommand(DIMMER_ADDRESSES[addr], CHANNELS[ch], lightLevel);
      Serial.print("  Address 0x");
      Serial.print(DIMMER_ADDRESSES[addr], HEX);
      Serial.print(", Channel ");
      Serial.print(ch + 1);
      Serial.println(" set to OFF.");
      delay(50); // Short delay for reliability
    }
  }
  delay(1000);
}

void loop() {
  // Check if data is available from Serial
  if (Serial.available() > 0) {
    char input = Serial.read();

    if (input == '0') {
      // Toggle fan state
      fanOn = !fanOn;

      if (fanOn) {
        setFanSpeed(fanSpeed, FAN_1);
        setFanSpeed(fanSpeed, FAN_2);
        setFanSpeed(fanSpeed, FAN_3);
        setFanSpeed(fanSpeed, FAN_4);
        Serial.println("Fans ON");
      } else {
        setFanSpeed(0, FAN_1);  // Turn off
        setFanSpeed(0, FAN_2);
        setFanSpeed(0, FAN_3);
        setFanSpeed(0, FAN_4);
        Serial.println("Fans OFF");
      }
    }
  }

  // Optional: Add a delay or keep this loop fast
  delay(100);
}