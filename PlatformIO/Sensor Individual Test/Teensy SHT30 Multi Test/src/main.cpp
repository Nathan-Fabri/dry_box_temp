#include <Wire.h>
#include <SparkFun_I2C_Mux_Arduino_Library.h> // TCA9548A multiplexer
#include <Adafruit_SHT31.h>                  // SHT30 sensors

QWIICMUX myMux;

Adafruit_SHT31 sht1; // For sensor on channel 0
Adafruit_SHT31 sht2; // For sensor on channel 1

double t = 200;

// Bus recovery routine
void recoverI2C() {
  pinMode(18, OUTPUT); // SDA
  pinMode(19, OUTPUT); // SCL
  for (int i = 0; i < 9; i++) {
    digitalWrite(19, HIGH);
    delayMicroseconds(5);
    digitalWrite(19, LOW);
    delayMicroseconds(5);
  }
  pinMode(18, INPUT_PULLUP);
  pinMode(19, INPUT_PULLUP);
}


void setup() {
  Serial.begin(9600);
  delay(5000); // Initial pause

  Serial.println("Qwiic Mux - Identical SHT30 Sensors with Same Address");

  recoverI2C(); // Bus recovery
  Wire.begin();
  Wire.setClock(100000); // Lower speed for stability

  if (!myMux.begin()) {
    Serial.println("Mux not detected. Halting.");
    while (1);
  }
  Serial.println("Mux detected");

  // Init sensor 1 (channel 0)
  myMux.setPort(0);
  delay(t);
  if (!sht1.begin(0x44)) {
    Serial.println("Sensor 1 (channel 0) failed to initialize.");
  } else {
    Serial.println("Sensor 1 (channel 0) initialized.");
    sht1.reset();
  }

  // Init sensor 2 (channel 1)
  myMux.setPort(1);
  delay(t);
  if (!sht2.begin(0x44)) {
    Serial.println("Sensor 2 (channel 1) failed to initialize.");
  } else {
    Serial.println("Sensor 2 (channel 1) initialized.");
    sht2.reset();
  }
}

void loop() {
  // Sensor 1 - channel 0
  myMux.setPort(0);
  delay(t);
  float temp1 = sht1.readTemperature();
  float hum1 = sht1.readHumidity();
  Serial.println("Reading Sensor 1 (channel 0)");
  if (!isnan(temp1) && !isnan(hum1)) {
    Serial.print("Temp 1: "); Serial.print(temp1); Serial.print(" °C, ");
    Serial.print("Humidity 1: "); Serial.print(hum1); Serial.println(" %");
  } else {
    Serial.println("Sensor 1 read failed.");
  }

  // Sensor 2 - channel 1
  myMux.setPort(1);
  delay(t);
  float temp2 = sht2.readTemperature();
  float hum2 = sht2.readHumidity();
  Serial.println("Reading Sensor 2 (channel 1)");
  if (!isnan(temp2) && !isnan(hum2)) {
    Serial.print("Temp 2: "); Serial.print(temp2); Serial.print(" °C, ");
    Serial.print("Humidity 2: "); Serial.print(hum2); Serial.println(" %");
  } else {
    Serial.println("Sensor 2 read failed.");
  }

  delay(2000);
}
