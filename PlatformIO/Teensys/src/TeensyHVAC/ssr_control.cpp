// ssr_control.cpp
#include "ssr_control.h"
#include "pinmap.h"
#include "relay_control.h"

bool dehumidifier1 = false;
bool dehumidifier2 = false;
bool dehumidifier3 = false;
bool humidifier = false;
bool heater = false;

void setupSSR() {
    // Initialize all SSR pins as outputs
    pinMode(PIN_SSR_DEHUMIDIFIER_1, OUTPUT);
    pinMode(PIN_SSR_DEHUMIDIFIER_2, OUTPUT);
    pinMode(PIN_SSR_DEHUMIDIFIER_3, OUTPUT);
    pinMode(PIN_SSR_HUMIDIFIER, OUTPUT);
    pinMode(PIN_SSR_HEATER, OUTPUT);
    
    // Set all SSRs to initial OFF state
    setAllSSRsOff();
}

void setDehumidifier1(bool on) {
digitalWrite(PIN_SSR_DEHUMIDIFIER_1, on ? HIGH : LOW);
dehumidifier1 = on;
}

void setDehumidifier2(bool on) {
digitalWrite(PIN_SSR_DEHUMIDIFIER_2, on ? HIGH : LOW);
dehumidifier2 = on;
}

void setDehumidifier3(bool on) {
digitalWrite(PIN_SSR_DEHUMIDIFIER_3, on ? HIGH : LOW);
dehumidifier3 = on;
}

void setHumidifier(bool on) {
digitalWrite(PIN_SSR_HUMIDIFIER, on ? HIGH : LOW);
humidifier = on;
}

void setHeater(bool on){
    digitalWrite(PIN_SSR_HEATER, on ? HIGH : LOW);
    heater = on;
}

void setAllSSRsOff(){
    setDehumidifier1(false);
    setDehumidifier2(false);
    setDehumidifier3(false);
    setHeater(false);
}

void controlDehumidifier1(float currHumidity, int humidity, float deltaHumidity){
    if(abs(currHumidity - humidity) > deltaHumidity){
        if(currHumidity > humidity && !dehumidifier1){
            setDehumidifier1(true);
            setRelayState(PTC_Heater_1, true);
        }
        else if(currHumidity < humidity && dehumidifier1){
            setDehumidifier1(false);
            setRelayState(PTC_Heater_1, false);
        }
    }
}

void controlDehumidifier2(float currHumidity, int humidity, float deltaHumidity){
    if(abs(currHumidity - humidity) > deltaHumidity){
        if(currHumidity > humidity && !dehumidifier2){
            setDehumidifier2(true);
            setRelayState(PTC_Heater_2, true);
        }
        else if(currHumidity < humidity && dehumidifier2){
            setDehumidifier2(false);
            setRelayState(PTC_Heater_2, false);
        }
    }
}

void controlDehumidifier3(float currHumidity, int humidity, float deltaHumidity){
    if(abs(currHumidity - humidity) > deltaHumidity){
        if(currHumidity > humidity && !dehumidifier3){
            setDehumidifier3(true);
        }
        else if(currHumidity < humidity && dehumidifier3){
            setDehumidifier3(false);
        }
    }
}

void controlHumidifier(int currHumidity, int humidity, float deltaHumidity){
    if(abs(currHumidity - humidity) > deltaHumidity){
        if(currHumidity < humidity && !humidifier){
            setHumidifier(true);
        }
        else if(currHumidity > humidity && humidifier){
            setHumidifier(false);
        }
    }
}

void controlHeater(float currAmbientTemperature, float ambientTemperature, float deltaAirTemperature){
    if(abs(currAmbientTemperature - ambientTemperature) > deltaAirTemperature){
        if(currAmbientTemperature < ambientTemperature && !heater){
            setHeater(true);
        }
        else if(currAmbientTemperature > ambientTemperature && heater){
            setHeater(false);
        }
    }
}