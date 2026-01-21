#include <Arduino.h>
#include <Arduino_PortentaMachineControl.h>
#include <pinDefinitions.h>
#include <AccelStepper.h>

// Define the pins connected to the DM542T stepper controller
#define stepPin 1 // Pin for the step signal
#define dirPin 2  // Pin for the direction signal

AccelStepper stepper(AccelStepper::MotorInterfaceType::DRIVER, PinNameToIndex(MC_DO_DO1_PIN), PinNameToIndex(MC_DO_DO2_PIN)); // Step on DO0, Dir on DO1

void setup()
{
	MachineControl_DigitalOutputs.begin();
	stepper.enableOutputs();
	stepper.setMinPulseWidth(130); // this is necessary. Maybe you can get it to work with something closer to 100us, but 130us seems like a safe value
	stepper.setAcceleration(1000); // choose any value you want
	stepper.setMaxSpeed(1000); // I wouldn't go above 1000, but values up to 1500 might work
	stepper.setSpeed(300); // choose any value up to MaxSpeed
}

void loop()
{
	stepper.runSpeed();
}