#include "load_cell.h"
#include "pinmap.h"

// ADC resolution for Teensy 4.1 (12-bit)
const int ADC_RESOLUTION = 4096;
const float VREF = 3.333;  // Reference voltage for Teensy

// Hardware voltage divider scaling
const float R1 = 10000.0;  // 10k ohm
const float R2 = 20000.0;  // 20k ohm
const float HARDWARE_DIVIDER_RATIO = R2 / (R1 + R2);  // = 0.6667 (scales 5V → 3.33V)

// Simple linear calibration based on actual measurements
const float VOLTS_TO_POUNDS = 91.97;  // Original 61.3083 lb/V adjusted for 0.6667 voltage divider (61.3083 ÷ 0.6667)
const float ZERO_OFFSET_VOLTS = 0.0;  // Your actual 0 lb reading due to the stepper motor, metal shell holder, etc

// Variables to store the current weight and averaging
static float currentWeight = 0.0;
static const int AVERAGE_SAMPLES = 100;  // Number of samples to average
static float weightSamples[AVERAGE_SAMPLES];
static int sampleIndex = 0;
static bool samplesInitialized = false;

void setupLoadCell() {
    analogReadResolution(16);      // Use higher resolution ADC (up to 65536)
    analogReadAveraging(32);       // Average 32 samples for better noise rejection
    
    pinMode(PIN_LOAD_CELL, INPUT);
    
    // Initialize averaging array
    for (int i = 0; i < AVERAGE_SAMPLES; i++) {
        weightSamples[i] = 0.0;
    }
    sampleIndex = 0;
    samplesInitialized = false;
}

float readLoadCellWeight() {
    static unsigned long lastSampleTime = 0;
    static const unsigned long SAMPLE_INTERVAL = 100; // 10Hz sampling (100ms)
    
    unsigned long currentTime = millis();
    
    // Only update averaging if enough time has passed
    if (currentTime - lastSampleTime >= SAMPLE_INTERVAL) {
        // Read analog value
        uint16_t raw = analogRead(PIN_LOAD_CELL);
        
        // Convert to voltage (hardware divider already applied)
        float voltage = (raw * VREF / ADC_RESOLUTION);
        
        // Simple linear conversion: Weight = (Voltage - Zero Offset) × Scale Factor
        float instantWeight = (voltage - ZERO_OFFSET_VOLTS) * VOLTS_TO_POUNDS;
        
        // Add to circular buffer for averaging
        weightSamples[sampleIndex] = instantWeight;
        sampleIndex = (sampleIndex + 1) % AVERAGE_SAMPLES;
        
        // Calculate average weight
        float totalWeight = 0.0;
        int samplesToUse = samplesInitialized ? AVERAGE_SAMPLES : sampleIndex + 1;
        
        for (int i = 0; i < samplesToUse; i++) {
            totalWeight += weightSamples[i];
        }
        
        currentWeight = totalWeight / samplesToUse;
        
        // Mark samples as initialized once we've filled the buffer once
        if (sampleIndex == 0 && !samplesInitialized) {
            samplesInitialized = true;
        }
        
        lastSampleTime = currentTime;
    }
    
    return currentWeight;
}

float getLoadCellWeight() {
    return currentWeight;
}

void debugPrintLoadCell() {
    static unsigned long lastPrintTime = 0;
    static const unsigned long PRINT_INTERVAL = 1000; // 1 second interval
    
    unsigned long currentTime = millis();
    
    // Update the averaged reading first (this handles the 10Hz sampling)
    readLoadCellWeight();
    
    // Only print if enough time has passed
    if (currentTime - lastPrintTime >= PRINT_INTERVAL) {
        uint16_t raw = analogRead(PIN_LOAD_CELL);
        float voltage = (raw * VREF / ADC_RESOLUTION);
        
        // Show both instant and averaged readings for comparison
        SerialUSB1.print("✅ Load_Cell | Voltage: ");
        SerialUSB1.print(voltage, 3);
        SerialUSB1.print(" V | Weight: ");
        SerialUSB1.print(currentWeight, 2);
        SerialUSB1.println(" lb");

        lastPrintTime = currentTime;
    }
}

// Optional: Function to adjust zero offset if needed
void setLoadCellZeroOffset(float offsetVolts) {
    // You can call this to set a new zero point
    // For example, if 0 lbs reads 0.031V instead of 0V:
    // setLoadCellZeroOffset(0.031);
}