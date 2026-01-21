#!/bin/bash
# Stop script for DryBox system
# This script stops the running JSONparse.py and serialDataParser.py processes
#
# Usage:
#   ./stop_drybox.sh                  - Normal shutdown (sends SIGINT to JSONparse.py)
#   ./stop_drybox.sh --force          - Force kill processes immediately
#   ./stop_drybox.sh --ensure-alloff  - Make sure ALLOFF commands are sent to Teensy controllers
#   ./stop_drybox.sh --timeout=30     - Wait up to 30 seconds for JSONparse.py to exit gracefully
#
# The script sends SIGINT (KeyboardInterrupt) to JSONparse.py to trigger the send_shutoff()
# function that sends ALLOFF commands to all Teensy controllers.

# Get the directory where this script is located (Scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up one level to get RPI5 directory
BASE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$BASE_DIR/DataLogging"

# Configuration variables - Adjust these as needed
SHUTDOWN_TIMEOUT=3     # Maximum seconds to wait for JSONparse.py to shut down gracefully
LOG_FILE="$LOG_DIR/drybox_shutdown.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Parse command line arguments
FORCE_KILL=false
ENSURE_ALLOFF=false

# Process command line arguments
for arg in "$@"; do
    case $arg in
        --force)
            FORCE_KILL=true
            shift
            ;;
        --ensure-alloff)
            ENSURE_ALLOFF=true
            shift
            ;;
        --timeout=*)
            custom_timeout="${arg#*=}"
            if [[ "$custom_timeout" =~ ^[0-9]+$ ]]; then
                SHUTDOWN_TIMEOUT=$custom_timeout
                echo "Using custom timeout: $SHUTDOWN_TIMEOUT seconds" >> "$LOG_FILE"
            else
                echo "Invalid timeout value. Using default: $SHUTDOWN_TIMEOUT seconds" >> "$LOG_FILE"
            fi
            shift
            ;;
    esac
done

echo "----------------------------------------------" >> "$LOG_FILE"
echo "Stopping DryBox system at $(date)" >> "$LOG_FILE"
echo "----------------------------------------------" >> "$LOG_FILE"

# Find PIDs of running processes
JSONPARSE_PID=$(pgrep -f "python3 .*/JSONparse.py")
SERIALDEBUG_PID=$(pgrep -f "python3 .*/serialDebug.py")
LOGDB_PID=$(pgrep -f "python3 .*/logDB.py")

if [ "$FORCE_KILL" = true ]; then
    echo "Force kill mode enabled. Immediately terminating processes." >> "$LOG_FILE"
    
    # Force kill logDB.py
    if [ -n "$LOGDB_PID" ]; then
        echo "Force killing logDB.py (PID: $LOGDB_PID)..." >> "$LOG_FILE"
        kill -9 $LOGDB_PID
    fi
    
    # Force kill serialDebug.py
    if [ -n "$SERIALDEBUG_PID" ]; then
        echo "Force killing serialDebug.py (PID: $SERIALDEBUG_PID)..." >> "$LOG_FILE"
        kill -9 $SERIALDEBUG_PID
    fi
    
    # Force kill JSONparse.py
    if [ -n "$JSONPARSE_PID" ]; then
        echo "Force killing JSONparse.py (PID: $JSONPARSE_PID)..." >> "$LOG_FILE"
        kill -9 $JSONPARSE_PID
    fi
    
    # Set ENSURE_ALLOFF to true since we're bypassing the normal shutdown
    ENSURE_ALLOFF=true
else
    # Normal shutdown procedure
    # Stop logDB.py first
    if [ -n "$LOGDB_PID" ]; then
        echo "Stopping logDB.py (PID: $LOGDB_PID)..." >> "$LOG_FILE"
        kill -SIGINT $LOGDB_PID
        sleep 2
        
        # Check if it's still running
        if kill -0 $LOGDB_PID 2>/dev/null; then
            echo "Process didn't exit gracefully, forcing termination..." >> "$LOG_FILE"
            kill -9 $LOGDB_PID
        else
            echo "logDB.py stopped successfully" >> "$LOG_FILE"
        fi
    else
        echo "logDB.py is not running" >> "$LOG_FILE"
    fi
    
    # Stop serialDebug.py next
if [ -n "$SERIALDEBUG_PID" ]; then
    echo "Stopping serialDebug.py (PID: $SERIALDEBUG_PID)..." >> "$LOG_FILE"
    kill -SIGINT $SERIALDEBUG_PID
    sleep 2
    
    # Check if it's still running
    if kill -0 $SERIALDEBUG_PID 2>/dev/null; then
        echo "Process didn't exit gracefully, forcing termination..." >> "$LOG_FILE"
        kill -9 $SERIALDEBUG_PID
    else
        echo "serialDebug.py stopped successfully" >> "$LOG_FILE"
    fi
else
    echo "serialDebug.py is not running" >> "$LOG_FILE"
fi

# Stop JSONparse.py next
if [ -n "$JSONPARSE_PID" ]; then
    echo "Stopping JSONparse.py (PID: $JSONPARSE_PID)..." >> "$LOG_FILE"
    echo "Sending KeyboardInterrupt (SIGINT) signal to allow proper shutdown sequence..." >> "$LOG_FILE"
    kill -SIGINT $JSONPARSE_PID
    
    # Give JSONparse.py more time to send ALLOFF commands to all Teensy controllers
    echo "Waiting for JSONparse.py to send ALLOFF commands to Teensy controllers..." >> "$LOG_FILE"
    
    # Wait up to SHUTDOWN_TIMEOUT seconds for JSONparse.py to exit gracefully
    timeout=$SHUTDOWN_TIMEOUT
    while [ $timeout -gt 0 ] && kill -0 $JSONPARSE_PID 2>/dev/null; do
        echo "Waiting for JSONparse.py to complete shutdown sequence ($timeout seconds remaining)..." >> "$LOG_FILE"
        sleep 1
        timeout=$((timeout-1))
    done
    
    # Check if it's still running after timeout
    if kill -0 $JSONPARSE_PID 2>/dev/null; then
        echo "WARNING: JSONparse.py is still running after $SHUTDOWN_TIMEOUT seconds" >> "$LOG_FILE"
        echo "The ALLOFF commands may not have been sent properly" >> "$LOG_FILE"
        echo "Force terminating JSONparse.py..." >> "$LOG_FILE"
        kill -9 $JSONPARSE_PID
    else
        echo "JSONparse.py stopped successfully - ALLOFF commands should have been sent" >> "$LOG_FILE"
    fi
else
    echo "JSONparse.py is not running" >> "$LOG_FILE"
fi

fi  # End of normal shutdown procedure (closes the else branch from force kill check)

echo "DryBox system stopped at $(date)" >> "$LOG_FILE"
echo "----------------------------------------------" >> "$LOG_FILE"

# If ensure-alloff is specified, we'll manually send ALLOFF commands to all Teensy devices
if [ "$ENSURE_ALLOFF" = true ]; then
    echo "Ensuring ALLOFF commands are sent to Teensy controllers..." >> "$LOG_FILE"
    
    # Get the config file path dynamically
    CONFIG_PATH="$BASE_DIR/JSONS/configParser.json"
    
    if [ -f "$CONFIG_PATH" ]; then
        echo "Reading serial port configuration from $CONFIG_PATH..." >> "$LOG_FILE"
        
        # We'll use Python to parse the JSON and send the ALLOFF commands
        python3 -c "
import json
import serial
import time

try:
    # Load configuration
    with open('$CONFIG_PATH', 'r') as f:
        config = json.load(f)
    
    # Find Teensy devices
    for device in config['serial_ports']:
        try:
            port = device['port']
            name = device['name']
            baud = device['baud_rate']
            
            print(f'Sending ALLOFF command to {name} on {port}...')
            
            # Open serial connection
            ser = serial.Serial(port, baud, timeout=1)
            time.sleep(0.5)
            
            # Send ALLOFF command
            ser.write(b'ALLOFF\\n')
            time.sleep(0.5)
            
            # Read response
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f'Response from {name}: {response}')
            
            # Close connection
            ser.close()
            print(f'ALLOFF command sent to {name}')
            
        except Exception as e:
            print(f'Error sending ALLOFF to {name}: {e}')
    
except Exception as e:
    print(f'Error: {e}')
" >> "$LOG_FILE" 2>&1
    else
        echo "Config file not found at $CONFIG_PATH, cannot send ALLOFF commands manually" >> "$LOG_FILE"
    fi
fi

# Print a minimal success message to the terminal
echo "DryBox system stopped successfully."
if [ -n "$JSONPARSE_PID" ] || [ -n "$SERIALDEBUG_PID" ] || [ -n "$LOGDB_PID" ]; then
    echo "- Stopped processes: ${JSONPARSE_PID:+JSONparse.py }${SERIALDEBUG_PID:+serialDebug.py }${LOGDB_PID:+logDB.py}"
    echo "- Log file: $LOG_FILE"
else
    echo "- No running DryBox processes were found."
fi
