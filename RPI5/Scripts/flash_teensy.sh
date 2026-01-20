#!/bin/bash
# This script flashes Teensy microcontrollers using PlatformIO

# Get the directory where this script is located (Scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up one level to get RPI5 directory, then up one more to get drybox directory
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_DIR="$(dirname "$SCRIPT_DIR")/DataLogging"

# Define paths dynamically
PIO_PROJECT_PATH="$BASE_DIR/PlatformIO/Teensys"
LOG_FILE="$LOG_DIR/teensy_flash.log"
PIO_ENV_PATH="$HOME/pio-env"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Start logging
echo "=======================================" >> "$LOG_FILE"
echo "Flash operation started at $(date)" >> "$LOG_FILE"
echo "=======================================" >> "$LOG_FILE"

# Check if target environment is provided
if [ -z "$1" ]; then
    echo "Error: No target environment specified." | tee -a "$LOG_FILE"
    echo "Usage: $0 [TeensyHVAC|TeensyLeft|TeensyRight|all]" | tee -a "$LOG_FILE"
    exit 1
fi

TARGET="$1"

# Function to flash a specific Teensy environment
flash_teensy() {
    local env="$1"
    echo "Flashing $env..." | tee -a "$LOG_FILE"
    
    # Change to the PlatformIO project directory
    cd "$PIO_PROJECT_PATH" || {
        echo "Error: Could not change to project directory $PIO_PROJECT_PATH" | tee -a "$LOG_FILE"
        return 1
    }
    
    # Activate the PlatformIO virtual environment
    if [ -f "$PIO_ENV_PATH/bin/activate" ]; then
        echo "Activating PlatformIO virtual environment..." | tee -a "$LOG_FILE"
        # We need to source the activate script in the current shell context
        source "$PIO_ENV_PATH/bin/activate"
        
        # Verify activation
        if command -v pio >/dev/null 2>&1; then
            echo "PlatformIO environment activated successfully" | tee -a "$LOG_FILE"
        else
            echo "Error: Failed to activate PlatformIO environment (pio command not found)" | tee -a "$LOG_FILE"
            return 1
        fi
    else
        echo "Error: PlatformIO virtual environment not found at $PIO_ENV_PATH" | tee -a "$LOG_FILE"
        return 1
    fi
    
    # Run PlatformIO upload command
    echo "Running: pio run -e \"$env\" --target upload" | tee -a "$LOG_FILE"
    pio run -e "$env" --target upload 2>&1 | tee -a "$LOG_FILE"
    
    # Check result
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "Successfully flashed $env" | tee -a "$LOG_FILE"
        return 0
    else
        echo "Failed to flash $env" | tee -a "$LOG_FILE"
        return 1
    fi
}

# Flash based on target specification
case "$TARGET" in
    "TeensyHVAC")
        flash_teensy "TeensyHVAC"
        exit $?
        ;;
    "TeensyLeft")
        flash_teensy "TeensyLeft"
        exit $?
        ;;
    "TeensyRight")
        flash_teensy "TeensyRight"
        exit $?
        ;;
    "all")
        # Flash all Teensy environments
        failed=0
        flash_teensy "TeensyHVAC" || failed=1
        flash_teensy "TeensyLeft" || failed=1
        flash_teensy "TeensyRight" || failed=1
        
        if [ $failed -eq 0 ]; then
            echo "All Teensy environments flashed successfully" | tee -a "$LOG_FILE"
            exit 0
        else
            echo "One or more Teensy environments failed to flash" | tee -a "$LOG_FILE"
            exit 1
        fi
        ;;
    *)
        echo "Error: Invalid target environment '$TARGET'" | tee -a "$LOG_FILE"
        echo "Usage: $0 [TeensyHVAC|TeensyLeft|TeensyRight|all]" | tee -a "$LOG_FILE"
        exit 1
        ;;
esac
