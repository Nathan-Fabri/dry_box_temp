#!/usr/bin/env python3
import os
import sys
import json
import time
import signal
import logging
import re
from pathlib import Path
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

running = True

# Define paths dynamically based on script location
# Get the directory where this script is located (Python folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get RPI5 directory
BASE_DIR = os.path.dirname(SCRIPT_DIR)
# Go up one more level to get drybox root directory
DRYBOX_ROOT = os.path.dirname(BASE_DIR)

# Load environment variables from .env file in drybox root
ENV_PATH = os.path.join(DRYBOX_ROOT, '.env')
load_dotenv(ENV_PATH)
LOG_DIR = os.path.join(BASE_DIR, "DataLogging")
JSON_DIR = os.path.join(BASE_DIR, "JSONS")

# Configuration file paths - Dynamic paths
CONFIG_PATH = os.path.join(JSON_DIR, 'configLogDB.json')
LOG_PATH = os.path.join(LOG_DIR, 'logDB.log')

# Setup logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

def log_print(message):
    print(message)
    logging.info(message)


def load_config():
    """Load configuration from configLogDB.json with environment variable substitution"""
    global config, dbConfig
    config_path = Path(CONFIG_PATH)

    if not config_path.exists():
        log_print(f"ERROR: Configuration file not found at {config_path}")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config_text = f.read()

            # Replace environment variables in the config
            for key, value in os.environ.items():
                config_text = config_text.replace(f"${{{key}}}", value)

            config = json.loads(config_text)
            log_print(f"Loaded configuration from {config_path}")
    except Exception as e:
        log_print(f"ERROR: Failed to parse configuration: {e}")
        sys.exit(1)

    # Set up database config with environment variables (override config values if present)
    db_config_raw = config.get("database", {})
    dbConfig = {
        "host": os.getenv("DB_HOST", db_config_raw.get("host")),
        "port": os.getenv("DB_PORT", db_config_raw.get("port")),
        "dbname": os.getenv("DB_NAME", db_config_raw.get("dbname")),
        "user": os.getenv("DB_USER", db_config_raw.get("user")),
        "password": os.getenv("DB_PASSWORD", db_config_raw.get("password")),
    }

    if not all([dbConfig["host"], dbConfig["port"], dbConfig["dbname"], dbConfig["user"]]):
        log_print("ERROR: Incomplete database configuration. Check your environment variables or config file.")
        sys.exit(1)

    if not dbConfig["password"]:
        log_print("WARNING: No database password found in environment variables or config!")


def get_last_position(log_path):
    """Get the last processed position from a tracking file"""
    position_file = log_path + '.position'
    if os.path.exists(position_file):
        try:
            with open(position_file, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def save_last_position(log_path, position):
    """Save the last processed position to a tracking file"""
    position_file = log_path + '.position'
    try:
        with open(position_file, 'w') as f:
            f.write(str(position))
    except Exception as e:
        logging.error(f"Error saving position: {e}")

# ...existing parser functions remain the same...

# def parse_temp_humidity_sensor_data(message):
#     pattern = (
#         r'✅\s*env_chamber\s*\|\s*'
#         r'temperature:\s*([\d.]+)\s*°C\s*\|\s*'
#         r'humidity:\s*([\d.]+)\s*%RH'
#     )

#     match = re.search(pattern, message, re.IGNORECASE)
#     if not match:
#         return None

#     temperature = float(match.group(1))
#     humidity = float(match.group(2))

#     timestamp = datetime.now(timezone.utc).isoformat()

#     return {
#         'timestamp': timestamp,
#         'sensors': [
#             {'name': 'env_chamber_temperature', 'value': temperature},
#             {'name': 'env_chamber_humidity', 'value': humidity}
#         ]
#     }

def parse_temp_humidity_sensor_data(message):
    pattern = (
        r'✅ env_chamber \| '
        r'temperature: ([\d.]+) °C \| '
        r'humidity: ([\d.]+) %RH'
    )

    match = re.match(pattern, message, re.IGNORECASE)
    if not match:
        return None

    temperature = float(match.group(1))
    humidity = float(match.group(2))

    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        'timestamp': timestamp,
        'sensors': [
            {'name': 'env_chamber_temperature', 'value': temperature},
            {'name': 'env_chamber_humidity', 'value': humidity}
        ]
    }


# def parse_temp_humidity_sensor_data(message):
#     """Parse temperature/humidity sensor data"""
#     temp_hum_pattern = r'✅ (\w+(?:_\w+)*) \| Temp: ([\d.]+) °C \| Hum: ([\d.]+) %RH'
#     temp_hum_match = re.match(temp_hum_pattern, message)
    
#     if not temp_hum_match:
#         return None
    
#     sensor_base_name = temp_hum_match.group(1)
#     temperature = float(temp_hum_match.group(2))
#     humidity = float(temp_hum_match.group(3))
    
#     timestamp = datetime.now(timezone.utc).isoformat()
    
#     return {
#         'timestamp': timestamp,
#         'sensors': [
#             {'name': f"{sensor_base_name}_Temp", 'value': temperature},
#             {'name': f"{sensor_base_name}_Hum", 'value': humidity}
#         ]
#     }


def parse_sensor_data_vector(message):
    """Main parser function"""
    if not message.startswith('✅'):
        return None
    
    parsed_data = parse_temp_humidity_sensor_data(message)
    if parsed_data:
        return parsed_data
    return None

# def insert_vector_to_timescaledb(parsed_data, device_name):
#     """Insert vector data into TimescaleDB"""
#     if parsed_data is None or "sensors" not in parsed_data:
#         return

#     timestamp = parsed_data["timestamp"]
#     records = []

#     for entry in parsed_data['sensors']:
#         sensor_id = entry["name"]
#         value = entry["value"]
#         records.append((timestamp, sensor_id, value))

#     if not records:
#         return

#     insert_stmt = """
#         INSERT INTO sensor_data_testing (time, sensor_id, value)
#         VALUES %s
#         ON CONFLICT (time, sensor_id) DO NOTHING;
#     """
#     # insert_stmt = """
#     #     INSERT INTO sensor_data (time, sensor_id, value)
#     #     VALUES (NOW(), %s, %s)
#     #     ON CONFLICT DO NOTHING;
#     # """

#     try:
#         conn = psycopg2.connect(**dbConfig)
#         cur = conn.cursor()
#         execute_values(cur, insert_stmt, records)
#         conn.commit()
#         cur.close()
#         conn.close()
#         logging.info(f"Inserted {len(records)} values from {device_name} to TimescaleDB.")
#     except Exception as e:
#         logging.error(f"Failed DB insert from {device_name}: {e}")

def insert_vector_to_timescaledb(parsed_data, device_name):
    if parsed_data is None or "sensors" not in parsed_data:
        return

    records = []
    ts = parsed_data["timestamp"]

    for entry in parsed_data['sensors']:
        records.append((ts, entry["name"], entry["value"]))

    if not records:
        return

    insert_stmt = """
        INSERT INTO sensor_data_testing (time, sensor_id, value)
        VALUES %s
        ON CONFLICT DO NOTHING;
    """

    try:
        with psycopg2.connect(**dbConfig) as conn:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    insert_stmt,
                    records,
                    template="(%s, %s, %s)"
                )
            conn.commit()

        logging.info(f"Inserted {len(records)} values from {device_name} to TimescaleDB.")

    except Exception as e:
        logging.error(f"Failed DB insert from {device_name}: {e}")


def process_log_line(line):
    """Process a line from the serial log file"""
    try:
        match = re.search(r'DATA: ([^:]+): (.*)', line)
        if not match:
            return False
        
        device_name = match.group(1)
        data_part = match.group(2)
        
        parsed_data = parse_sensor_data_vector(data_part)
        if parsed_data:
            insert_vector_to_timescaledb(parsed_data, device_name)
            return True
    except Exception as e:
        logging.error(f"Error processing log line: {e}")
    
    return False

def follow_log_file(log_path):
    """Follow the log file with position tracking"""
    lines_read = 0
    lines_processed = 0
    last_position = get_last_position(log_path)
    
    # Get the sleep interval from config (convert ms to seconds)
    sleep_interval = config.get("log_interval_ms", 100) / 1000.0  # Default to 100ms
    
    try:
        # with open(log_path, 'r') as file:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as file:

            file.seek(last_position)
            log_print(f"Starting from position {last_position}")
            log_print(f"Using {sleep_interval*1000}ms check interval")
            
            while running:
                line = file.readline()
                if not line:
                    save_last_position(log_path, file.tell())
                    time.sleep(sleep_interval)  # Use configurable interval
                    continue
                
                lines_read += 1
                
                if "DATA:" in line:
                    if process_log_line(line.strip()):
                        lines_processed += 1
                
                # Save position every 10 lines
                if lines_read % 10 == 0:
                    save_last_position(log_path, file.tell())
                
                # Progress every 100 lines
                if lines_read % 100 == 0:
                    log_print(f"Processed {lines_read} lines, {lines_processed} sensor readings")
                    
    except Exception as e:
        logging.error(f"Error following log file: {e}")
    finally:
        # Save final position
        try:
            save_last_position(log_path, file.tell())
        except:
            pass

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    global running
    # Don't use logging in signal handlers to avoid reentrant calls
    # Just set the flag and let the main loop handle shutdown
    running = False
    
    if sig == signal.SIGINT:
        sys.exit(0)

def main():
    """Main function"""
    global running
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    log_print("LogDB starting...")
    log_print(f"Loaded .env from: {ENV_PATH}")
    load_config()
    
    sensor_log_path = config.get("sensor_log_path")
    log_print(f"Monitoring: {sensor_log_path}")
    
    if not os.path.exists(sensor_log_path):
        log_print(f"Error: Log file not found at {sensor_log_path}")
        return
    
    log_print("LogDB running. Press Ctrl+C to exit.")
    follow_log_file(sensor_log_path)
    
    # Log shutdown message after the main loop exits
    if not running:
        log_print("Received shutdown signal. Shutting down...")
    log_print("LogDB shut down.")

if __name__ == "__main__":
    main()