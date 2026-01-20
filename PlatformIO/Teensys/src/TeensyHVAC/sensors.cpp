#include "sensors.h"

const SensorConfig sensorconfigs[SENSORID] = {
    {1},  // Exterior
    {4},  // Chiller
    {6},  // Box_Outlet
    {5},  // Box_Inlet
    {9},  // Shell
    {8},  // Left_Tower
    {7}   // Right_Tower
};

const char* const sensorNames[SENSORID] = {
    "Exterior",
    "Chiller",
    "Box_Outlet",
    "Box_Inlet",
    "Shell",
    "Left_Tower",
    "Right_Tower"
};
