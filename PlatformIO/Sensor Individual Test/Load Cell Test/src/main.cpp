#include "Arduino_PortentaMachineControl.h"

// Calibration data (provided from LoadStar)
const int n = 5;
double pounds[n] = {0.0, 59.350, 118.510, 185.510, 245.420};
double volts[n]  = {0.505, 1.477, 2.449, 3.535, 4.508};

// Pin used for analog in
const int analogPin = 0;

// 16-bit ADC
const float adcMax = 65535.0;
const float vRef = 2.8; // ADC input range
const float voltageDividerGain = (100.0 + 39.0) / 39.0;

// Slope and intercept
float slope = 0.0;
float intercept = 0.0;

void computeCalibration() {
  double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

  for (int i = 0; i < n; i++) {
    sumX  += volts[i];
    sumY  += pounds[i];
    sumXY += volts[i] * pounds[i];
    sumX2 += volts[i] * volts[i];
  }

  slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  intercept = (sumY - slope * sumX) / n;
}

void setup() {
  Serial.begin(115200);
  while (!Serial);

  // Initialize analog input mode
  MachineControl_AnalogIn.begin(SensorType::V_0_10);

  // Compute slope and intercept from calibration data
  computeCalibration();
}

void loop() {
  uint16_t raw = MachineControl_AnalogIn.read(analogPin);
  float voltage = (raw / adcMax) * vRef * voltageDividerGain;
  float load = slope * voltage + intercept;

  Serial.print("Voltage: ");
  Serial.print(voltage, 3);
  Serial.print(" V | Load: ");
  Serial.print(load, 2);
  Serial.println(" lb");

  delay(500);
}
