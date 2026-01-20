#!/usr/bin/env python3
# Dynamic paths version of serialDebug.py

import serial
import time
import os
from datetime import datetime, timezone  # Changed from import datetime
import argparse
import signal
import sys
import json
import random
import logging
import re
from pathlib import Path

# Define paths dynamically based on script location
# Get the directory where this script is located (Python folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get RPI5 directory
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, "DataLogging")
JSON_DIR = os.path.join(BASE_DIR, "JSONS")

# Configuration file paths - Dynamic paths
CONFIG_PATH = os.path.join(JSON_DIR, 'configDebug.json')  # Changed to configParser.json
LOG_PATH = os.path.join(LOG_DIR, 'serialDebug.log')

# Set up logging
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH)
        # Removed console handler to prevent terminal output
    ]
)

# Custom print function that logs to file only (not to console)
def log_print(*args, **kwargs):
    message = " ".join(map(str, args))
    logging.info(message)
    # Removed console output

# Default configuration - These values will be overridden by the JSON config
DEFAULT_CONFIG = {
    "serial_ports": [
        {
            "port": "/dev/ttyUSB0",
            "baud_rate": 115200,
            "name": "Teensy1"
        },
        # Add more Teensy devices as needed
        # {
        #     "port": "/dev/ttyUSB1",
        #     "baud_rate": 115200,
        #     "name": "Teensy2"
        # },
        # {
        #     "port": "/dev/ttyUSB2",
        #     "baud_rate": 115200,
        #     "name": "Teensy3"
        # }
    ],
    "log_interval_ms": 1000,  # Milliseconds between log entries
    "debug": True,
    "process_vectors": True  # Whether to process and log vector data
}

# Global variables
config = DEFAULT_CONFIG
serial_connections = []
running = True

def load_config():
    """Load configuration from config.json if it exists, otherwise use defaults"""
    global config
    config_path = Path(CONFIG_PATH)
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                # Update default config with loaded values
                config.update(loaded_config)
                log_print(f"Loaded configuration from {config_path}")
        except Exception as e:
            log_print(f"Error loading configuration: {e}")
            log_print("Using default configuration")
    else:
        log_print(f"Configuration file not found at {config_path}")
        log_print("Using default configuration")
        # Save default config for future editing
        try:
            os.makedirs(config_path.parent, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                log_print(f"Default configuration saved to {config_path}")
        except Exception as e:
            log_print(f"Error saving default configuration: {e}")

def setup_serial_connections():
    """Initialize all serial connections"""
    global serial_connections
    
    # First, check what serial ports are available
    import glob
    available_ports = glob.glob('/dev/tty*')
    log_print(f"Available serial ports: {[p for p in available_ports if 'AMA' in p or 'ACM' in p or 'USB' in p]}")
    
    for device in config["serial_ports"]:
        try:
            log_print(f"Attempting to connect to {device['name']} on {device['port']}...")
            
            # Check if port exists
            if device['port'] not in available_ports:
                log_print(f"Warning: Port {device['port']} not found in available ports!")
            
            ser = serial.Serial(
                port=device["port"],
                baudrate=device["baud_rate"],
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Clear any initial data
            ser.reset_input_buffer()
            
            serial_connections.append({
                "connection": ser,
                "name": device["name"],
                "port": device["port"],
                "buffer": ""
            })
            log_print(f"Successfully connected to {device['name']} on {device['port']} at {device['baud_rate']} baud")
        except Exception as e:
            log_print(f"Error connecting to {device['name']} on {device['port']}: {e}")
            log_print(f"   If this is a permission error, try: sudo chmod 666 {device['port']}")

def parse_sensor_data_vector(message):
    """
    Parse sensor data from messages like:
    "✅ Heater | Temp: 28.20 °C | Hum: 43.70 %RH"
    
    Returns a vector format with timestamp, separate sensor names for temperature and humidity, 
    and their corresponding values.
    
    Example output:
    {
        'timestamp': '2025-06-05T15:42:23.456789',
        'sensors': [
            {'name': 'Heater_Temp', 'value': 28.20},
            {'name': 'Heater_Hum', 'value': 43.70}
        ]
    }
    """
    # Skip non-sensor data messages
    if not message.startswith('✅'):
        return None
    
    # Extract sensor name, temperature, and humidity using regex
    pattern = r'✅ (\w+(?:_\w+)*) \| Temp: ([\d.]+) °C \| Hum: ([\d.]+) %RH'
    match = re.match(pattern, message)
    
    if not match:
        return None
        
    sensor_base_name = match.group(1)
    temperature = float(match.group(2))
    humidity = float(match.group(3))
    
    timestamp = datetime.now().isoformat()
    
    return {
    'timestamp': timestamp,
    'sensors': [
        {'name': f"{sensor_base_name}_Temp", 'value': temperature},
        {'name': f"{sensor_base_name}_Hum", 'value': humidity}
        ]
    }

def process_debug_line(device, line):
    """Process a debug message line and log it"""
    device_name = device["name"]
    # Log the data to debug log file for real-time verification
    logging.info(f"DATA: {device_name}: {line}")
    
    # Parse and log data in vector format if enabled in config
    if config.get("process_vectors", True):  # Default to True if not specified
        vector_data = parse_sensor_data_vector(line)
        if vector_data:
            vector_log = f"VECTOR DATA: {device_name} - Timestamp: {vector_data['timestamp']}"
            for sensor in vector_data['sensors']:
                vector_log += f"\n  - {sensor['name']}: {sensor['value']}"
            logging.info(vector_log)
    
    # Debug logging if enabled in config
    if config["debug"]:
        logging.debug(f"{device_name}: {line}")

def read_serial_data():
    """Read data from all serial connections"""
    for device in serial_connections:
        ser = device["connection"]
        
        try:
            in_waiting = ser.in_waiting
            if in_waiting > 0:
                # Read incoming data
                logging.debug(f"Data available on {device['name']} ({in_waiting} bytes)")
                new_data = ser.read(in_waiting).decode('utf-8', errors='replace')
                device["buffer"] += new_data
                
                # Process complete lines
                while '\n' in device["buffer"]:
                    line, device["buffer"] = device["buffer"].split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Process as debug line and log
                    process_debug_line(device, line)
            else:
                # Only print this message occasionally to avoid log spam
                if random.random() < 0.01:  # 1% chance to print this message
                    logging.debug(f"No data on {device['name']} port {device['port']}")
                    
        except Exception as e:
            logging.error(f"Error reading from {device['name']}: {e}")
            # Try to reconnect
            try:
                ser.close()
                time.sleep(1)
                ser.open()
                logging.info(f"Reconnected to {device['name']}")
            except:
                logging.error(f"Failed to reconnect to {device['name']}")

def signal_handler(sig, frame):
    """Handle signals gracefully (SIGINT/SIGTERM)"""
    global running
    
    # Don't use logging in signal handlers to avoid reentrant calls
    # Just set the flag and let the main loop handle shutdown
    running = False
    
    # If it's SIGINT (ctrl+c or direct kill), exit immediately after cleanup
    if sig == signal.SIGINT:
        log_print("Immediate shutdown requested. Closing files...")
        cleanup_resources()
        sys.exit(0)

def cleanup_resources():
    """Close all open resources safely"""
    # Close all serial connections
    for device in serial_connections:
        try:
            connection = device["connection"]
            if connection.is_open:
                connection.close()
                log_print(f"Closed connection to {device['name']}")
        except Exception as e:
            log_print(f"Error closing connection to {device['name']}: {e}")

def main():
    """Main function"""
    global running
    
    # Set up signal handler for Ctrl+C
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    log_print("Signal handlers registered for graceful shutdown (SIGTERM/SIGINT)")
    log_print("Use ./stop_drybox.sh to properly shut down this program")
    log_print(f"Logging to {LOG_PATH}")
    
    # Load configuration
    load_config()
    
    # Set up serial connections
    setup_serial_connections()
    
    if not serial_connections:
        log_print("No serial connections established. Exiting.")
        return
    
    log_print("Serial data parser running. Press Ctrl+C to exit.")
    
    # Main loop
    last_log_time = time.time() * 1000  # Convert to ms
    
    while running:
        current_time = time.time() * 1000  # Convert to ms
        
        # Only log at specified intervals
        if (current_time - last_log_time) >= config["log_interval_ms"]:
            read_serial_data()
            last_log_time = current_time
        
        # Sleep to prevent CPU hogging
        time.sleep(0.01)
    
    # Log shutdown message after the main loop exits
    if not running:
        log_print("Received shutdown signal. Shutting down...")
    
    # Clean up
    cleanup_resources()
    
    log_print("Serial data parser shut down successfully.")

if __name__ == "__main__":
    main()