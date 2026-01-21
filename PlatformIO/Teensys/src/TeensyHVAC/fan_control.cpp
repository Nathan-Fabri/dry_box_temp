// fan_control.cpp
#include "fan_control.h"
#include "pinmap.h"

// Constants for fan control
const int FANS[2] = {FAN_1, FAN_2};
const int NUM_FANS = sizeof(FANS) / sizeof(FANS[0]);
int fanSpeedHolder = 0;

void setupFanControl(int fanSpeed) {
    for (int i = 0; i < NUM_FANS; i++) {
        // First ensure pin is output and LOW
        pinMode(FANS[i], OUTPUT);
        digitalWrite(FANS[i], LOW);
        
        // Configure PWM settings
        analogWriteResolution(FAN_PWM_RESOLUTION);
        analogWriteFrequency(FANS[i], FAN_PWM_FREQUENCY);
        
        // Explicitly write 0 to PWM
        analogWrite(FANS[i], 0);
    }
    
    fanSpeedHolder = fanSpeed;
    
    // Only turn on fans if fanSpeed > 0
    if (fanSpeed > 0) {
        turnAllFansOn(fanSpeed);
    }
}

void setFanSpeed(int pin, int percent) {
    percent = constrain(percent, 0, 100);
    if (percent == 0) {
        digitalWrite(pin, LOW);
        // Make extra sure PWM is disabled by explicitly setting it to 0
        analogWrite(pin, 0);
    } else {
        // Map 0-100 to 0-4095 for 12-bit resolution
        int pwmValue = map(percent, 0, 100, 0, (1 << FAN_PWM_RESOLUTION) - 1);
        analogWrite(pin, pwmValue);
    }
}

void turnAllFansOn(int fanSpeed) {
    // If speed is 0, call turnAllFansOff instead
    if (fanSpeed <= 0) {
        turnAllFansOff();
        return;
    }
    
    // Proceed with turning fans on at specified speed
    for (int i = 0; i < NUM_FANS; i++) {
        setFanSpeed(FANS[i], fanSpeed);
        delay(100);  // Brief delay between fan starts for stability
    }
}

void turnAllFansOff() {
    for (int i = 0; i < NUM_FANS; i++) {
        setFanSpeed(FANS[i], 0);
        digitalWrite(FANS[i], LOW);  // Ensure pin is LOW  
        
        // Force pin mode to OUTPUT again just to be sure
        pinMode(FANS[i], OUTPUT);
        digitalWrite(FANS[i], LOW);
        
        delay(100);      
    }
}

void turnFansOnInOrder() {
    turnAllFansOff();
    for (int i = 0; i < NUM_FANS; i++) {
        setFanSpeed(FANS[i], 100);
        delay(1000);
    }
    for (int i = NUM_FANS - 1; i >= 0; i--) {
        setFanSpeed(FANS[i], 0);
        delay(1000);
    }
    turnAllFansOn(fanSpeedHolder);
    delay(5000);
    turnAllFansOff();
}

int getPWMFromCFM(float desiredCFM, float maxCFM) {
    // Clamp to safe range
    if (desiredCFM <= 0) return 0;
    if (desiredCFM >= maxCFM) return 100;

    return round((desiredCFM / maxCFM) * 100.0);
}

// === Global PID state (put in global.cpp if needed) ===
float fan_integral = 0.0;
float fan_prevError = 0.0;
unsigned long fan_lastTime = 0;

// === PID tuning constants ===
float fan_Kp = 15;    
float fan_Ki = 0.1;  
float fan_Kd = 0.5;  

/**
 * @brief Sets the PID control parameters for fan control
 * 
 * @param kp Proportional gain
 * @param ki Integral gain
 * @param kd Derivative gain
 */
void setFanPIDValues(float kp, float ki, float kd) {
    fan_Kp = kp;
    fan_Ki = ki;
    fan_Kd = kd;
}

void handleFanControl(float ambientTemp, float setTemp, float deltaTemp) {
    // Validate ambient temp
    if (ambientTemp < -50 || ambientTemp > 100) return;

    // Target temp = setTemp - deltaTemp (we want to cool to below setpoint)
    float targetTemp = setTemp - deltaTemp;

    float error = targetTemp - ambientTemp;

    // Deadband behavior
    if (abs(error) < 0.2) {  // Deadband of 0.2°C
        fan_integral = 0;
        turnAllFansOff();
        return;
    }

    // Time delta
    unsigned long now = millis();
    float dt = (now - fan_lastTime) / 1000.0;
    if (dt <= 0) dt = 0.01;
    fan_lastTime = now;

    // PID calculations
    fan_integral += error * dt;
    fan_integral = constrain(fan_integral, -50, 50);  // Anti-windup

    float derivative = (error - fan_prevError) / dt;
    fan_prevError = error;

    float pid_output = fan_Kp * error + fan_Ki * fan_integral + fan_Kd * derivative;
    pid_output = constrain(pid_output, -100, 100);

    // Map PID output to PWM range
    int fanPWM;
    if (error > 0) {
        // Temperature below target (need heating, reduce cooling)
        fanPWM = map(abs(pid_output), 0, 100, 90, 0);  // Fan ramps down from 90-0%
    } else {
        // Temperature above target (need cooling)
        // More aggressive cooling - starting at 40% and ramping up more quickly
        // Use non-linear response for better performance near target
        float absOutput = abs(pid_output);
        
        // Start at 40% minimum when any cooling is needed
        if (absOutput < 10) {
            // When close to target, still maintain significant cooling
            fanPWM = 40 + (absOutput * 2);  // 40-60% range for small errors
        } else if (absOutput < 50) {
            // Mid-range errors get more aggressive response
            fanPWM = 60 + ((absOutput - 10) * 0.8);  // 60-92% range
        } else {
            // Large errors get maximum cooling
            fanPWM = 92 + ((absOutput - 50) * 0.16);  // 92-100% range
        }
    }

    fanPWM = constrain(fanPWM, 0, 100);
    
    // Call debug function (uncomment when debugging is needed)
    //debugFanControl(ambientTemp, setTemp, error, pid_output, fanPWM);
    
    turnAllFansOn(fanPWM);
}

/**
 * @brief Debug function for fan control PID values and state
 */
void debugFanControl(float ambientTemp, float setTemp, float error, float pid_output, int fanPWM) {
    SerialUSB1.println("\n--- Fan Control Debug ---");
    SerialUSB1.print("Current Ambient Temp: ");
    SerialUSB1.print(ambientTemp);
    SerialUSB1.print("°C, Target: ");
    SerialUSB1.print(setTemp);
    SerialUSB1.println("°C");
    
    SerialUSB1.print("Error: ");
    SerialUSB1.println(error);
    
    SerialUSB1.print("PID Components - P: ");
    SerialUSB1.print(fan_Kp * error);
    SerialUSB1.print(" I: ");
    SerialUSB1.print(fan_Ki * fan_integral);
    SerialUSB1.print(" D: ");
    SerialUSB1.println(fan_Kd * (error - fan_prevError));
    
    SerialUSB1.print("Raw PID output: ");
    SerialUSB1.println(pid_output);
    SerialUSB1.print("Constrained PID output: ");
    SerialUSB1.println(constrain(pid_output, -100, 100));
    
    SerialUSB1.print("Final fan PWM (0=off, 100=full): ");
    SerialUSB1.println(fanPWM);
}
