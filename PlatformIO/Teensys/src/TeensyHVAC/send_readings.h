#pragma once
#include <Arduino.h>

/**
 * @brief Sends sensor readings over serial to the Raspberry Pi or remote host.
 *
 * Outputs a formatted text stream including:
 * - Object temperatures (label: "AmbientTemps")
 * - Humidity or ambient temperatures (label: "Humidity")
 * - (Optional) Weight from load cell (currently commented out)
 *
 * Data is printed in CSV-style format (e.g., 21.3,22.5,23.0,...), 
 * terminated by a newline after each line.
 *
 * This function assumes the existence of the following global arrays (declared elsewhere):
 * - `objectAvg[]` : Averaged object temperatures
 * - `ambientAvg[]` : Averaged humidity or ambient temps
 * - `currentWeight` (optional) : Current weight reading from load cell
 */
void sendReadings();
