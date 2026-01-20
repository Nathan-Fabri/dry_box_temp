#include "command_parser.h"
#include "sensor_scan.h"
// extern float ambientTemps[6];     // e.g., from Modbus
// extern float humidityTemps[6];    // or could be humidity readings if that's what you meant
// extern float currentWeight;    // from load cell

float currentWeight = 0.0;

void sendReadings() {
    Serial.println("Sending sensor readings:");

    // Send object temperatures
    Serial.print("AmbientTemps:");
    for (int i = 0; i < 6; i++) {
        // Serial.print(objectAvg[i], 1);  // One decimal precision
        if (i < 5) Serial.print(",");   // Comma between values
    }
    Serial.println();

    // Send ambient temps or humidity
    Serial.print("Humidity:");
    for (int i = 0; i < 6; i++) {
        // Serial.print(ambientAvg[i], 1);
        if (i < 5) Serial.print(",");
    }
    Serial.println();

    // // Send weight
    // Serial.print("Weight:");
    // Serial.println(currentWeight, 2);  // Two decimal places for precision
}