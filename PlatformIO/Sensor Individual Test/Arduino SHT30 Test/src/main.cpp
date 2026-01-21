#include <Wire.h>
#include <SparkFun_I2C_Mux_Arduino_Library.h> // Library for the TCA9548A multiplexer
#include <Adafruit_SHT31.h>                  // Library for the SHT30 sensors

QWIICMUX myMux;                              // Create an instance of the multiplexer
Adafruit_SHT31 sht1 = Adafruit_SHT31();      // Create an instance for the first SHT30 sensor
Adafruit_SHT31 sht2 = Adafruit_SHT31();  

double t = 200;

void setup()
{
  Serial.begin(9600);

  // Add a 5-second pause before starting
  delay(5000);

  Serial.println();
  Serial.println("Qwiic Mux Shield Read Example");

  Wire.begin();

  // Initialize the multiplexer
  if (!myMux.begin())
  {
    Serial.println("Mux not detected. Freezing...");
    while (1)
      ;
  }
  Serial.println("Mux detected");

  // Initialize the first SHT30 sensor on channel 0
  myMux.setPort(0); // Select channel 0
  delay(t);        // Small delay to stabilize communication
  if (!sht1.begin(0x44)) // Default I2C address for SHT30
  {
    Serial.println("Failed to initialize SHT30 sensor on channel 0");
  }
  else
  {
    Serial.println("SHT30 sensor on channel 0 initialized");
    sht1.reset(); // Perform a soft reset
  }

  // Initialize the second SHT30 sensor on channel 1
  myMux.setPort(1); // Select channel 1
  delay(t);        // Small delay to stabilize communication
  if (!sht2.begin(0x44)) // Default I2C address for SHT30
  {
    Serial.println("Failed to initialize SHT30 sensor on channel 1");
  }
  else
  {
    Serial.println("SHT30 sensor on channel 1 initialized");
    sht2.reset(); // Perform a soft reset
  }
}

void loop()
{
  // Read data from the first sensor
  myMux.setPort(0); // Select channel 0
  delay(t);        // Small delay to stabilize communication
  Serial.println("Switched to channel 0");
  float temp1 = sht1.readTemperature();
  float humidity1 = sht1.readHumidity();

  if (!isnan(temp1) && !isnan(humidity1))
  {
    Serial.print("Sensor 1 - Temp: ");
    Serial.print(temp1);
    Serial.print(" °C, Humidity: ");
    Serial.print(humidity1);
    Serial.println(" %");
  }
  else
  {
    Serial.println("Failed to read from Sensor 1");
    Serial.print("Temp1: ");
    Serial.println(temp1);
    Serial.print("Humidity1: ");
    Serial.println(humidity1);
  }

  delay(1000);

  // Read data from the second sensor
  myMux.setPort(1); // Select channel 1
  delay(t);        // Small delay to stabilize communication
  Serial.println("Switched to channel 1");
  float temp2 = sht2.readTemperature();
  float humidity2 = sht2.readHumidity();

  if (!isnan(temp2) && !isnan(humidity2))
  {
    Serial.print("Sensor 2 - Temp: ");
    Serial.print(temp2);
    Serial.print(" °C, Humidity: ");
    Serial.print(humidity2);
    Serial.println(" %");
  }
  else
  {
    Serial.println("Failed to read from Sensor 2");
    Serial.print("Temp2: ");
    Serial.println(temp2);
    Serial.print("Humidity2: ");
    Serial.println(humidity2);
  }

  delay(2000); // Wait 2 seconds before the next reading
}