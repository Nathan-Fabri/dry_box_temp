#include "fan_control.h"
#include <Arduino.h>
#include "pinmap.h"  // Defines your PIN_L_FAN_x and PIN_R_FAN_x

const int FANS[4] = {FAN_1, FAN_2, FAN_3, FAN_4};
const int NUM_FANS = sizeof(FANS) / sizeof(FANS[0]);
int fanSpeedHolder = 0;

void setupFanControl(int fanSpeed) {
    //Set all fan pins as outputs
    for (int i = 0; i < 4; i++) {
        pinMode(FANS[i], OUTPUT);
        analogWriteFrequency(FANS[i], 20000);
    }
    fanSpeedHolder = fanSpeed; 
    turnAllFansOn(fanSpeed);  // Start with all fans on
    Serial.println("Fan control initialized.");
}

void setFanSpeed(int pin, int percent) {
    percent = constrain(percent, 0, 100);
    if (percent == 0) {
        pinMode(pin, OUTPUT);      // Make sure it's an output
        digitalWrite(pin, LOW);     // Force the pin LOW manually
    } else {
        int pwmValue = map(percent, 0, 100, 0, 255);
        analogWrite(pin, pwmValue);
    }
}

void turnAllFansOn(int fanSpeed) {
    for (int i = 0; i < 4; i++) {
        setFanSpeed(FANS[i], fanSpeed);
        delay(100);
    }
}

void turnAllFansOff() {
    for (int i = 0; i < 4; i++) {
        setFanSpeed(FANS[i], 0);  
        delay(100);      
    }
}

void turnFansOnInOrder(){
    turnAllFansOff();
    for(int i = 0; i < 4; i++){
        setFanSpeed(FANS[i], 100);
        delay(1000);
    }
    for(int i = 3; i >= 0; i--){
        setFanSpeed(FANS[i], 0);
        delay(1000);
    }
    turnAllFansOn(fanSpeedHolder);
    delay(5000);
    turnAllFansOff();
}

int getPWMFromFtMin(float desiredFtMin, float maxFtMin = 2500.0) {
    // Clamp to safe range
    if (desiredFtMin <= 0) return 0;
    if (desiredFtMin >= maxFtMin) return 100;

    float pwm = (desiredFtMin / maxFtMin) * 100.0;
    return round(pwm); // Return as integer PWM percent
}

void handleFanControl(int& fanSpeed) {
    turnAllFansOn(getPWMFromFtMin(fanSpeed));
} 