#pragma once

/**
 * @file pinmap.h
 * @brief Defines hardware pin mappings for all actuators and sensors in the system.
 *
 * This file serves as a centralized place to map logical hardware components (fans, relays, SSRs, etc.)
 * to their corresponding physical GPIO pins on the microcontroller.
 */

// -----------------------------
// LEFT FAN PWM OUTPUTS
// -----------------------------

#define FAN_1          3   ///< Left fan 1 PWM output
#define FAN_2          4   ///< Left fan 2 PWM output
#define FAN_3          5   ///< Left fan 3 PWM output
#define FAN_4          9   ///< Left fan 4 PWM output

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