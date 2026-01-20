import json
import time
import RPi.GPIO as GPIO
import serial
import sys
import os
import signal  # Added for signal handling
import logging
from datetime import datetime

# Define paths dynamically based on script location
# Get the directory where this script is located (Python folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get RPI5 directory
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, "DataLogging")
JSON_DIR = os.path.join(BASE_DIR, "JSONS")

# PID file location
PID_FILE = '/tmp/jsonparse.pid'

# Configuration file paths - Dynamic paths
CONFIG_PATH = os.path.join(JSON_DIR, 'configParser.json')
SHELL_JSON_PATH = os.path.join(JSON_DIR, 'shellJson.json')
LOG_PATH = os.path.join(LOG_DIR, 'jsonParse.log')

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
    if 'end' in kwargs and kwargs['end'] != '\n':
        if kwargs['end'] == '\r':  # For updating countdown timer
            logging.info(f"TIMER: {message}")
            # Removed console output
            return
    logging.info(message)
    # Removed console output

def ensure_single_instance():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())

            # Check if the old PID is still running
            if os.path.exists(f"/proc/{old_pid}"):
                log_print(f"Another instance (PID {old_pid}) is running. Killing it...")
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(1)  # wait briefly for cleanup
        except Exception as e:
            log_print(f"Error checking/killing old process: {e}")

    # Write current PID to file
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        log_print(f"Registered current PID {os.getpid()} to {PID_FILE}")
    except Exception as e:
        log_print(f"Error writing PID file: {e}")
        sys.exit(1)

# Define paths for layer control
NEXT_LAYER_TRIGGER = os.path.join(LOG_DIR, "next_layer.trigger")
PREV_LAYER_TRIGGER = os.path.join(LOG_DIR, "prev_layer.trigger")
JUMP_TO_LAYER_TRIGGER = os.path.join(LOG_DIR, "jump_to_layer.trigger")
NEXT_STEP_TRIGGER = os.path.join(LOG_DIR, "next_step.trigger")
PREV_STEP_TRIGGER = os.path.join(LOG_DIR, "prev_step.trigger")
CURRENT_LAYER_INFO = os.path.join(LOG_DIR, "current_layer.txt")

# ESTOP PIN - GPIO PIN 22
ESTOP_PIN = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(ESTOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# PAUSE PIN - GPIO PIN 27
PAUSE_PIN = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(PAUSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# NEXT PIN - GPIO PIN 17
NEXT_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Accepted Deltas from DB Control Page
deltaShellTemperature = 1 #+/- Celsius/Kelevin (Same)
deltaAirTemperature   = 2 #+/- Celsius/Kelvin (Same)
deltaHumidity         = 5 #+/- Percent Relative Humidity
deltaShellFanAirflow  = 5 #+/- Percentage
sidesOn               = 2 #How many towers on 

# JSON Parameters Variable Declarations
name = []
ambientTemperature = []
shellTemperature = []
humidity = []
duration = []
shellSpeed = []
fanSpeed = []
# KpValue = []
# KiValue = []
# KdValue = []

# Flag to indicate if shutdown is in progress
shutdown_in_progress = False

# Signal handler for SIGTERM and SIGINT (sent by stop_drybox.sh)
def signal_handler(signum, frame):
    global shutdown_in_progress
    
    if shutdown_in_progress:
        # If we're already shutting down and get another signal, exit immediately
        sys.exit(1)
        
    shutdown_in_progress = True
    
    if signum == signal.SIGTERM:
        # For SIGTERM, we set the flag and let the main loop handle it
        # Don't use logging in signal handlers to avoid reentrant calls
        pass
    elif signum == signal.SIGINT:
        # For SIGINT, directly call send_shutoff and clean up
        try:
            send_shutoff()
            GPIO.cleanup()
        except Exception as e:
            pass  # Don't log in signal handler
        finally:
            sys.exit(0)

# Register the signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Inform about signal handling setup
log_print("Signal handlers registered for graceful shutdown (SIGTERM/SIGINT)")
log_print("Use ./stop_drybox.sh to properly shut down this program")
log_print(f"Logging to {LOG_PATH}")

# Load configuration from config.json
def load_config():
    """Load configuration from config.json"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            log_print(f"Loaded configuration from {CONFIG_PATH}")
            return config
    except Exception as e:
        log_print(f"Error loading configuration: {e}")
        sys.exit(1)

# Get the config
config = load_config()

# Connecting to Teensy's using persistent device paths by ID
try:
    # Find device configurations in config.json
    teensy_configs = {device["name"]: device for device in config["serial_ports"]}
    
    # Check if all required Teensys are in the config
    required_teensys = ["TeensyHVAC", "TeensyLeft", "TeensyRight"]
    missing = [name for name in required_teensys if name not in teensy_configs]
    
    if missing:
        raise serial.SerialException(f"Missing configuration for Teensy devices: {', '.join(missing)}")
    
    # Connect to each Teensy using its persistent path
    hvac_config = teensy_configs["TeensyHVAC"]
    left_config = teensy_configs["TeensyLeft"]
    right_config = teensy_configs["TeensyRight"]
    
    log_print(f"Connecting to TeensyHVAC on {hvac_config['port']}...")
    serHVAC = serial.Serial(hvac_config["port"], hvac_config["baud_rate"], timeout=1)
    time.sleep(1)
    serHVAC.reset_input_buffer()
    serHVAC.reset_output_buffer()

    log_print(f"Connecting to TeensyLeft on {left_config['port']}...")
    serLEFT = serial.Serial(left_config["port"], left_config["baud_rate"], timeout=1)
    time.sleep(1)

    log_print(f"Connecting to TeensyRight on {right_config['port']}...")
    serRIGHT = serial.Serial(right_config["port"], right_config["baud_rate"], timeout=1)
    time.sleep(1)
    
    log_print("All Teensy devices connected successfully using persistent device paths.")

except serial.SerialException as e:
    log_print(f"[ERROR] Could not open one or more serial ports: {e}")
    log_print("Check if all Teensy devices are connected and properly recognized.")
    log_print("Try unplugging and reconnecting the USB cables if needed.")
    sys.exit(1)
except Exception as e:
    log_print(f"[ERROR] Unexpected error during initialization: {e}")
    sys.exit(1)


def kelvin_to_celsius(kelvin: float) -> float:
    """Converts temperature from Kelvin to Celsius."""
    return kelvin - 273.15

def read_shell_layers(filename):
    """
    Parses a JSON file containing shell layer data and extracts time-series parameters.

    The function reads a JSON file with the structure:
        {
            "shell layer": [
                {
                    "name": str,
                    "ambient_temperature": [float],
                    "shell_temperature": [float],
                    "humidity": [float],
                    "time": [float],
                    "shell_speed": [float],
                    "fan_speed": [float]
                },
                ...
            ]
        }

    Extracted values are appended to global lists:
    - name, ambientTemperature, shellTemperature, humidity, duration, shellSpeed, fanSpeed

    Args:
        filename (str): Path to the JSON file containing shell layer data.

    Returns:
        None
    """
    # Open and parse the JSON file
    with open(filename, 'r') as file:
        data = json.load(file)

    # Check for the required top-level key
    if "shell_layer" not in data:
        log_print("No 'shell_layer' category found.")
        return

    # Iterate through each shell layer and extract parameters
    for idx, layer in enumerate(data["shell_layer"], 1):
        dataName = layer['name']
        dataAmbientTemperature = layer['ambient_temperature']  # list
        dataShellTemperature = layer['shell_temperature']      # list
        dataHumidity = layer['humidity']                       # list
        dataTime = layer['time']                               # list
        dataShellSpeed = layer['shell_speed']                  # list
        dataFanSpeed = layer['fan_speed']                      # list

        # TODO
        # dataKp = layer['Kp']
        # dataKi = layer['Ki']
        # dataKd = layer['Kd']

        # print(f"Shell Layer {idx}:")
        # print(f"  Name                : {dataName}")
        # print(f"  Ambient Temperatures (K) : {dataAmbientTemperature}")
        # print(f"  Ambient Temperatures (C) : {[kelvin_to_celsius(t) for t in dataAmbientTemperature]}")
        # print(f"  Shell Temperatures (K)   : {dataShellTemperature}")
        # print(f"  Shell Temperatures (C)   : {[kelvin_to_celsius(t) for t in dataShellTemperature]}")
        # print(f"  Humidity (%)             : {dataHumidity}")
        # print(f"  Time (m)                 : {dataTime}")
        # print(f"  Shell Speed (RPM)        : {dataShellSpeed}")
        # print(f"  Fan Speed (CFM)          : {dataFanSpeed}")
        # print()

        # Append values to the global lists
        name.append(dataName)
        ambientTemperature.append(dataAmbientTemperature)
        shellTemperature.append(dataShellTemperature)
        humidity.append(dataHumidity)
        duration.append(dataTime)
        shellSpeed.append(dataShellSpeed)
        fanSpeed.append(dataFanSpeed)
        
        #TODO
        #KpValue.append(dataKp)
        #KiValue.append(dataKi)
        #KdValue.append(dataKd)

def sendHVAC(idx, idx2):
    """
    Sends a formatted HVAC control command over serial to the Teensy.

    This function constructs and transmits a command to control HVAC settings for a specific
    shell layer and time index. It pulls values from pre-populated global arrays and sends them
    to the Teensy microcontroller over a serial connection in the following format:

        START-ATEMP:<val>,STEMP:<val>,HUM:<val>,TIME:<val>,OMEGA:<val>,
        DST:<val>,DAT:<val>,DH:<val>,DSFA:<val>\n

    Args:
        idx (int): Index of the shell layer.
        idx2 (int): Time index within the selected layer.

    Returns:
        None. Sends data over serial and waits for acknowledgment from the Teensy.

    Notes:
        - Relies on global arrays: ambientTemperature, shellTemperature, humidity,
          duration, shellSpeed, deltaShellTemperature, deltaAirTemperature,
          deltaHumidity, deltaShellFanAirflow.
        - Assumes `serHVAC` is a configured and open serial.Serial object.
        - Calls `waitForACK()` to ensure the command was received.
    """
    # Construct command string using formatted data from shell layer arrays
    command = (
        f"START-ATEMP:{ambientTemperature[idx][idx2]},"
        f"STEMP:{shellTemperature[idx][idx2]},"
        f"HUM:{humidity[idx][idx2]},"
        f"TIME:{duration[idx][idx2]},"
        f"OMEGA:{shellSpeed[idx][idx2]},"
        f"FAN:{fanSpeed[idx][idx2]},"
        f"DST:{deltaShellTemperature},"
        f"DAT:{deltaAirTemperature},"
        f"DH:{deltaHumidity},"
        f"DSFA:{deltaShellFanAirflow}\n"
    )

    # command2 = (
    #     f"PID-Kp:{KpValue},"
    #     f"Ki:{KiValue},"
    #     f"Kd:{KdValue}\n"
    # )

    # Clear serial output buffer and send the command
    serHVAC.flush()
    serHVAC.write(command.encode('utf-8'))
    serHVAC.flush()

    # Logging for confirmation
    log_print(f"[Pi → TeensyHVAC] {command.strip()}")
    log_print(">> Command sent. Waiting for Teensy's response:")

    # Wait for ACK/UKN response from Teensy
    waitForACK(command, serHVAC)

    #TODO SEND PID VALUES


def sendOther(idx, idx2):
    """
    Sends a shell layer HVAC command to one or both Teensy devices (LEFT and optionally RIGHT).

    Constructs and sends a formatted command string over serial using environmental data
    from the shell layer and time index provided. If `sidesOn == 2`, the command is sent to
    both the LEFT and RIGHT Teensy controllers. Otherwise, it's sent only to LEFT.

    Command format:
        START-ATEMP:<val>,STEMP:<val>,HUM:<val>,TIME:<val>,FAN:<val>,
              DST:<val>,DAT:<val>,DH:<val>,DSFA:<val>\n

    Args:
        idx (int): Index of the shell layer.
        idx2 (int): Time index within the selected layer.

    Returns:
        None

    Notes:
        - Uses global arrays: ambientTemperature, shellTemperature, humidity,
          duration, fanSpeed, and delta parameters.
        - Assumes `serLEFT` and `serRIGHT` are open serial connections.
        - `sidesOn` controls whether one or both Teensy devices are used.
        - Waits for ACK after sending to each device.
    """
    # Build command string from global data
    command = (
        f"START-ATEMP:{ambientTemperature[idx][idx2]},"
        f"STEMP:{shellTemperature[idx][idx2]},"
        f"HUM:{humidity[idx][idx2]},"
        f"TIME:{duration[idx][idx2]},"
        f"FAN:{fanSpeed[idx][idx2]},"
        f"DST:{deltaShellTemperature},"
        f"DAT:{deltaAirTemperature},"
        f"DH:{deltaHumidity},"
        f"DSFA:{deltaShellFanAirflow}\n"
    )

    # Send to RIGHT if both sides are active
    if sidesOn == 2:
        log_print(f"[Pi → TeensyRIGHT] {command.strip()}")
        log_print(">> Command sent. Waiting for RIGHT Teensy's response:")
        serRIGHT.write(command.encode('utf-8'))
        waitForACK(command, serRIGHT)

    # Always send to LEFT
    log_print(f"[Pi → TeensyLEFT] {command.strip()}")
    log_print(">> Command sent. Waiting for LEFT Teensy's response:")
    serLEFT.write(command.encode('utf-8'))
    waitForACK(command, serLEFT)

def send_shutoff():
    """
    Sends a unified 'ALLOFF' command to shut down all HVAC-related Teensy devices.

    This function constructs the shutdown command and sends it to the main HVAC Teensy.
    Optionally, it can also shut off auxiliary Teensy devices (e.g., LEFT and RIGHT)
    by uncommenting the `teensyOtherOff(command)` line.

    Returns:
        None
    """
    command = "ALLOFF\n"

    # Send shutdown command to primary HVAC Teensy
    log_print("Sending Off to HVAC")
    serHVAC.write(command.encode('utf-8'))
    waitForACK(command, serHVAC)
    log_print("HVAC OFF")
    
    log_print("Sending Off to LEFT")
    serLEFT.write(command.encode('utf-8'))
    waitForACK(command, serLEFT)
    log_print("LEFT OFF")
    
    log_print("Sending Off to RIGHT")
    serRIGHT.write(command.encode('utf-8'))
    waitForACK(command, serRIGHT)
    log_print("RIGHT OFF")

def waitForACK(command, ser):
    """
    Waits for an acknowledgment (ACK) from the Teensy over serial after sending a command.
    Prints all received lines until ACK or UKN is received.
    """
    max_retries = 3
    retries = 0
    timeout_counter = 0
    max_timeout = 50  # 5 seconds total timeout (50 * 0.1)

    ser.reset_input_buffer()  # Clear any previous unread serial data

    while retries < max_retries and timeout_counter < max_timeout:
        if ser.in_waiting:
            line = ser.readline().decode(errors='ignore').strip()
            print(f"<< {line}")
            
            # Check if the response contains "ACK" (including device-specific ACKs)
            if "ACK" in line:
                return True  # Success
            # Check if the response contains "UKN" (including device-specific UKNs)
            elif "UKN" in line:
                print("Resending command...")
                ser.flush()
                ser.write(command.encode('utf-8'))
                retries += 1
                time.sleep(0.5)
        else:
            time.sleep(0.1)  # Short sleep if no data
            timeout_counter += 1

    if timeout_counter >= max_timeout:
        print("[ERROR] Timeout waiting for Teensy response")
    else:
        print("[ERROR] Teensy did not acknowledge command after 3 retries")

def check_connections():
    """
    Verify that all serial connections are still open and valid.
    Returns True if all connections are valid, False otherwise.
    """
    try:
        all_valid = all([serHVAC.is_open, serLEFT.is_open, serRIGHT.is_open])
        if not all_valid:
            print("[WARNING] One or more serial connections have been closed!")
            # Try to identify which connections are closed
            if not serHVAC.is_open:
                print("[WARNING] TeensyHVAC connection is closed")
            if not serLEFT.is_open:
                print("[WARNING] TeensyLeft connection is closed")
            if not serRIGHT.is_open:
                print("[WARNING] TeensyRight connection is closed")
        return all_valid
    except Exception as e:
        print(f"[ERROR] Error checking serial connections: {e}")
        return False

def reconnect_serial_devices():
    """
    Attempt to reconnect to any closed serial devices.
    """
    global serHVAC, serLEFT, serRIGHT
    
    # Get configuration
    teensy_configs = {device["name"]: device for device in config["serial_ports"]}
    
    try:
        # Try to reconnect to TeensyHVAC if needed
        if 'serHVAC' in globals() and not serHVAC.is_open:
            hvac_config = teensy_configs["TeensyHVAC"]
            print(f"Attempting to reconnect to TeensyHVAC on {hvac_config['port']}...")
            serHVAC = serial.Serial(hvac_config["port"], hvac_config["baud_rate"], timeout=1)
            print("TeensyHVAC reconnected successfully.")
            
        # Try to reconnect to TeensyLeft if needed
        if 'serLEFT' in globals() and not serLEFT.is_open:
            left_config = teensy_configs["TeensyLeft"]
            print(f"Attempting to reconnect to TeensyLeft on {left_config['port']}...")
            serLEFT = serial.Serial(left_config["port"], left_config["baud_rate"], timeout=1)
            print("TeensyLeft reconnected successfully.")
            
        # Try to reconnect to TeensyRight if needed
        if 'serRIGHT' in globals() and not serRIGHT.is_open:
            right_config = teensy_configs["TeensyRight"]
            print(f"Attempting to reconnect to TeensyRight on {right_config['port']}...")
            serRIGHT = serial.Serial(right_config["port"], right_config["baud_rate"], timeout=1)
            print("TeensyRight reconnected successfully.")
            
    except serial.SerialException as e:
        print(f"[ERROR] Failed to reconnect to one or more serial ports: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during reconnection: {e}")
        raise

def update_layer_info(current_idx, total_layers, layer_name="Initializing", current_step=0, total_steps=0, elapsed_time=0, remaining_time=0):
    """
    Update the current layer information file.
    
    Args:
        current_idx (int): The current layer index (1-based for display)
        total_layers (int): The total number of layers
        layer_name (str): The name of the current layer
        current_step (int): The current step within the layer (1-based for display)
        total_steps (int): The total number of steps in the current layer
        elapsed_time (int): Elapsed time in seconds for the current step
        remaining_time (int): Remaining time in seconds for the current step
    """
    try:
        with open(CURRENT_LAYER_INFO, 'w') as f:
            f.write(f"{current_idx},{total_layers},{layer_name},{current_step},{total_steps},{elapsed_time},{remaining_time}")
    except Exception as e:
        print(f"Error updating layer info: {e}")

def clear_layer_triggers():
    """Remove any existing layer and step navigation trigger files."""
    try:
        if os.path.exists(NEXT_LAYER_TRIGGER):
            os.remove(NEXT_LAYER_TRIGGER)
        if os.path.exists(PREV_LAYER_TRIGGER):
            os.remove(PREV_LAYER_TRIGGER)
        if os.path.exists(JUMP_TO_LAYER_TRIGGER):
            os.remove(JUMP_TO_LAYER_TRIGGER)
        if os.path.exists(NEXT_STEP_TRIGGER):
            os.remove(NEXT_STEP_TRIGGER)
        if os.path.exists(PREV_STEP_TRIGGER):
            os.remove(PREV_STEP_TRIGGER)
    except Exception as e:
        print(f"Error clearing navigation triggers: {e}")

def check_layer_triggers():
    """Check if any layer navigation triggers exist and clear them if found."""
    next_trigger = os.path.exists(NEXT_LAYER_TRIGGER)
    prev_trigger = os.path.exists(PREV_LAYER_TRIGGER)
    jump_trigger = os.path.exists(JUMP_TO_LAYER_TRIGGER)
    next_step_trigger = os.path.exists(NEXT_STEP_TRIGGER)
    prev_step_trigger = os.path.exists(PREV_STEP_TRIGGER)
    
    if next_trigger or prev_trigger or jump_trigger or next_step_trigger or prev_step_trigger:
        clear_layer_triggers()
        return True
    return False

def check_layer_navigation(current_idx, total_layers):
    """
    Check if layer navigation has been requested and return the new layer index.
    
    Args:
        current_idx (int): The current layer index (0-based)
        total_layers (int): The total number of layers
        
    Returns:
        int: The new layer index (0-based)
    """
    if os.path.exists(NEXT_LAYER_TRIGGER):
        os.remove(NEXT_LAYER_TRIGGER)
        if current_idx < total_layers - 1:
            print(f"\nAdvancing to next layer (Layer {current_idx + 2})...")
            return current_idx + 1
    
    if os.path.exists(PREV_LAYER_TRIGGER):
        os.remove(PREV_LAYER_TRIGGER)
        if current_idx > 0:
            print(f"\nGoing back to previous layer (Layer {current_idx})...")
            return current_idx - 1
            
    if os.path.exists(JUMP_TO_LAYER_TRIGGER):
        try:
            with open(JUMP_TO_LAYER_TRIGGER, 'r') as f:
                target_layer = int(f.read().strip())
                
            os.remove(JUMP_TO_LAYER_TRIGGER)
            
            # Convert from 1-based (UI) to 0-based (internal)
            target_idx = target_layer - 1
            
            # Validate the target index
            if target_idx >= 0 and target_idx < total_layers:
                print(f"\nJumping to layer {target_layer}...")
                return target_idx
            else:
                print(f"\nInvalid target layer: {target_layer}. Must be between 1 and {total_layers}.")
        except Exception as e:
            print(f"Error processing jump to layer: {e}")
            os.remove(JUMP_TO_LAYER_TRIGGER)
    
    return current_idx

def check_step_navigation(current_step_idx, total_steps):
    """
    Check if step navigation has been requested and return the new step index.
    
    Args:
        current_step_idx (int): The current step index (0-based)
        total_steps (int): The total number of steps in the current layer
        
    Returns:
        tuple: (step_changed, new_step_idx)
            step_changed (bool): True if step navigation was requested
            new_step_idx (int): The new step index (0-based)
    """
    if os.path.exists(NEXT_STEP_TRIGGER):
        os.remove(NEXT_STEP_TRIGGER)
        if current_step_idx < total_steps - 1:
            print(f"\nAdvancing to next step (Step {current_step_idx + 2})...")
            return True, current_step_idx + 1
    
    if os.path.exists(PREV_STEP_TRIGGER):
        os.remove(PREV_STEP_TRIGGER)
        if current_step_idx > 0:
            print(f"\nGoing back to previous step (Step {current_step_idx})...")
            return True, current_step_idx - 1
    
    return False, current_step_idx

def run_shelling():
    """
    Executes the shelling process layer by layer, sending HVAC commands at each step.

    This function:
    - Iterates through predefined shell layers and time segments.
    - Sends HVAC control data via serial.
    - Monitors pause and emergency stop (E-Stop) GPIO inputs.
    - Waits for user input to proceed to the next layer.
    - Safely shuts down on E-Stop, manual interrupt, or end of process.

    Controls:
        - E-Stop button (active LOW): Immediately aborts the process.
        - Pause button (active LOW): Toggles pause/resume.
        - Next button (active LOW): Advances to the next shell layer.

    Returns:
        None
    """
    paused = False
    current_layer_idx = 0
    total_layers = len(name)
    
    # Initialize layer info file
    update_layer_info(current_layer_idx, total_layers)
    
    # Remove any existing trigger files
    clear_layer_triggers()

    try:
        while current_layer_idx < total_layers:
            layer_name = name[current_layer_idx]
            total_steps = len(duration[current_layer_idx])
            
            # Print layer header
            log_print("\n" + "=" * 50)
            log_print(f"STARTING LAYER {current_layer_idx + 1}/{total_layers}: {layer_name}")
            log_print(f"DEBUG: current_layer_idx={current_layer_idx}, total_layers={total_layers}, total_steps={total_steps}")
            log_print("=" * 50)
            
            # Initialize layer with step 0
            update_layer_info(current_layer_idx + 1, total_layers, layer_name, 0, total_steps)
            
            # For step navigation
            current_step_idx = 0
            
            while current_step_idx < total_steps:
                # Update step information (1-based for display)
                current_step = current_step_idx + 1
                t = duration[current_layer_idx][current_step_idx]
                update_layer_info(current_layer_idx + 1, total_layers, layer_name, current_step, total_steps, 0, 0)
                
                # Print step header
                log_print("\n" + "-" * 40)
                log_print(f"Layer {current_layer_idx + 1}/{total_layers} ({layer_name}) - Step {current_step}/{total_steps}")
                log_print("-" * 40)
                
                total_seconds = int(t * 60)
                log_print(f"Waiting for {t} minutes ({total_seconds} seconds)...")
                
                # Send HVAC commands
                sendHVAC(current_layer_idx, current_step_idx)
                
                # Send commands to LEFT Teensy
                sendOther(current_layer_idx, current_step_idx)

                remaining = total_seconds
                start_time = time.time()
                
                while remaining > 0:
                    # Check for layer or step navigation triggers
                    if check_layer_triggers():
                        # Trigger detected, break the time segment loop
                        break
                    
                    # Check for E-Stop
                    if GPIO.input(ESTOP_PIN) == GPIO.LOW:
                        print("\nE-Stop triggered! Aborting.")
                        return
                        
                    # Check if shutdown signal received
                    if shutdown_in_progress:
                        print("\nShutdown signal received. Aborting.")
                        return

                    # Periodically check if connections are still valid
                    if remaining % 30 == 0:  # Check every 30 seconds
                        if not check_connections():
                            print("\n[ERROR] Serial connection issue detected.")
                            print("Attempting to reconnect...")
                            try:
                                # Try to reconnect to any closed connections
                                reconnect_serial_devices()
                            except Exception as e:
                                print(f"Reconnection failed: {e}")
                                print("Continuing with available connections...")

                    # Check for pause/resume toggle
                    if GPIO.input(PAUSE_PIN) == GPIO.LOW:
                        paused = not paused
                        state = "Paused" if paused else "Resumed"
                        print(f"\n[{state}] Press again to toggle.")
                        time.sleep(2)  # debounce

                    # Countdown logic
                    if not paused:
                        # Calculate elapsed and remaining time
                        elapsed_seconds = int(time.time() - start_time)
                        
                        # Update the layer info with timing data
                        update_layer_info(
                            current_layer_idx + 1,
                            total_layers,
                            layer_name,
                            current_step,
                            total_steps,
                            elapsed_seconds,
                            remaining
                        )
                        
                        log_print(f"Time left: {remaining // 60}m {remaining % 60}s", end='\r')
                        time.sleep(1)
                        remaining -= 1
                    else:
                        time.sleep(0.1)  # reduce CPU load when paused
                
                # Check if we need to skip to a different layer
                new_layer_idx = check_layer_navigation(current_layer_idx, total_layers)
                if new_layer_idx != current_layer_idx:
                    # Layer navigation requested, break out of time segment loop
                    current_layer_idx = new_layer_idx
                    break
                
                # Check if we need to move to a different step
                step_changed, new_step_idx = check_step_navigation(current_step_idx, total_steps)
                if step_changed:
                    # Step navigation requested, update step index and continue with next step
                    current_step_idx = new_step_idx
                    break
                
                # If we completed the current step normally, move to the next step
                log_print(f"\nDEBUG: Step {current_step_idx + 1} completed. Moving to step {current_step_idx + 2}")
                current_step_idx += 1
            
            # Check if layer navigation happened during time segments
            new_layer_idx = check_layer_navigation(current_layer_idx, total_layers)
            if new_layer_idx != current_layer_idx:
                current_layer_idx = new_layer_idx
                continue
            
            # Check if all steps in this layer are completed    
            if current_step_idx >= total_steps:
                # Layer completed normally, print completion message
                log_print("\n" + "=" * 50)
                log_print(f"LAYER {current_layer_idx + 1}/{total_layers} ({layer_name}) COMPLETED")
                log_print(f"DEBUG: current_step_idx={current_step_idx}, total_steps={total_steps}")
                
                if current_layer_idx < total_layers - 1:
                    next_layer_name = name[current_layer_idx + 1]
                    log_print(f"Automatically advancing to next shell layer: {next_layer_name}")
                    log_print(f"DEBUG: Advancing from layer {current_layer_idx + 1} to {current_layer_idx + 2}")
                    current_layer_idx += 1
                else:
                    log_print("This was the final layer. Entering idle state...")
                    log_print("=" * 50 + "\n")
                    
                    # Enter idle state after completing all layers
                    idle_result = run_idle_state()
                    
                    if idle_result == "restart":
                        # Restart from the beginning if layer navigation was triggered
                        current_layer_idx = 0
                        continue
                    elif idle_result in ["estop", "shutdown", "interrupt"]:
                        # Exit the main loop for these conditions
                        return idle_result
                    else:
                        # This shouldn't happen, but exit gracefully
                        return "complete"

    except KeyboardInterrupt:
        # This should rarely be triggered now that we have signal handlers,
        # but keep it as a fallback just in case
        print("\nKeyboardInterrupt received. Shutting down safely...")
        if not shutdown_in_progress:
            # Only call send_shutoff if we haven't already started shutdown
            send_shutoff()
            GPIO.cleanup()
        return "interrupt"

    # Uncomment this for an extra layer of safety during shutdown
    # Enable for production use
    finally:
        print("\nFinal shutdown cleanup...")
        try:
            send_shutoff()
        except Exception as e:
            print(f"Error sending shutdown commands: {e}")
        
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"Error cleaning up GPIO: {e}")
        
        # Close all serial connections
        try:
            if 'serHVAC' in globals() and serHVAC.is_open:
                serHVAC.close()
                print("Closed TeensyHVAC connection")
                
            if 'serLEFT' in globals() and serLEFT.is_open:
                serLEFT.close()
                print("Closed TeensyLeft connection")
                
            if 'serRIGHT' in globals() and serRIGHT.is_open:
                serRIGHT.close()
                print("Closed TeensyRight connection")
        except Exception as e:
            print(f"Error closing serial connections: {e}")
            
        print("Final cleanup complete.")
        return "complete"

def run_test_button():
    print("Waiting for Button")
    while(True):
        if GPIO.input(ESTOP_PIN) == GPIO.LOW:
                            print("\nE-Stop triggered! Aborting.")
                            break
    

# Main execution block
if __name__ == "__main__":
    ensure_single_instance()

    # Setup GPIO before anything else that may use it
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ESTOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PAUSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        log_print(f"Using config from: {CONFIG_PATH}")

        if not os.path.exists(SHELL_JSON_PATH):
            log_print(f"[ERROR] Shell JSON file not found at {SHELL_JSON_PATH}")
            sys.exit(1)

        # Load and run the shell layers in a loop to handle restarts
        log_print("Loading shell layers from shell JSON file...")
        read_shell_layers(SHELL_JSON_PATH)
        
        while True:
            log_print("Starting shelling process...")
            result = run_shelling()
            
            # If run_shelling returns, check if we need to restart or exit
            if result == "restart":
                log_print("Restarting shelling process from beginning...")
                # Reload shell layers in case they were updated
                read_shell_layers(SHELL_JSON_PATH)
                continue
            elif result in ["estop", "shutdown", "interrupt"]:
                log_print(f"Shelling process terminated: {result}")
                break
            else:
                # Normal completion
                log_print("Shelling process completed normally.")
                break

    except Exception as e:
        log_print(f"\n[ERROR] An unexpected error occurred: {e}")
        try:
            send_shutoff()
            GPIO.cleanup()
        except:
            pass
        sys.exit(1)

    finally:
        if shutdown_in_progress:
            log_print("\nReceived shutdown signal. Shutting down gracefully...")
            log_print("Finalizing shutdown process...")
            try:
                log_print("Sending ALLOFF commands to Teensy controllers...")
                send_shutoff()
                GPIO.cleanup()
            except Exception as e:
                log_print(f"Error during shutdown: {e}")
            log_print("Shutdown complete.")
        else:
            log_print("\nNormal shutdown complete.")
            try:
                send_shutoff()
                GPIO.cleanup()
            except:
                pass

        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
                log_print(f"Removed PID file: {PID_FILE}")
        except Exception as e:
            log_print(f"Error removing PID file: {e}")

def load_idle_config():
    """Load idle configuration from idleConfig.json"""
    try:
        if os.path.exists(IDLE_CONFIG_PATH):
            with open(IDLE_CONFIG_PATH, 'r') as f:
                idle_config = json.load(f)
                log_print(f"Loaded idle configuration from {IDLE_CONFIG_PATH}")
                return idle_config
        else:
            # Default idle configuration
            default_config = {
                "ambient_temperature": 26,  # Celsius
                "shell_temperature": 0,     # Celsius
                "humidity": 0,              # %
                "shell_speed": 0,           # RPM
                "fan_speed": 0              # CFM
            }
            log_print("Using default idle configuration (no idle config file found)")
            return default_config
    except Exception as e:
        log_print(f"Error loading idle configuration: {e}")
        # Return default configuration on error
        return {
            "ambient_temperature": 26,
            "shell_temperature": 0,
            "humidity": 0,
            "shell_speed": 0,
            "fan_speed": 0
        }

def send_idle_commands(idle_config):
    """Send idle state commands to all Teensy devices"""
    try:
        # Build command string for idle state using START format with a very long time (999999 minutes for continuous operation)
        idle_command = (
            f"START-ATEMP:{idle_config['ambient_temperature']},"
            f"STEMP:{idle_config['shell_temperature']},"
            f"HUM:{idle_config['humidity']},"
            f"TIME:999999,"  # Very long time to indicate continuous idle operation
            f"OMEGA:{idle_config['shell_speed']},"
            f"FAN:{idle_config['fan_speed']},"
            f"DST:{deltaShellTemperature},"
            f"DAT:{deltaAirTemperature},"
            f"DH:{deltaHumidity},"
            f"DSFA:{deltaShellFanAirflow}\n"
        )
        
        # Send to HVAC Teensy
        log_print(f"[Pi → TeensyHVAC] {idle_command.strip()}")
        serHVAC.flush()
        serHVAC.write(idle_command.encode('utf-8'))
        serHVAC.flush()
        waitForACK(idle_command, serHVAC)
        
        # Build command for LEFT/RIGHT Teensys (without OMEGA parameter)
        idle_command_sides = (
            f"START-ATEMP:{idle_config['ambient_temperature']},"
            f"STEMP:{idle_config['shell_temperature']},"
            f"HUM:{idle_config['humidity']},"
            f"TIME:999999,"  # Very long time to indicate continuous idle operation
            f"FAN:{idle_config['fan_speed']},"
            f"DST:{deltaShellTemperature},"
            f"DAT:{deltaAirTemperature},"
            f"DH:{deltaHumidity},"
            f"DSFA:{deltaShellFanAirflow}\n"
        )
        
        # Send to LEFT Teensy
        log_print(f"[Pi → TeensyLeft] {idle_command_sides.strip()}")
        serLEFT.flush()
        serLEFT.write(idle_command_sides.encode('utf-8'))
        serLEFT.flush()
        waitForACK(idle_command_sides, serLEFT)
        
        # Send to RIGHT Teensy if both sides are active
        if sidesOn == 2:
            log_print(f"[Pi → TeensyRight] {idle_command_sides.strip()}")
            serRIGHT.flush()
            serRIGHT.write(idle_command_sides.encode('utf-8'))
            serRIGHT.flush()
            waitForACK(idle_command_sides, serRIGHT)
        
        log_print("Idle state commands sent to all Teensy devices")
        
    except Exception as e:
        log_print(f"Error sending idle commands: {e}")

def run_idle_state():
    """Run the system in idle state after all layers are completed"""
    log_print("\n" + "=" * 50)
    log_print("ENTERING IDLE STATE")
    log_print("All shell layers completed. System will maintain idle conditions.")
    log_print("=" * 50)
    
    # Load idle configuration
    idle_config = load_idle_config()
    
    # Log idle configuration
    log_print("Idle Configuration:")
    log_print(f"  Ambient Temperature: {idle_config['ambient_temperature']}°C")
    log_print(f"  Shell Temperature: {idle_config['shell_temperature']}°C")
    log_print(f"  Humidity: {idle_config['humidity']}%")
    log_print(f"  Shell Speed: {idle_config['shell_speed']} RPM")
    log_print(f"  Fan Speed: {idle_config['fan_speed']} CFM")
    
    # Update layer info to show idle state
    update_layer_info(0, 0, "IDLE", 0, 0, 0, 0)
    
    # Send idle commands to all Teensy devices
    send_idle_commands(idle_config)
    
    # Enter idle monitoring loop
    paused = False
    idle_start_time = time.time()
    
    try:
        while True:
            # Check for layer navigation triggers (to restart layers if needed)
            if check_layer_triggers():
                log_print("Layer navigation triggered during idle state. Restarting shell process...")
                return "restart"
            
            # Check for E-Stop
            if GPIO.input(ESTOP_PIN) == GPIO.LOW:
                log_print("E-Stop triggered during idle state! Shutting down.")
                return "estop"
            
            # Check if shutdown signal received
            if shutdown_in_progress:
                log_print("Shutdown signal received during idle state.")
                return "shutdown"
            
            # Check for pause/resume toggle
            if GPIO.input(PAUSE_PIN) == GPIO.LOW:
                paused = not paused
                state = "Paused" if paused else "Resumed"
                log_print(f"Idle state {state}")
                time.sleep(2)  # debounce
            
            # Periodically check connections and resend idle commands
            current_time = time.time()
            if int(current_time - idle_start_time) % 300 == 0:  # Every 5 minutes
                # Reload idle configuration in case it was updated
                idle_config = load_idle_config()
                
                if not check_connections():
                    log_print("Serial connection issue detected during idle state.")
                    try:
                        reconnect_serial_devices()
                        send_idle_commands(idle_config)
                    except Exception as e:
                        log_print(f"Reconnection during idle failed: {e}")
                else:
                    # Resend idle commands periodically to maintain state
                    send_idle_commands(idle_config)
                    log_print("Idle state commands refreshed")
            
            # Check for idle configuration updates every 30 seconds
            elif int(current_time - idle_start_time) % 30 == 0:
                # Check if idle config file has been modified
                try:
                    if os.path.exists(IDLE_CONFIG_PATH):
                        file_mtime = os.path.getmtime(IDLE_CONFIG_PATH)
                        if not hasattr(run_idle_state, 'last_config_mtime'):
                            run_idle_state.last_config_mtime = file_mtime
                        elif file_mtime > run_idle_state.last_config_mtime:
                            log_print("Idle configuration updated. Reloading...")
                            idle_config = load_idle_config()
                            send_idle_commands(idle_config)
                            run_idle_state.last_config_mtime = file_mtime
                except Exception as e:
                    log_print(f"Error checking idle config updates: {e}")
            
            # Update idle state timing
            elapsed_idle_time = int(current_time - idle_start_time)
            update_layer_info(0, 0, "IDLE", 0, 0, elapsed_idle_time, 0)
            
            if not paused:
                time.sleep(1)
            else:
                time.sleep(0.1)  # reduce CPU load when paused
                
    except KeyboardInterrupt:
        log_print("KeyboardInterrupt received during idle state.")
        return "interrupt"
