#!/usr/bin/env python3
"""
Development DryBox Web Control Interface

A Flask web server that provides a web interface to start and stop a simulated DryBox system.
This development version creates mock processes and data for testing without requiring actual hardware.
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import subprocess
import os
import time
import threading
import datetime
import json
import shutil
import jsonschema
import glob
import multiprocessing
import signal
import random

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Define paths dynamically based on script location
# Get the directory where this script is located (Python folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get RPI5 directory
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, "DataLogging", "dev")
JSON_DIR = os.path.join(BASE_DIR, "JSONS", "dev")
SCRIPTS_DIR = os.path.join(BASE_DIR, "Scripts")

# Create development directories
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# Define paths for scripts (development versions will be created)
START_SCRIPT = os.path.join(SCRIPTS_DIR, "dev_start_drybox.sh")
STOP_SCRIPT = os.path.join(SCRIPTS_DIR, "dev_stop_drybox.sh")
FLASH_SCRIPT = os.path.join(SCRIPTS_DIR, "dev_flash_teensy.sh")

# Define paths for log files (development versions)
STARTUP_LOG = os.path.join(LOG_DIR, "drybox_startup.log")
SHUTDOWN_LOG = os.path.join(LOG_DIR, "drybox_shutdown.log")
JSONPARSE_LOG = os.path.join(LOG_DIR, "jsonParse.log")
SERIALDEBUG_LOG = os.path.join(LOG_DIR, "serialDebug.log")
FLASH_LOG = os.path.join(LOG_DIR, "teensy_flash.log")
CURRENT_LAYER_INFO = os.path.join(LOG_DIR, "current_layer.txt")
NEXT_LAYER_TRIGGER = os.path.join(LOG_DIR, "next_layer.trigger")
PREV_LAYER_TRIGGER = os.path.join(LOG_DIR, "prev_layer.trigger")
JUMP_TO_LAYER_TRIGGER = os.path.join(LOG_DIR, "jump_to_layer.trigger")
NEXT_STEP_TRIGGER = os.path.join(LOG_DIR, "next_step.trigger")
PREV_STEP_TRIGGER = os.path.join(LOG_DIR, "prev_step.trigger")

# Define path for development shellJson.json
SHELL_JSON = os.path.join(JSON_DIR, "shellJson.json")
SCHEMA_FILE = os.path.join(JSON_DIR, "schema")
IDLE_CONFIG_PATH = os.path.join(JSON_DIR, "idleConfig.json")

# Global variables to track system state
system_running = False
last_action = None
last_action_time = None

# Development mock processes
mock_processes = {}
mock_threads = {}

def create_mock_shell_json():
    """Create a mock shellJson.json for development."""
    mock_shell_data = {
        "layers": [
            {
                "name": "Layer 1 - Initial Setup",
                "duration": 3600,
                "steps": [
                    {"name": "Heat Up", "duration": 600, "temperature": 25.0, "humidity": 45},
                    {"name": "Stabilize", "duration": 1800, "temperature": 26.0, "humidity": 40},
                    {"name": "Process", "duration": 1200, "temperature": 27.0, "humidity": 35}
                ]
            },
            {
                "name": "Layer 2 - Main Process",
                "duration": 7200,
                "steps": [
                    {"name": "Prepare", "duration": 300, "temperature": 27.0, "humidity": 35},
                    {"name": "Execute", "duration": 6600, "temperature": 28.0, "humidity": 30},
                    {"name": "Cool Down", "duration": 300, "temperature": 26.0, "humidity": 35}
                ]
            },
            {
                "name": "Layer 3 - Finalization",
                "duration": 1800,
                "steps": [
                    {"name": "Final Process", "duration": 1200, "temperature": 25.0, "humidity": 40},
                    {"name": "Complete", "duration": 600, "temperature": 24.0, "humidity": 45}
                ]
            }
        ]
    }
    
    with open(SHELL_JSON, 'w') as f:
        json.dump(mock_shell_data, f, indent=2)

def create_mock_idle_config():
    """Create a mock idle configuration for development."""
    mock_idle_config = {
        "ambient_temperature": 26,
        "shell_temperature": 0,
        "humidity": 0,
        "shell_speed": 0,
        "fan_speed": 0
    }
    
    with open(IDLE_CONFIG_PATH, 'w') as f:
        json.dump(mock_idle_config, f, indent=2)

def mock_jsonparse_process():
    """Mock JSONparse.py process that simulates layer progression."""
    current_layer = 1
    total_layers = 3
    current_step = 1
    total_steps = 3
    layer_name = "Layer 1 - Initial Setup"
    start_time = time.time()
    
    with open(JSONPARSE_LOG, 'w') as log_file:
        log_file.write(f"[{datetime.datetime.now()}] Mock JSONparse started\n")
        log_file.flush()
        
        while True:
            try:
                # Check for trigger files
                if os.path.exists(NEXT_LAYER_TRIGGER):
                    current_layer = min(current_layer + 1, total_layers)
                    current_step = 1
                    layer_name = f"Layer {current_layer} - {'Initial Setup' if current_layer == 1 else 'Main Process' if current_layer == 2 else 'Finalization'}"
                    os.remove(NEXT_LAYER_TRIGGER)
                    log_file.write(f"[{datetime.datetime.now()}] Advanced to layer {current_layer}\n")
                    log_file.flush()
                
                if os.path.exists(PREV_LAYER_TRIGGER):
                    current_layer = max(current_layer - 1, 1)
                    current_step = 1
                    layer_name = f"Layer {current_layer} - {'Initial Setup' if current_layer == 1 else 'Main Process' if current_layer == 2 else 'Finalization'}"
                    os.remove(PREV_LAYER_TRIGGER)
                    log_file.write(f"[{datetime.datetime.now()}] Moved back to layer {current_layer}\n")
                    log_file.flush()
                
                if os.path.exists(JUMP_TO_LAYER_TRIGGER):
                    with open(JUMP_TO_LAYER_TRIGGER, 'r') as f:
                        target_layer = int(f.read().strip())
                    current_layer = max(1, min(target_layer, total_layers))
                    current_step = 1
                    layer_name = f"Layer {current_layer} - {'Initial Setup' if current_layer == 1 else 'Main Process' if current_layer == 2 else 'Finalization'}"
                    os.remove(JUMP_TO_LAYER_TRIGGER)
                    log_file.write(f"[{datetime.datetime.now()}] Jumped to layer {current_layer}\n")
                    log_file.flush()
                
                if os.path.exists(NEXT_STEP_TRIGGER):
                    current_step = min(current_step + 1, total_steps)
                    os.remove(NEXT_STEP_TRIGGER)
                    log_file.write(f"[{datetime.datetime.now()}] Advanced to step {current_step}\n")
                    log_file.flush()
                
                if os.path.exists(PREV_STEP_TRIGGER):
                    current_step = max(current_step - 1, 1)
                    os.remove(PREV_STEP_TRIGGER)
                    log_file.write(f"[{datetime.datetime.now()}] Moved back to step {current_step}\n")
                    log_file.flush()
                
                # Update current layer info
                elapsed_time = int(time.time() - start_time)
                remaining_time = max(0, 7200 - elapsed_time)  # Mock 2-hour total process
                
                with open(CURRENT_LAYER_INFO, 'w') as f:
                    f.write(f"{current_layer},{total_layers},{layer_name},{current_step},{total_steps},{elapsed_time},{remaining_time}")
                
                # Simulate temperature and sensor data
                temp = 25.0 + random.uniform(-1.0, 1.0)
                humidity = 40 + random.uniform(-5, 5)
                log_file.write(f"[{datetime.datetime.now()}] Temperature: {temp:.1f}°C, Humidity: {humidity:.1f}%\n")
                log_file.flush()
                
                time.sleep(5)
                
            except Exception as e:
                log_file.write(f"[{datetime.datetime.now()}] Error in mock JSONparse: {e}\n")
                log_file.flush()
                break

def mock_serialdebug_process():
    """Mock serialDebug.py process that simulates serial communication."""
    with open(SERIALDEBUG_LOG, 'w') as log_file:
        log_file.write(f"[{datetime.datetime.now()}] Mock SerialDebug started\n")
        log_file.flush()
        
        while True:
            try:
                # Simulate receiving data from Teensy controllers
                teensy_data = [
                    f"TeensyHVAC: Temp={25.0 + random.uniform(-2, 2):.1f}, Fan={random.randint(0, 100)}%",
                    f"TeensyLeft: Position={random.randint(0, 1000)}, Speed={random.randint(0, 50)}",
                    f"TeensyRight: Sensor={random.randint(500, 1500)}, Status=OK"
                ]
                
                for data in teensy_data:
                    log_file.write(f"[{datetime.datetime.now()}] {data}\n")
                
                log_file.flush()
                time.sleep(3)
                
            except Exception as e:
                log_file.write(f"[{datetime.datetime.now()}] Error in mock SerialDebug: {e}\n")
                log_file.flush()
                break

def mock_logdb_process():
    """Mock logDB.py process that simulates database logging."""
    with open(os.path.join(LOG_DIR, "logDB.log"), 'w') as log_file:
        log_file.write(f"[{datetime.datetime.now()}] Mock LogDB started\n")
        log_file.flush()
        
        while True:
            try:
                # Simulate database operations
                log_file.write(f"[{datetime.datetime.now()}] Logged sensor data to database\n")
                log_file.write(f"[{datetime.datetime.now()}] Database connection OK\n")
                log_file.flush()
                time.sleep(10)
                
            except Exception as e:
                log_file.write(f"[{datetime.datetime.now()}] Error in mock LogDB: {e}\n")
                log_file.flush()
                break

def check_system_status():
    """Check if the mock DryBox system is running."""
    return len(mock_processes) > 0 and all(p.is_alive() for p in mock_processes.values())

def update_system_state():
    """Update the global system state variables."""
    global system_running
    system_running = check_system_status()

def create_development_scripts():
    """Create development versions of the shell scripts."""
    # Create development start script
    start_script_content = f'''#!/bin/bash
# Development startup script for DryBox system
echo "----------------------------------------------" >> "{STARTUP_LOG}"
echo "Starting Development DryBox system at $(date)" >> "{STARTUP_LOG}"
echo "----------------------------------------------" >> "{STARTUP_LOG}"
echo "Mock processes will be started by Python web control" >> "{STARTUP_LOG}"
echo "Development mode - no actual hardware required" >> "{STARTUP_LOG}"
'''
    
    with open(START_SCRIPT, 'w') as f:
        f.write(start_script_content)
    
    # Create development stop script
    stop_script_content = f'''#!/bin/bash
# Development stop script for DryBox system
echo "----------------------------------------------" >> "{SHUTDOWN_LOG}"
echo "Stopping Development DryBox system at $(date)" >> "{SHUTDOWN_LOG}"
echo "----------------------------------------------" >> "{SHUTDOWN_LOG}"
echo "Mock processes will be stopped by Python web control" >> "{SHUTDOWN_LOG}"
'''
    
    with open(STOP_SCRIPT, 'w') as f:
        f.write(stop_script_content)
    
    # Create development flash script
    flash_script_content = f'''#!/bin/bash
# Development flash script for Teensy controllers
TARGET=${{1:-all}}
echo "----------------------------------------------" >> "{FLASH_LOG}"
echo "Mock flashing Teensy $TARGET at $(date)" >> "{FLASH_LOG}"
echo "----------------------------------------------" >> "{FLASH_LOG}"
echo "Development mode - simulating flash operation" >> "{FLASH_LOG}"
sleep 2
echo "Flash operation completed successfully" >> "{FLASH_LOG}"
'''
    
    with open(FLASH_SCRIPT, 'w') as f:
        f.write(flash_script_content)

# Initialize development environment
def initialize_dev_environment():
    """Initialize the development environment with mock data and scripts."""
    create_development_scripts()
    create_mock_shell_json()
    create_mock_idle_config()
    
    # Create initial log files
    for log_file in [STARTUP_LOG, SHUTDOWN_LOG, JSONPARSE_LOG, SERIALDEBUG_LOG, FLASH_LOG]:
        with open(log_file, 'w') as f:
            f.write(f"Development DryBox Control - Log initialized at {datetime.datetime.now()}\n")

# Initialize on startup
initialize_dev_environment()
update_system_state()

def get_log_content(log_path, num_lines=50):
    """Read the last n lines from a log file."""
    if not os.path.exists(log_path):
        return "Log file not found."
    
    try:
        # Use Python's approach since we're on Windows
        with open(log_path, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-num_lines:]) if lines else "Log file is empty."
    except Exception as e:
        return f"Error reading log file: {e}"

@app.route('/')
def index():
    """Render the main web interface."""
    update_system_state()
    
    # Get log file content (last 50 lines)
    startup_log = get_log_content(STARTUP_LOG, 50)
    shutdown_log = get_log_content(SHUTDOWN_LOG, 50)
    jsonparse_log = get_log_content(JSONPARSE_LOG, 50)
    serialdebug_log = get_log_content(SERIALDEBUG_LOG, 50)
    
    return render_template('index.html', 
                          system_running=system_running,
                          last_action=last_action,
                          last_action_time=last_action_time,
                          startup_log=startup_log,
                          shutdown_log=shutdown_log,
                          jsonparse_log=jsonparse_log,
                          serialdebug_log=serialdebug_log)

@app.route('/debug')
def debug():
    """Render the debug panel interface."""
    update_system_state()
    
    # Get log file content (last 50 lines) for initial display
    startup_log = get_log_content(STARTUP_LOG, 50)
    shutdown_log = get_log_content(SHUTDOWN_LOG, 50)
    jsonparse_log = get_log_content(JSONPARSE_LOG, 50)
    serialdebug_log = get_log_content(SERIALDEBUG_LOG, 50)
    flash_log = get_log_content(FLASH_LOG, 50)
    
    return render_template('debug.html', 
                          system_running=system_running,
                          startup_log=startup_log,
                          shutdown_log=shutdown_log,
                          jsonparse_log=jsonparse_log,
                          serialdebug_log=serialdebug_log,
                          flash_log=flash_log)

@app.route('/api/start', methods=['POST'])
def start_system():
    """API endpoint to start the mock DryBox system."""
    global last_action, last_action_time, system_running, mock_processes
    
    if system_running:
        return jsonify({"status": "error", "message": "System is already running"})
    
    try:
        # Start mock processes
        mock_processes['jsonparse'] = multiprocessing.Process(target=mock_jsonparse_process)
        mock_processes['serialdebug'] = multiprocessing.Process(target=mock_serialdebug_process)
        mock_processes['logdb'] = multiprocessing.Process(target=mock_logdb_process)
        
        for name, process in mock_processes.items():
            process.start()
            with open(STARTUP_LOG, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] Started mock {name} process (PID: {process.pid})\n")
        
        # Update status
        time.sleep(1)  # Give processes time to start
        update_system_state()
        
        last_action = "start"
        last_action_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "status": "success", 
            "message": "Development DryBox system started successfully",
            "output": "Mock processes started",
            "system_running": system_running
        })
    
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error starting Development DryBox system: {str(e)}",
            "system_running": check_system_status()
        })

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """API endpoint to stop the mock DryBox system."""
    global last_action, last_action_time, system_running, mock_processes
    
    if not system_running:
        return jsonify({"status": "error", "message": "System is not running"})
    
    try:
        # Stop mock processes
        for name, process in mock_processes.items():
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                with open(SHUTDOWN_LOG, 'a') as f:
                    f.write(f"[{datetime.datetime.now()}] Stopped mock {name} process\n")
        
        mock_processes.clear()
        
        # Update status
        update_system_state()
        
        last_action = "stop"
        last_action_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "status": "success", 
            "message": "Development DryBox system stopped successfully",
            "output": "Mock processes stopped",
            "system_running": system_running
        })
    
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error stopping Development DryBox system: {str(e)}",
            "system_running": check_system_status()
        })

@app.route('/api/status')
def get_status():
    """API endpoint to get the current system status."""
    update_system_state()
    return jsonify({
        "system_running": system_running,
        "last_action": last_action,
        "last_action_time": last_action_time
    })

@app.route('/api/logs/<log_type>')
def get_logs(log_type):
    """API endpoint to get log file content."""
    num_lines = request.args.get('lines', 50, type=int)
    
    if log_type == 'startup':
        log_content = get_log_content(STARTUP_LOG, num_lines)
    elif log_type == 'shutdown':
        log_content = get_log_content(SHUTDOWN_LOG, num_lines)
    elif log_type == 'jsonparse':
        log_content = get_log_content(JSONPARSE_LOG, num_lines)
    elif log_type == 'serialdebug':
        log_content = get_log_content(SERIALDEBUG_LOG, num_lines)
    elif log_type == 'flash':
        log_content = get_log_content(FLASH_LOG, num_lines)
    else:
        return jsonify({"status": "error", "message": "Invalid log type"})
    
    return jsonify({
        "status": "success",
        "content": log_content
    })

@app.route('/api/flash', methods=['POST'])
def flash_teensy():
    """API endpoint to simulate flashing Teensy microcontrollers."""
    target = request.json.get('target', 'all')
    
    # Check if target is valid
    valid_targets = ['TeensyHVAC', 'TeensyLeft', 'TeensyRight', 'all']
    if target not in valid_targets:
        return jsonify({
            "status": "error",
            "message": f"Invalid target: {target}. Valid targets are: {', '.join(valid_targets)}"
        })
    
    try:
        # Simulate flash operation
        def run_mock_flash():
            with open(FLASH_LOG, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] Starting flash operation for {target}\n")
                f.write(f"[{datetime.datetime.now()}] Compiling firmware...\n")
                time.sleep(2)
                f.write(f"[{datetime.datetime.now()}] Uploading to {target}...\n")
                time.sleep(3)
                f.write(f"[{datetime.datetime.now()}] Flash operation completed successfully\n")
        
        threading.Thread(target=run_mock_flash).start()
        
        return jsonify({
            "status": "success",
            "message": f"Mock flash operation started for {target}. Check flash log for progress."
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error in mock flash operation: {str(e)}"
        })

@app.route('/stream_flash_log')
def stream_flash_log():
    """Stream flash log file content in real-time."""
    def generate():
        if not os.path.exists(FLASH_LOG):
            yield "Flash log file not found. It will be created when you start a flash operation.\n"
            return
        
        # First yield the existing content
        try:
            with open(FLASH_LOG, 'r') as f:
                content = f.read()
                yield content
                
                # Then continue to yield new content as it's added
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    yield line
        except Exception as e:
            yield f"Error reading flash log: {e}\n"
    
    return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route('/stream_log/<log_type>')
def stream_log(log_type):
    """Stream log file content in real-time."""
    if log_type == 'startup':
        log_path = STARTUP_LOG
    elif log_type == 'shutdown':
        log_path = SHUTDOWN_LOG
    elif log_type == 'jsonparse':
        log_path = JSONPARSE_LOG
    elif log_type == 'serialdebug':
        log_path = SERIALDEBUG_LOG
    else:
        return "Invalid log type", 400
    
    def generate():
        if not os.path.exists(log_path):
            yield "Log file not found.\n"
            return
        
        # First yield the existing content
        try:
            with open(log_path, 'r') as f:
                content = f.read()
                yield content
                
                # Then continue to yield new content as it's added
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    yield line
        except Exception as e:
            yield f"Error reading log: {e}\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/api/upload_shell_json', methods=['POST'])
def upload_shell_json():
    """API endpoint to upload a new shellJson.json file."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})
    
    try:
        # Read the uploaded file content
        file_content = file.read().decode('utf-8')
        
        # Validate JSON format
        try:
            json_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            return jsonify({
                "status": "error", 
                "message": f"Invalid JSON format: {str(e)}"
            })
        
        # Create backup of existing file
        if os.path.exists(SHELL_JSON):
            backup_path = f"{SHELL_JSON}.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(SHELL_JSON, backup_path)
        
        # Write the new JSON file
        with open(SHELL_JSON, 'w') as f:
            f.write(file_content)
        
        # Log the action
        global last_action, last_action_time
        last_action = "upload_shell_json"
        last_action_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        restart_needed = system_running
        restart_message = ""
        
        if restart_needed:
            restart_message = " You may need to restart the DryBox system for changes to take effect."
        
        return jsonify({
            "status": "success", 
            "message": f"Development shellJson.json uploaded successfully.{restart_message}",
            "restart_needed": restart_needed
        })
    
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error uploading shellJson.json: {str(e)}"
        })

@app.route('/api/get_shell_json')
def get_shell_json():
    """API endpoint to get the current shellJson.json file content."""
    try:
        if not os.path.exists(SHELL_JSON):
            return jsonify({
                "status": "error",
                "message": "shellJson.json file not found"
            })
        
        with open(SHELL_JSON, 'r') as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "content": content
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error reading shellJson.json: {str(e)}"
        })

@app.route('/api/get_current_layer')
def get_current_layer():
    """API endpoint to get the current active shell layer."""
    try:
        layer_info_file = CURRENT_LAYER_INFO
        
        if not os.path.exists(layer_info_file):
            return jsonify({
                "status": "error",
                "message": "Layer information not available",
                "current_layer": 0,
                "total_layers": 0,
                "layer_name": "Unknown",
                "current_step": 0,
                "total_steps": 0,
                "elapsed_time": 0,
                "remaining_time": 0
            })
        
        with open(layer_info_file, 'r') as f:
            content = f.read().strip().split(',')
            if len(content) >= 5:
                current_layer = int(content[0])
                total_layers = int(content[1])
                layer_name = content[2]
                current_step = int(content[3])
                total_steps = int(content[4])
                
                elapsed_time = 0
                remaining_time = 0
                if len(content) >= 7:
                    try:
                        elapsed_time = int(content[5])
                        remaining_time = int(content[6])
                    except (ValueError, IndexError):
                        pass
                
                return jsonify({
                    "status": "success",
                    "current_layer": current_layer,
                    "total_layers": total_layers,
                    "layer_name": layer_name,
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "elapsed_time": elapsed_time,
                    "remaining_time": remaining_time
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid layer information format",
                    "current_layer": 0,
                    "total_layers": 0,
                    "layer_name": "Unknown",
                    "current_step": 0,
                    "total_steps": 0,
                    "elapsed_time": 0,
                    "remaining_time": 0
                })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting current layer: {str(e)}",
            "current_layer": 0,
            "total_layers": 0,
            "layer_name": "Unknown",
            "current_step": 0,
            "total_steps": 0,
            "elapsed_time": 0,
            "remaining_time": 0
        })

@app.route('/api/next_layer', methods=['POST'])
def next_layer():
    """API endpoint to advance to the next shell layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        with open(NEXT_LAYER_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Next layer command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error advancing to next layer: {str(e)}"
        })

@app.route('/api/prev_layer', methods=['POST'])
def prev_layer():
    """API endpoint to go back to the previous shell layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        with open(PREV_LAYER_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Previous layer command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error going to previous layer: {str(e)}"
        })

@app.route('/api/jump_to_layer', methods=['POST'])
def jump_to_layer():
    """API endpoint to jump to a specific shell layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        target_layer = request.json.get('target_layer', 1)
        
        if not isinstance(target_layer, int) or target_layer < 1:
            return jsonify({
                "status": "error",
                "message": "Invalid target layer. Must be a positive integer."
            })
        
        with open(JUMP_TO_LAYER_TRIGGER, 'w') as f:
            f.write(str(target_layer))
        
        return jsonify({
            "status": "success",
            "message": f"Jump to layer {target_layer} command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error jumping to layer: {str(e)}"
        })

@app.route('/api/next_step', methods=['POST'])
def next_step():
    """API endpoint to advance to the next step within the current layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        with open(NEXT_STEP_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Next step command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error advancing to next step: {str(e)}"
        })

@app.route('/api/prev_step', methods=['POST'])
def prev_step():
    """API endpoint to go back to the previous step within the current layer."""
    if not system_running:
        return jsonify({
            "status": "error",
            "message": "DryBox system is not running"
        })
    
    try:
        with open(PREV_STEP_TRIGGER, 'w') as f:
            f.write(str(datetime.datetime.now()))
        
        return jsonify({
            "status": "success",
            "message": "Previous step command sent"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error going to previous step: {str(e)}"
        })

@app.route('/api/set_idle_config', methods=['POST'])
def set_idle_config():
    """API endpoint to configure idle state parameters after layers complete."""
    try:
        idle_config = request.json
        
        required_fields = ['ambient_temperature', 'shell_temperature', 'humidity', 'shell_speed', 'fan_speed']
        for field in required_fields:
            if field not in idle_config:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                })
        
        with open(IDLE_CONFIG_PATH, 'w') as f:
            json.dump(idle_config, f, indent=2)
        
        return jsonify({
            "status": "success",
            "message": "Development idle configuration saved successfully"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error saving idle configuration: {str(e)}"
        })

@app.route('/api/get_idle_config')
def get_idle_config():
    """API endpoint to get the current idle configuration."""
    try:
        if not os.path.exists(IDLE_CONFIG_PATH):
            default_config = {
                "ambient_temperature": 26,
                "shell_temperature": 0,
                "humidity": 0,
                "shell_speed": 0,
                "fan_speed": 0
            }
            return jsonify({
                "status": "success",
                "config": default_config
            })
        
        with open(IDLE_CONFIG_PATH, 'r') as f:
            config = json.load(f)
            
        return jsonify({
            "status": "success",
            "config": config
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error reading idle configuration: {str(e)}"
        })

def cleanup_processes():
    """Clean up mock processes on exit."""
    global mock_processes
    for name, process in mock_processes.items():
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()

import atexit
atexit.register(cleanup_processes)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    print("Development DryBox Web Control Interface")
    print("========================================")
    print("This is a development version that simulates the DryBox system")
    print("without requiring actual hardware or Raspberry Pi environment.")
    print("")
    print("Features:")
    print("- Mock processes simulate JSONparse.py, serialDebug.py, and logDB.py")
    print("- Development logs stored in RPI5/DataLogging/dev/")
    print("- Development configs stored in RPI5/JSONS/dev/")
    print("- All original functionality preserved for testing")
    print("")
    print("Starting server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    
    # Run the web server on a different port to avoid conflicts
    try:
        app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutting down development server...")
        cleanup_processes()
