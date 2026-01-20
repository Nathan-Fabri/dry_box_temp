#include <Arduino.h>
#include <Arduino_PortentaMachineControl.h>

// Sketch to flash the led on Digital Output 01 on the M7 Core
#define LED 6   // Defines digital output 01 

// the setup function runs once when you press reset or power the board
void setup() {
  // Initalizes the Digital Outputs
  MachineControl_DigitalOutputs.begin();

  // Initalizes the M4 core
  //bootM4();
}

// the loop function runs over and over again forever
void loop() {
 MachineControl_DigitalOutputs.write(LED, LOW); // turn the red LED on (LOW is the voltage level)
 delay(200); // wait for 200 milliseconds
 MachineControl_DigitalOutputs.write(LED, HIGH); // turn the LED off by making the voltage HIGH
 delay(200); // wait for 200 milliseconds
}