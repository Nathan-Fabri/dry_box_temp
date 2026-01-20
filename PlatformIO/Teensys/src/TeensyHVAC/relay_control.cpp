#include "relay_control.h"
#include "pinmap.h"
#include <Arduino.h>

// === Relay Configuration ===
struct RelayConfig {
    int pin;
    bool defaultClosed;  // true = normally closed, false = normally open
};

// Relay configuration table (must match RelayID order)
const RelayConfig relayConfigs[NUM_RELAYS] = {
    {PIN_RELAY_PTC_HEATER_1 , false}, // PTC Heater 1 (normally off)
    {PIN_RELAY_PTC_HEATER_2, false}, // PTC Heater 2 (normally off)
};

// === Setup ===
void setupRelays() {
    for (int i = 0; i < NUM_RELAYS; i++) {
        pinMode(relayConfigs[i].pin, OUTPUT);
    }
    resetRelaysToDefault();  // Ensure all relays are at default state
}

// === Core Control ===
void setRelayState(RelayID relay, bool matchDefault) {
    if (relay < 0 || relay >= NUM_RELAYS) return;

    const RelayConfig& config = relayConfigs[relay];
    bool shouldBeClosed = matchDefault ? config.defaultClosed : !config.defaultClosed;

    // Assume LOW = closed, HIGH = open (invert here if needed)
    digitalWrite(config.pin, shouldBeClosed ? LOW : HIGH);
}

// === Bulk Helpers ===
void allRelaysOff() {
    for (int i = 0; i < NUM_RELAYS; i++) {
        setRelayState((RelayID)i, false);
    }
}

void allRelaysOn() {
    for (int i = 0; i < NUM_RELAYS; i++) {
        setRelayState((RelayID)i, true);
    }
}

void resetRelaysToDefault() {
    for (int i = 0; i < NUM_RELAYS; i++) {
        setRelayState((RelayID)i, false);
    }
}
