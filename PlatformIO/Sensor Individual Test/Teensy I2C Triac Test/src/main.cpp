// #include <Wire.h>

// const uint8_t DIMMER_ADDRESS = 0x27;  // Or 0x3F depending on DIP switch
// const uint8_t CHANNELS[4] = {0x80, 0x81, 0x82, 0x83};  // Channel select bytes
// const int DELAY_TIME = 100;  // ms between dimming steps

// void sendDimmerCommand(uint8_t channel, uint8_t level) {
//   Wire.beginTransmission(DIMMER_ADDRESS);
//   Wire.write(channel);
//   Wire.write(level);
//   Wire.endTransmission();
// }

// void setup() {
//   Wire.begin();
//   Serial.begin(115200);
//   delay(1000);
//   Serial.println("4-Channel I2C AC Dimmer Demo Starting...");

//   // Initialize all channels to fully OFF (dimming level 100)
//   Serial.println("Initializing all channels to OFF...");
//   for (int ch = 0; ch < 4; ch++) {
//     sendDimmerCommand(CHANNELS[ch], 100);
//     Serial.print("  Channel ");
//     Serial.print(ch + 1);
//     Serial.println(" set to OFF.");
//     delay(50); // Short delay for reliability
//   }
//   delay(1000);
  
// }

// void loop(){}

//------------------------------------------- 4 Triac Test

#include <Wire.h>

// I2C addresses for the 4 triacs
const uint8_t DIMMER_ADDRESSES[4] = {0x27, 0x26, 0x25, 0x24};
const uint8_t CHANNELS[4] = {0x80, 0x81, 0x82, 0x83};  // Channel select bytes
const int DELAY_TIME = 100;  // ms between dimming steps

void sendDimmerCommand(uint8_t address, uint8_t channel, uint8_t level) {
  Wire.beginTransmission(address);
  Wire.write(channel);
  Wire.write(level);
  Wire.endTransmission();
}

void setup() {
  Wire.begin();
  Serial.begin(115200);
  delay(5000);
  Serial.println("4-Channel I2C AC Dimmer Demo Starting...");

  // Initialize all channels on all triacs to fully OFF (dimming level 100)
  Serial.println("Initializing all channels to OFF...");
  for (int addr = 0; addr < 4; addr++) {
    for (int ch = 0; ch < 4; ch++) {
      sendDimmerCommand(DIMMER_ADDRESSES[addr], CHANNELS[ch], 0);
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

void loop(){}

// void loop() {
//   // Loop through each triac and channel to toggle ON and OFF
//   for (int addr = 0; addr < 4; addr++) {
//     for (int ch = 0; ch < 4; ch++) {
//       // Turn the channel ON (fully bright)
//       Serial.print("Address 0x");
//       Serial.print(DIMMER_ADDRESSES[addr], HEX);
//       Serial.print(", Channel ");
//       Serial.print(ch + 1);
//       Serial.println(" - Turning ON");
//       sendDimmerCommand(DIMMER_ADDRESSES[addr], CHANNELS[ch], 0); // Brightness level 0 (fully ON)
//       delay(1000); // Wait for 1 second

//       // Turn the channel OFF (fully dimmed)
//       Serial.print("Address 0x");
//       Serial.print(DIMMER_ADDRESSES[addr], HEX);
//       Serial.print(", Channel ");
//       Serial.print(ch + 1);
//       Serial.println(" - Turning OFF");
//       sendDimmerCommand(DIMMER_ADDRESSES[addr], CHANNELS[ch], 100); // Brightness level 100 (fully OFF)
//       delay(1000); // Wait for 1 second
//     }
//   }
// }

//-----------------------------------------------------------------------

// void loop() {
//   // Loop through each of the 4 channels
//   for (int ch = 0; ch < 4; ch++) {
//     Serial.print("Channel ");
//     Serial.print(ch + 1);
//     Serial.println(" - Fading IN (brightening)");

//     // Fade in (from fully off (100) to fully on (0))
//     for (int level = 100; level >= 0; level--) {
//       sendDimmerCommand(CHANNELS[ch], level);
//       Serial.print("  Brightness: ");
//       Serial.println(100 - level);  // Interpreted as brightness %
//       delay(DELAY_TIME);
//     }

//     Serial.println("  Channel fully ON.");
//     delay(500);

//     Serial.print("Channel ");
//     Serial.print(ch + 1);
//     Serial.println(" - Fading OUT (dimming)");

//     // Fade out (from fully on (0) to fully off (100))
//     for (int level = 0; level <= 100; level++) {
//       sendDimmerCommand(CHANNELS[ch], level);
//       Serial.print("  Brightness: ");
//       Serial.println(100 - level);
//       delay(DELAY_TIME);
//     }

//     Serial.println("  Channel fully OFF.");
//     delay(500);
//   }
// }
