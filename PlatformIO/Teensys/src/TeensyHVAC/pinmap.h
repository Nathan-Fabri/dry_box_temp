#pragma once

// -------------------------
// MODBUS RS-485 UART Pins
// -------------------------

/**
 * @brief UART RX pin for Modbus sensor communication (Serial1 RX).
 */
#define PIN_MODBUS_RX           0

/**
 * @brief UART TX pin for Modbus sensor communication (Serial1 TX).
 */
#define PIN_MODBUS_TX           1

/**
 * @brief RS-485 Receiver Enable pin (LOW = Receive mode).
 */
#define PIN_MODBUS_RE           15

/**
 * @brief RS-485 Driver Enable pin (HIGH = Transmit mode).
 */
#define PIN_MODBUS_DE           16


// -------------------------
// Solid-State Relays (SSRs)
// -------------------------

/**
 * @brief SSR output pin for Dehumidifier 1.
 */
#define PIN_SSR_DEHUMIDIFIER_1  2

/**
 * @brief SSR output pin for Dehumidifier 2.
 */
#define PIN_SSR_DEHUMIDIFIER_2  6

/**
 * @brief SSR output pin for Dehumidifier 3.
 */
#define PIN_SSR_DEHUMIDIFIER_3  4

/**
 * @brief SSR output pin for the Humidifier.
 */
#define PIN_SSR_HUMIDIFIER      5

/**
 * @brief SSR output pin for the Heater.
 */
#define PIN_SSR_HEATER          2


// -------------------------
// Relay-Controlled HVAC Dampers
// -------------------------

/**
 * @brief Relay pin for Dehumidifer PTC Heater 1.
 */
#define PIN_RELAY_PTC_HEATER_1      29

/**
 * @brief Relay pin for Dehumidifer PTC Heater 2.
 */
#define PIN_RELAY_PTC_HEATER_2      28

/**
 * @brief Relay pin for HVAC Damper 3.
 */
#define PIN_RELAY_DAMPER_3_TBD      9 //Pin TBD


// -------------------------
// HVAC Fan PWM Pins
// -------------------------

/**
 * @brief PWM control pin for HVAC Fan 1.
 */
#define FAN_1          10

/**
 * @brief PWM control pin for HVAC Fan 2.
 */
#define FAN_2          11

/**
 * @brief (TODO) Tachometer pin for HVAC Fan 1 (not yet connected).
 */
#define PIN_HVAC_FAN_1_TACH     2000  // TODO: Assign real pin

/**
 * @brief (TODO) Tachometer pin for HVAC Fan 2 (not yet connected).
 */
#define PIN_HVAC_FAN_2_TACH     2000  // TODO: Assign real pin


// -------------------------
// Stepper Motor Control Pins
// -------------------------

/**
 * @brief Step pulse pin for the stepper motor driver.
 */
#define PIN_STEPPER_STEP        23

/**
 * @brief Direction pin for the stepper motor driver.
 */
#define PIN_STEPPER_DIR         22

// -------------------------
// Load Cell Pins
// -------------------------

#define PIN_LOAD_CELL       24