#include "sensor_scan.h"
#include "modbus_rtu.h"
#include "sensors.h"
#include "global.h"

// Sensor name strings (extern defined in sensors.cpp)
extern const char* const sensorNames[SENSORID];

static const SensorID* debugSensorList = nullptr;
static size_t debugSensorCount = 0;

// Local variables for outlier detection
float tempOutlier = 2.0;  // °C
float humOutlier  = 3.0;  // %RH

// Global sensor data arrays (used by non-blocking scanner)
float ambientTemps[SENSORID];
float humidityRH[SENSORID];

// Non-blocking sensor scanning state
static int currentSensorIndex = 0;
static unsigned long lastSensorScanTime = 0;
static const unsigned long SENSOR_SCAN_INTERVAL_ms = 50; // 50ms between sensor reads
static unsigned long lastMethodCallTime = 0;
static const unsigned long METHOD_CALL_INTERVAL_ms = 1000; // 1000ms = 1 Hz
static uint8_t currentModbusAddress = 0;
static bool sensorScanInitialized = false;

static bool debugActive = false;
static size_t debugSensorIndex = 0;
static unsigned long lastPrintStart = 0;
static unsigned long lastPrintStep = 0;

void debugPrintAllSensors() {
  debugSensorIndex = 0;
  debugActive = true;
  lastPrintStart = millis();  // Start timing
  lastPrintStep = 0;
}

void debugPrintSensors(const SensorID* ids, size_t count) {
  debugSensorList = ids;
  debugSensorCount = count;
  debugSensorIndex = 0;
  debugActive = true;
  lastPrintStart = millis();
  lastPrintStep = 0;
}

void serviceSensorDebugPrint() {
  if (!debugActive) return;

  unsigned long now = millis();

  if (debugSensorIndex == 0 && (now - lastPrintStart < 1000)) return;
  if (debugSensorIndex == 0) {
    lastPrintStart = now;
  }

  if (now - lastPrintStep < 50) return;

  if (debugSensorList && debugSensorIndex >= debugSensorCount) {
    debugActive = false;
    return;
  } else if (!debugSensorList && debugSensorIndex >= SENSORID) {
    debugActive = false;
    return;
  }

  SensorID id = debugSensorList ? debugSensorList[debugSensorIndex] : static_cast<SensorID>(debugSensorIndex);
  float temp = 0.0, hum = 0.0;

  if (readSensor(id, temp, hum)) {
    SerialUSB1.print("✅ ");
    SerialUSB1.print(sensorNames[id]);
    SerialUSB1.print(" | Temp: ");
    SerialUSB1.print(temp);
    SerialUSB1.print(" °C | Hum: ");
    SerialUSB1.print(hum);
    SerialUSB1.println(" %RH");
  } else {
    SerialUSB1.print("❌ ");
    SerialUSB1.print(sensorNames[id]);
    SerialUSB1.println(" read failed.");
  }

  debugSensorIndex++;
  lastPrintStep = now;
}

// Non-blocking sensor scanning - call this every loop cycle
void serviceNonBlockingSensorScan() {
    unsigned long currentTime = millis();
    
    // Exit early if method shouldn't run yet (1 Hz control)
    if (!(currentTime - lastMethodCallTime >= METHOD_CALL_INTERVAL_ms)) {
        return;
    }
    
    // Initialize on first run
    if (!sensorScanInitialized) {
        lastSensorScanTime = currentTime;
        sensorScanInitialized = true;
        lastMethodCallTime = currentTime;
        return;
    }
    
    // Exit early if not enough time has passed between individual sensor reads
    if (!(currentTime - lastSensorScanTime >= SENSOR_SCAN_INTERVAL_ms)) {
        return;
    }
    
    SensorID currentId = static_cast<SensorID>(currentSensorIndex);
    
    // Skip sensors with no modbus address
    if (sensorconfigs[currentId].modbusAddress > 0) {
        float temp = 0.0, hum = 0.0;
        currentModbusAddress = sensorconfigs[currentId].modbusAddress;
        
        // Perform the modbus read (this is blocking but quick ~10-15ms)
        bool success = readModbusSensor(currentModbusAddress, temp, hum);
        
        if (success) {
            ambientTemps[currentSensorIndex] = temp;
            humidityRH[currentSensorIndex] = hum;
            updateGlobalSensorVariables(currentId, temp, hum);
            
            // Print successful reads in database-parseable format
            SerialUSB1.print("✅ ");
            SerialUSB1.print(sensorNames[currentId]);
            SerialUSB1.print(" | Temp: ");
            SerialUSB1.print(temp);
            SerialUSB1.print(" °C | Hum: ");
            SerialUSB1.print(hum);
            SerialUSB1.println(" %RH");
        } else {
            // Failed to read sensor
            ambientTemps[currentSensorIndex] = -999;
            humidityRH[currentSensorIndex] = -999;
            updateGlobalSensorVariables(currentId, -999, -999);
            
            // Print failures for debugging
            SerialUSB1.print("❌ ");
            SerialUSB1.print(sensorNames[currentId]);
            SerialUSB1.print(" (addr ");
            SerialUSB1.print(currentModbusAddress);
            SerialUSB1.println(") failed");
        }
    } else {
        // No sensor configured - mark as invalid
        ambientTemps[currentSensorIndex] = -999;
        humidityRH[currentSensorIndex] = -999;
        updateGlobalSensorVariables(currentId, -999, -999);
    }
    
    // Move to next sensor
    currentSensorIndex = (currentSensorIndex + 1) % SENSORID;
    lastSensorScanTime = currentTime;
    lastMethodCallTime = currentTime;
}

// Initialize non-blocking sensor scanning
void initNonBlockingSensorScan() {
    currentSensorIndex = 0;
    lastSensorScanTime = 0;
    sensorScanInitialized = false;
}

// Helper function to update global sensor variables
void updateGlobalSensorVariables(SensorID id, float temp, float hum) {
    switch (id) {
        case Exterior:
            Exterior_Temp = temp;
            Exterior_RH = hum;
            break;
        case Chiller:
            Chiller_Temp = temp;
            Chiller_RH = hum;
            break;
        case Box_Outlet:
            Box_Outlet_Temp = temp;
            Box_Outlet_RH = hum;
            break;
        case Box_Inlet:
            Box_Inlet_Temp = temp;
            Box_Inlet_RH = hum;
            break;
        case Shell:
            Shell_Temp = temp;
            Shell_RH = hum;
            break;
        case Left_Tower:
            Left_Tower_Temp = temp;
            Left_Tower_RH = hum;
            break;
        case Right_Tower:
            Right_Tower_Temp = temp;
            Right_Tower_RH = hum;
            break;
        default:
            SerialUSB1.print("ERROR: Unknown sensor ID ");
            SerialUSB1.println(static_cast<int>(id));
            break;
    }
}

// Get sensor scanning status
bool isSensorScanningActive() {
    return (millis() - lastSensorScanTime < SENSOR_SCAN_INTERVAL_ms);
}

// Get current sensor being scanned
int getCurrentSensorIndex() {
    return currentSensorIndex;
}


