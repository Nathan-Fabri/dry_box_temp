#include "global.h"

// Stepper motor
int stepsPerRev = 200;

// Fan control
int lastFanSpeed = -1;

// Global sensor variables - Temperatures
float Exterior_Temp = 0.0;
float Chiller_Temp = 0.0;
float Box_Outlet_Temp = 0.0;
float Box_Inlet_Temp = 0.0;
float Shell_Temp = 0.0;
float Left_Tower_Temp = 0.0;
float Right_Tower_Temp = 0.0;

// Global sensor variables - Humidities
float Exterior_RH = 0.0;
float Chiller_RH = 0.0;
float Box_Outlet_RH = 0.0;
float Box_Inlet_RH = 0.0;
float Shell_RH = 0.0;
float Left_Tower_RH = 0.0;
float Right_Tower_RH = 0.0;

// Global sensor variables - Averages
float Temp_Avg = 0.0;
float Humidity_Avg = 0.0;