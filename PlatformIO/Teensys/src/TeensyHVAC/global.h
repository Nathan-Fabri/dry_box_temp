#pragma once

// Stepper motor
extern int stepsPerRev;

// Fan control
extern int lastFanSpeed;

// Global sensor variables - Temperatures
extern float Exterior_Temp;
extern float Chiller_Temp;
extern float Box_Outlet_Temp;
extern float Box_Inlet_Temp;
extern float Shell_Temp;
extern float Left_Tower_Temp;
extern float Right_Tower_Temp;

// Global sensor variables - Humidities
extern float Exterior_RH;
extern float Chiller_RH;
extern float Box_Outlet_RH;
extern float Box_Inlet_RH;
extern float Shell_RH;
extern float Left_Tower_RH;
extern float Right_Tower_RH;

// Global sensor variables - Averages
extern float Temp_Avg;
extern float Humidity_Avg;