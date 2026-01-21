#!/bin/bash
# Startup script for DryBox system
# This script runs the JSONparse.py program followed by serialDataParser.py after 1 second

# Get the directory where this script is located (Scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up one level to get RPI5 directory
BASE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$BASE_DIR/DataLogging"
PYTHON_DIR="$BASE_DIR/Python"

# Define paths dynamically
LOG_FILE="$LOG_DIR/drybox_startup.log"
JSONPARSE_PATH="$PYTHON_DIR/JSONparse.py"
SERIALDEBUG_PATH="$PYTHON_DIR/serialDebug.py"
LOGDB_PATH="$PYTHON_DIR/logDB.py"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "----------------------------------------------" >> "$LOG_FILE"
echo "Starting DryBox system at $(date)" >> "$LOG_FILE"
echo "----------------------------------------------" >> "$LOG_FILE"

# Check if the JSONparse script exists
if [ ! -f "$JSONPARSE_PATH" ]; then
    echo "ERROR: JSONparse script not found at $JSONPARSE_PATH" >> "$LOG_FILE"
    echo "ERROR: JSONparse script not found at $JSONPARSE_PATH"
    exit 1
fi

# Check if the serialDebug script exists
if [ ! -f "$SERIALDEBUG_PATH" ]; then
    echo "ERROR: serialDebug script not found at $SERIALDEBUG_PATH" >> "$LOG_FILE"
    echo "ERROR: serialDebug script not found at $SERIALDEBUG_PATH"
    exit 1
fi

# Check if the logDB script exists
if [ ! -f "$LOGDB_PATH" ]; then
    echo "ERROR: logDB script not found at $LOGDB_PATH" >> "$LOG_FILE"
    echo "ERROR: logDB script not found at $LOGDB_PATH"
    exit 1
fi

# Make sure scripts are executable
chmod +x "$JSONPARSE_PATH"
chmod +x "$SERIALDEBUG_PATH"
chmod +x "$LOGDB_PATH"

# Start JSONparse.py in the background
echo "Starting JSONparse.py in the background..." >> "$LOG_FILE"
python3 "$JSONPARSE_PATH" > /tmp/jsonparse.log 2>&1 &
JSONPARSE_PID=$!

# Wait for 1 second
echo "Waiting 1 second before starting serialDataParser.py..." >> "$LOG_FILE"
sleep 1

# Check if JSONparse.py is still running (basic error check)
if ! ps -p $JSONPARSE_PID > /dev/null; then
    echo "ERROR: JSONparse.py failed to start or exited too quickly" >> "$LOG_FILE"
    echo "Last 10 lines of JSONparse.py output:" >> "$LOG_FILE"
    tail -n 10 /tmp/jsonparse.log >> "$LOG_FILE"
    echo "ERROR: JSONparse.py failed to start or exited too quickly"
    exit 1
else
    echo "JSONparse.py started successfully with PID $JSONPARSE_PID" >> "$LOG_FILE"
fi

# Start serialDebug.py
echo "Starting serialDebug.py..." >> "$LOG_FILE"
python3 "$SERIALDEBUG_PATH" >> "$LOG_FILE" 2>&1 &
SERIALDEBUG_PID=$!

# Wait a moment to check if serialDebug.py is running
sleep 2
if ! ps -p $SERIALDEBUG_PID > /dev/null; then
    echo "ERROR: serialDebug.py failed to start or exited too quickly" >> "$LOG_FILE"
    echo "ERROR: serialDebug.py failed to start or exited too quickly"
    exit 1
else
    echo "serialDebug.py started successfully with PID $SERIALDEBUG_PID" >> "$LOG_FILE"
fi

# Wait 1 second before starting logDB.py
echo "Waiting 1 second before starting logDB.py..." >> "$LOG_FILE"
sleep 1

# Start logDB.py
echo "Starting logDB.py..." >> "$LOG_FILE"
python3 "$LOGDB_PATH" >> "$LOG_FILE" 2>&1 &
LOGDB_PID=$!

# Wait a moment to check if logDB.py is running
sleep 2
if ! ps -p $LOGDB_PID > /dev/null; then
    echo "ERROR: logDB.py failed to start or exited too quickly" >> "$LOG_FILE"
    echo "ERROR: logDB.py failed to start or exited too quickly"
    exit 1
else
    echo "logDB.py started successfully with PID $LOGDB_PID" >> "$LOG_FILE"
fi

echo "Both processes started successfully!" >> "$LOG_FILE"
echo "JSONparse.py PID: $JSONPARSE_PID" >> "$LOG_FILE"
echo "serialDebug.py PID: $SERIALDEBUG_PID" >> "$LOG_FILE"
echo "logDB.py PID: $LOGDB_PID" >> "$LOG_FILE"
echo "To check status, use: ps -p $JSONPARSE_PID -p $SERIALDEBUG_PID -p $LOGDB_PID" >> "$LOG_FILE"
echo "DryBox system started at $(date)" >> "$LOG_FILE"
echo "----------------------------------------------" >> "$LOG_FILE"

# Print a minimal success message to the terminal
echo "DryBox system started successfully."
echo "- JSONparse.py PID: $JSONPARSE_PID"
echo "- serialDebug.py PID: $SERIALDEBUG_PID"
echo "- logDB.py PID: $LOGDB_PID"
echo "- Log file: $LOG_FILE"
echo "- To stop, run: ./stop_drybox.sh"

# Exit the script, but leave the background processes running
exit 0
