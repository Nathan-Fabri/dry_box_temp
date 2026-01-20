// command_parser.cpp
#include "command_parser.h"
#include "stepper.h"
#include "fan_control.h"
#include "ssr_control.h"
#include "pinmap.h"
#include "relay_control.h"
#include "modbus_rtu.h"
#include "global.h"


// Helper functions
String getValue(String data, String key) {
    int startIndex = data.indexOf(key + ":");
    if (startIndex == -1) return "";
    startIndex += key.length() + 1;
    int endIndex = data.indexOf(',', startIndex);
    if (endIndex == -1) endIndex = data.length();
    return data.substring(startIndex, endIndex);
}

void turnOffEverything(){
    // First, directly force all fan pins LOW
    for (int i = 0; i < NUM_FANS; i++) {
        pinMode(FANS[i], OUTPUT);
        digitalWrite(FANS[i], LOW);
        // Also ensure PWM is disabled
        analogWrite(FANS[i], 0);
    }
    turnAllFansOff();
    allRelaysOff();
    setAllSSRsOff();
    stopContinuousStepper();
}

void parseIncomingData(String input, float& ambientTemp, float& shellTemp, int& humidity, int& shellTime, int& FanSpeed, int& omega, bool& machineState, float& deltaShellTemperature, float& deltaAirTemperature, float& deltaHumidity, float& deltaShellFanAirFlow, float& currAmbientTemperature, float& currShellTemperature, float& currHumidity) {
    input.trim();
    SerialUSB1.println("Parsing command: " + input);
    SerialUSB1.print("Initial machine state: ");
    SerialUSB1.println(machineState ? "ON" : "OFF");

    if (input.startsWith("ALLOFF")) {
        SerialUSB1.println("Received ALLOFF command");
        machineState = false;
        turnOffEverything();
        SerialUSB1.println("Machine state set to: OFF");
        Serial.println("ACK-TeensyHVAC");
    }
    else if(input.startsWith("SENSOR-")) {
        SerialUSB1.println("Received SENSOR command");
        input = input.substring(7);
        currAmbientTemperature = getValue(input, "CAT").toFloat();
        currShellTemperature   = getValue(input, "CST").toFloat();
        currHumidity           = getValue(input, "CH").toFloat();
        Serial.println("ACK-TeensyHVAC");
    }
    else if(input.startsWith("START-")) {
        SerialUSB1.println("Received START command");
        input = input.substring(6);
        ambientTemp           = getValue(input, "ATEMP").toFloat();
        shellTemp            = getValue(input, "STEMP").toFloat();
        humidity             = getValue(input, "HUM").toInt();
        shellTime            = getValue(input, "TIME").toInt();
        FanSpeed             = getValue(input, "FAN").toInt();
        omega                = getValue(input, "OMEGA").toInt();
        deltaShellTemperature = getValue(input, "DST").toFloat();
        deltaAirTemperature   = getValue(input, "DAT").toFloat();
        deltaHumidity         = getValue(input, "DH").toFloat();
        deltaShellFanAirFlow  = getValue(input, "DSFA").toFloat();

        // Stepper Motor setup
            if (omega > 0) {
                // Configure the stepper motor with the updated output RPM
                calculateStepperInterval(omega, stepsPerRev, 50.0);
                
                // Ensure stepper is running
                if (!continuousStepperEnabled) {
                    startContinuousStepper();
                }
            } else {
                // Stop the stepper if omega is zero
                stopContinuousStepper();
            }

        // --------------------------------------------
        // Debugging output
        // --------------------------------------------
        // SerialUSB1.println("Received and parsed START command:");
        // SerialUSB1.println("Ambient Temp: " + String(ambientTemp));
        // SerialUSB1.println("Shell Temp  : " + String(shellTemp));
        // SerialUSB1.println("Humidity    : " + String(humidity));
        // SerialUSB1.println("Time        : " + String(shellTime));
        // SerialUSB1.println("Fan Speed   : " + String(FanSpeed));
        // SerialUSB1.println("Omega       : " + String(omega));
        // SerialUSB1.println("DST         : " + String(deltaShellTemperature));
        // SerialUSB1.println("DAT         : " + String(deltaAirTemperature));
        // SerialUSB1.println("DH          : " + String(deltaHumidity));
        // SerialUSB1.println("DSFA        : " + String(deltaShellFanAirFlow));

        // Start Loop
        machineState = true;
        SerialUSB1.println("All devices initialized");
        SerialUSB1.print("Machine state set to: ");
        SerialUSB1.println(machineState ? "ON" : "OFF");
        Serial.println("ACK-TeensyHVAC");
    }
    else {
        SerialUSB1.println("Unknown command: " + input);
        SerialUSB1.println("UKN-TeensyHVAC");
    }
}