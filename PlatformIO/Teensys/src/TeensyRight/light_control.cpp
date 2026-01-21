#include "light_control.h"
#include <Wire.h>
#include <Arduino.h>
#include "fan_control.h"

// I2C addresses for the 4 triac dimmer boards
const uint8_t DIMMER_ADDRESSES[4] = {0x27, 0x26, 0x25, 0x24};
// Channel control bytes
const uint8_t CHANNELS[4] = {0x80, 0x81, 0x82, 0x83};

float currentLevel = 0;

// Increase Kp for more aggressive response to error
// Increase Ki for better steady-state correction
// Add small Kd for dampening oscillations
float Kp = 20.0;  // More aggressive proportional control
float Ki = 0.5;   // Increased integral control
float Kd = 2.0;   // Small derivative term to prevent overshooting

const int Order[16] =     {4, 5, 3, 2, 7, 6, 0, 1, 9, 8, 12, 13, 15, 14, 11, 10};
int OrderFlipped[16];

const int LeftSideRight[4]   = {5, 2, 6, 1};
const int LeftSideLeft[4]  = {4, 3, 7, 0};
const int RightSideLeft[4]  = {10, 14, 13, 8};
const int RightSideRight[4] = {11, 15, 12, 9};

const int cluster1[3] = {3, 4, 5};
const int cluster2[3] = {2, 6, 7};
const int cluster3[3] = {0, 1, 9};
const int cluster4[3] = {12, 8, 13};
const int cluster5[4] = {10, 11, 14, 15};

void setPIDValues(float vKp, float vKi, float vKd){
    Kp = vKp;
    Ki = vKi;
    Kd = vKd;
}

void sendDimmerCommand(uint8_t address, uint8_t channel, uint8_t level) {
    currentLevel = level;
    Wire.beginTransmission(address);
    Wire.write(channel);
    Wire.write(level);
    Wire.endTransmission();
}

void setupLightControl() {
    Wire.begin();
    allOn();
    allOff();
}

// PID state
float prevError = 0;
float integral = 0;
unsigned long lastTime = 0;

void debugLightControl(float currShellTemperature, float gShellTemp, float error, float pid_output, float currentLevel) {
    Serial.println("\n--- Light Control Debug ---");
    Serial.print("Current Shell Temp: ");
    Serial.print(currShellTemperature);
    Serial.print("°C, Target: ");
    Serial.print(gShellTemp);
    Serial.println("°C");
    
    Serial.print("Error: ");
    Serial.println(error);
    
    Serial.print("PID Components - P: ");
    Serial.print(Kp * error);
    Serial.print(" I: ");
    Serial.print(Ki * integral);
    Serial.print(" D: ");
    Serial.println(Kd * (error - prevError));
    
    Serial.print("Raw PID output: ");
    Serial.println(pid_output);
    Serial.print("Constrained PID output: ");
    Serial.println(constrain(pid_output, -100, 100));
    
    Serial.print("Final dimming level (0=full on, 100=off): ");
    Serial.println(currentLevel);
    Serial.println("-------------------------");
}

void handleLightControl(float currShellTemperature, float gShellTemp, float delta) {
    // Validate sensor reading
    if (currShellTemperature < -100 || currShellTemperature > 200) {
        return;  // Maintain previous state rather than react to bad reading
    }
    
    float error = gShellTemp - currShellTemperature;

    if (abs(error) < delta) {
        integral = 0;  // Reset integral term when in deadband
        setAllOn(100); // Lights OFF in deadband
        return;
    }

    unsigned long now = millis();
    float dt = (now - lastTime) / 1000.0;
    if (dt <= 0) dt = 0.01;
    lastTime = now;

    integral += error * dt;
    // Limit integral windup
    if (integral > 50) integral = 50;
    if (integral < -50) integral = -50;

    float derivative = (error - prevError) / dt;
    prevError = error;

    float pid_output = Kp * error + Ki * integral + Kd * derivative;
    
    // Constrain pid_output to reasonable range
    pid_output = constrain(pid_output, -100, 100);
    
    // Convert PID output to dimming level
    if (error > 0) {  // We need heat
        currentLevel = map(abs(pid_output), 0, 100, 90, 0);  // Minimum brightness is 90% dimming
    } else {  // We need cooling
        currentLevel = map(abs(pid_output), 0, 100, 10, 100);  // Maximum brightness is 10% dimming
    }
    
    // Ensure dimming level stays within valid range
    currentLevel = constrain(currentLevel, 0, 100);

    // Call debug function if needed
    //debugLightControl(currShellTemperature, gShellTemp, error, pid_output, currentLevel);

    setAllOn(currentLevel);
}

// PID state for thermal camera control (separate from infrared sensor PID)
float thermalPrevError = 0;
float thermalIntegral = 0;
unsigned long thermalLastTime = 0;

// Thermal camera PID parameters (different tuning from infrared sensor)
float thermalKp = 2.0;   // Much gentler proportional response for slow heating
float thermalKi = 0.1;   // Very low integral to prevent windup with slow response
float thermalKd = 0.5;   // Minimal derivative to reduce noise sensitivity

void setThermalPIDValues(float vKp, float vKi, float vKd){
    thermalKp = vKp;
    thermalKi = vKi;
    thermalKd = vKd;
}

void handleLightControlThermalCamera(float currShellTemperature, float gShellTemp, float delta) {
    // Validate sensor reading
    if (currShellTemperature < -100 || currShellTemperature > 200) {
        return;  // Maintain previous state rather than react to bad reading
    }
    
    float error = gShellTemp - currShellTemperature;

    if (abs(error) < delta) {
        thermalIntegral = 0;  // Reset integral term when in deadband
        setAllOn(100); // Lights OFF in deadband
        return;
    }

    unsigned long now = millis();
    float dt = (now - thermalLastTime) / 1000.0;
    if (dt <= 0) dt = 0.01;
    thermalLastTime = now;

    thermalIntegral += error * dt;
    // Limit integral windup
    if (thermalIntegral > 50) thermalIntegral = 50;
    if (thermalIntegral < -50) thermalIntegral = -50;

    float derivative = (error - thermalPrevError) / dt;
    thermalPrevError = error;

    float pid_output = thermalKp * error + thermalKi * thermalIntegral + thermalKd * derivative;
    
    // Constrain pid_output to reasonable range
    pid_output = constrain(pid_output, -100, 100);
    
    // Convert PID output to dimming level
    if (error > 0) {  // We need heat
        currentLevel = map(abs(pid_output), 0, 100, 90, 0);  // Minimum brightness is 90% dimming
    } else {  // We need cooling
        currentLevel = map(abs(pid_output), 0, 100, 10, 100);  // Maximum brightness is 10% dimming
    }
    
    // Ensure dimming level stays within valid range
    currentLevel = constrain(currentLevel, 0, 100);

    // Optional debug output for thermal camera control
    //debugThermalLightControl(currShellTemperature, gShellTemp, error, pid_output, currentLevel);

    setAllOn(currentLevel);
}

void debugThermalLightControl(float currShellTemperature, float gShellTemp, float error, float pid_output, float currentLevel) {
    Serial.println("\n--- Thermal Camera Light Control Debug ---");
    Serial.print("Current Shell Temp (Thermal): ");
    Serial.print(currShellTemperature);
    Serial.print("°C, Target: ");
    Serial.print(gShellTemp);
    Serial.println("°C");
    
    Serial.print("Error: ");
    Serial.println(error);
    
    Serial.print("Thermal PID Components - P: ");
    Serial.print(thermalKp * error);
    Serial.print(" I: ");
    Serial.print(thermalKi * thermalIntegral);
    Serial.print(" D: ");
    Serial.println(thermalKd * (error - thermalPrevError));
    
    Serial.print("Raw PID output: ");
    Serial.println(pid_output);
    Serial.print("Constrained PID output: ");
    Serial.println(constrain(pid_output, -100, 100));
    
    Serial.print("Final dimming level (0=full on, 100=off): ");
    Serial.println(currentLevel);
    Serial.println("---------------------------------------");
}

// Control a specific board and channel
void setLightLevel(uint8_t boardIndex, uint8_t channelIndex, uint8_t level) {
    if (boardIndex >= 4 || channelIndex >= 4) return; // prevent invalid access

    uint8_t address = DIMMER_ADDRESSES[boardIndex];
    uint8_t channel = CHANNELS[channelIndex];
    sendDimmerCommand(address, channel, level);
}

// Control light by global light number 0–15
void setLightByNumber(uint8_t lightNumber, uint8_t level) {
    if (lightNumber >= 16) return; // prevent invalid light number

    uint8_t boardIndex = lightNumber / 4;      // 0..3
    uint8_t channelIndex = lightNumber % 4;    // 0..3
    setLightLevel(boardIndex, channelIndex, level);
}

void setAllOn(int dimLvl){
    for (int i = 0; i < 16; i++) {
        setLightByNumber(i, dimLvl);
    }
}

void allOn(){
    for (int i = 0; i < 16; i++) {
        setLightByNumber(i, 0);
    }
}

void allOff(){
    for (int i = 0; i < 16; i++) {
        setLightByNumber(i, 100);
        delay(10); // Small delay to ensure all lights turn off
    }
} 