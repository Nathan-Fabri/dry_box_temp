#pragma once
#include "pinmap.h"

/**
 * @brief Identifiers for individual HVAC relay-controlled dampers.
 *
 * These represent logical damper functions, not physical pin numbers.
 * The relay control logic maps these to the correct GPIO pins and default states.
 */
enum RelayID {
    PTC_Heater_1,     ///< Relay for Dehumidifier 1 PTC Heater (normally off)
    PTC_Heater_2,   ///< Relay for Dehumidifier 2 PTC Heater (normally off)
    NUM_RELAYS         ///< Total number of defined relays
};

/**
 * @brief Initializes relay control pins and sets all relays to their default state.
 *
 * This should be called in setup(). It configures all damper relay pins as outputs
 * and sets them according to their defined default state (normally open or closed).
 */
void setupRelays();

/**
 * @brief Sets the HVAC damper to either its default state (true) or the opposite (false).
 *
 * The function internally knows whether each damper is normally open or closed.
 * Use `true` to apply the damper’s default (normal) state,
 * or `false` to switch it to the opposite state.
 *
 * @param relay The relay to control (e.g., Damper_1_Open or Damper_2_Closed).
 * @param matchDefault True to set to default state, false to invert.
 */
void setRelayState(RelayID relay, bool matchDefault);

/**
 * @brief Sets all HVAC relay-controlled dampers to the opposite of their default state (OFF).
 *
 * Internally calls `setRelayState()` with `false` for each relay,
 * effectively deactivating them based on default configuration.
 */
void allRelaysOff();

/**
 * @brief Sets all HVAC relay-controlled dampers to their default state (ON).
 *
 * Internally calls `setRelayState()` with `true` for each relay,
 * activating them to their defined normal position.
 */
void allRelaysOn();

/**
 * @brief Resets all relays to their defined default (normal) state.
 *
 * This is useful during initialization to ensure dampers start in a known state.
 */
void resetRelaysToDefault();

/**
 * @brief Placeholder for future damper relay control logic.
 *
 * Intended to house smart control behavior (e.g., based on temperature, mode, or timing).
 */
void controlRelays();
