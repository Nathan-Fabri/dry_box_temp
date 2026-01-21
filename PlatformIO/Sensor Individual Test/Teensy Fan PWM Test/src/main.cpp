// // // Include the necessary libraries
// #include <Arduino.h>

// // Pin for PWM control (connected to the yellow wire)
// const int pwmPin = 9;  // Modify this pin according to your setup

// // Function to set the fan speed
// void setFanSpeed(int percent) {
//   // Ensure the input is between 0 and 100
//   if (percent < 0) percent = 0;
//   if (percent > 100) percent = 100;

//   // Map the percentage (0-100) to PWM duty cycle (0-255)
//   int pwmValue = map(percent, 0, 100, 0, 255);

//   // Write the PWM value to the fan control pin
//   analogWrite(pwmPin, pwmValue);
// }

// void setup() {
//   // Set the PWM pin as an output
//   pinMode(pwmPin, OUTPUT);
  
//   // Set the PWM frequency to 20 kHz for the fan control pin
//   analogWriteFrequency(pwmPin, 20000);  // 20 kHz
// }

// void loop() {
//   int fanSpeed = 30;  // Set your fan speed variable here (from 1 to 100)

//   // Update the fan speed
//   setFanSpeed(fanSpeed);

//   // You can add a delay here to test the fan speed
//   delay(1000);  // Adjust as necessary
// }

/****************************************************************************************************************************/

#include <Arduino.h>

const int pwmPin = 9;  // Modify this pin according to your setup
bool fanOn = true;     // Keeps track of whether the fan is on
int fanSpeed = 100;     // Default fan speed (1 to 100)

void setFanSpeed(int percent) {
  // Clamp input to 0-100
  percent = constrain(percent, 0, 100);
  int pwmValue = map(percent, 0, 100, 0, 255);
  analogWrite(pwmPin, pwmValue);
}

void setup() {
  pinMode(pwmPin, OUTPUT);
  Serial.begin(9600);

  // Set initial speed
  setFanSpeed(fanSpeed);

  analogWriteFrequency(pwmPin, 20000);
}

void loop() {
  // Check if data is available from Serial
  if (Serial.available() > 0) {
    char input = Serial.read();

    if (input == '0') {
      // Toggle fan state
      fanOn = !fanOn;

      if (fanOn) {
        setFanSpeed(fanSpeed);
        Serial.println("Fan ON");
      } else {
        setFanSpeed(0);  // Turn off
        Serial.println("Fan OFF");
      }
    }
  }

  // Optional: Add a delay or keep this loop fast
  delay(100);
}
