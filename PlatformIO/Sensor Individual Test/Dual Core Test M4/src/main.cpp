#include <Arduino.h>
#include <Arduino_PortentaMachineControl.h>

// Sketch to flash led on Digital Output 02 on the M4 Core
#define LED 2   // Defines digital output 02 

// the setup function runs once when you press reset or power the board
void setup() {
  // Initalizes the Digital Outputs
  MachineControl_DigitalOutputs.begin();
}

// the loop function runs over and over again forever
void loop() {
 MachineControl_DigitalOutputs.write(LED, LOW); // turn the red LED on (LOW is the voltage level)
 delay(200); // wait for 200 milliseconds
 MachineControl_DigitalOutputs.write(LED, HIGH); // turn the LED off by making the voltage HIGH
 delay(200); // wait for 200 milliseconds
}