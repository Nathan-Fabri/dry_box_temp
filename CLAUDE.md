# DryBox Control System - Claude Context File

## Project Overview

The **DryBox** is an industrial environmental control system for precise temperature, humidity, and rotation management used in material processing. It features a distributed architecture with three Teensy 4.1 microcontrollers for real-time hardware control, coordinated by a Raspberry Pi 5 supervisor that handles control logic, data logging, and a web interface.

## System Architecture

### Hardware Layer - Three Teensy 4.1 Microcontrollers

1. **TeensyHVAC (Central Controller)**
   - Stepper motor control for rotating shell (DM422T driver)
   - Two HVAC fans with PWM control
   - Load cell for weight monitoring (HX711 interface)
   - 2 dehumidifiers + 1 humidifier via SSRs
   - PTC heaters via relays
   - Modbus RTU sensors (RS-485)

2. **TeensyLeft & TeensyRight (Tower Controllers)**
   - Fan control with PWM
   - Light control (triac-based)
   - Thermal camera integration (MLX90640 infrared)
   - Temperature/humidity sensors (SHT30, RS-485)
   - Environmental monitoring

**Serial Communication**: Each Teensy provides 3 USB serial interfaces:
- `if00`: Command/control interface
- `if02`: Debug output and sensor readings
- `if04`: Thermal camera data (tower units only)

### Software Layer - Raspberry Pi 5

Four main Python processes:

1. **JSONparse.py** (Master Controller)
   - Parses layer/step definitions from `shellJson.json`
   - Sends START commands and parameters to all Teensy units
   - Manages layer/step progression through time-based sequences
   - Handles GPIO buttons (E-Stop pin 22, Pause pin 27, Next pin 17)
   - Implements graceful shutdown with ALLOFF commands
   - Supports idle state after process completion

2. **serialDebug.py** (Data Monitor)
   - Reads debug interface (if02) from all Teensy units
   - Logs sensor readings to `DataLogging/` directory
   - Non-blocking continuous data collection

3. **logDB.py** (Database Logger)
   - Parses sensor data from log files
   - Stores to PostgreSQL database
   - Tracks file positions for incremental processing
   - Configurable via environment variables

4. **drybox_web_control.py** (Web Interface - Flask on port 5000)**
   - Start/stop system controls
   - Real-time log streaming
   - Shell layer navigation (next/previous/jump to layer)
   - Thermal camera live feed with temperature analysis
   - Firmware flashing for Teensy boards (via PlatformIO)
   - Layer configuration upload (`shellJson.json`)
   - System status monitoring

## Directory Structure

```
drybox/
├── PlatformIO/
│   ├── Teensys/                    # Main Teensy firmware (unified project)
│   │   ├── platformio.ini          # Board configs: TeensyHVAC, TeensyLeft, TeensyRight
│   │   └── src/
│   │       ├── TeensyHVAC/         # HVAC controller source
│   │       ├── TeensyLeft/         # Left tower source
│   │       └── TeensyRight/        # Right tower source
│   ├── Sensor Individual Test/     # Hardware testing projects
│   └── Remember.md                 # Quick command reference
│
├── RPI5/
│   ├── Python/
│   │   ├── JSONparse.py            # Master controller
│   │   ├── serialDebug.py          # Debug logger
│   │   ├── logDB.py                # Database logger
│   │   ├── drybox_web_control.py   # Production web server
│   │   ├── dev_drybox_web_control.py  # Dev server (no GPIO)
│   │   ├── static/                 # CSS, JS assets
│   │   └── templates/              # HTML templates (index.html, debug.html)
│   │
│   ├── JSONS/
│   │   ├── configParser.json       # Serial ports for if00 (commands)
│   │   ├── configDebug.json        # Serial ports for if02 (debug)
│   │   ├── configThermalCamera.json # Serial ports for if04 (camera)
│   │   ├── configLogDB.json        # Database connection settings
│   │   ├── shellJson.json          # Process layer definitions (uploaded via web)
│   │   ├── idleConfig.json         # Post-process idle state settings
│   │   └── schema                  # JSON schema for validation
│   │
│   ├── Scripts/
│   │   ├── start_drybox.sh         # Production startup
│   │   ├── stop_drybox.sh          # Production shutdown
│   │   ├── flash_teensy.sh         # Upload firmware to Teensys
│   │   ├── dev_start_drybox.sh     # Development startup
│   │   ├── dev_stop_drybox.sh      # Development shutdown
│   │   ├── install_service.sh      # Install systemd service
│   │   └── service_wrapper.sh      # Systemd service entry point
│   │
│   ├── DataLogging/                # Auto-created log files
│   └── drybox-web-control.service  # Systemd service file
│
├── .env                            # Environment variables (DB credentials, paths)
├── DEPLOYMENT.md                   # Comprehensive deployment guide
└── CLAUDE.md                       # This file
```

## Key Technologies

### Languages & Frameworks
- **Python 3**: Backend control, web interface
- **C++ (Arduino framework)**: Teensy firmware via PlatformIO
- **JavaScript/HTML/CSS**: Web interface frontend
- **Flask**: Web server framework

### Critical Libraries

**Python:**
- `pyserial`: Serial communication with Teensy boards
- `flask`: Web server
- `psycopg2`: PostgreSQL database
- `RPi.GPIO`: Hardware button inputs
- `opencv-python (cv2)`: Thermal camera processing
- `jsonschema`: Configuration validation
- `python-dotenv`: Environment variable management

**C++ (PlatformIO):**
- `ModbusMaster`: RS-485 sensor communication
- `ArduinoJson`: Data parsing
- `AccelStepper`: Stepper motor control
- `HX711`: Load cell interface
- `Adafruit_MLX90640`: Thermal camera

## Configuration Files

### Per-Deployment Configuration (Must be unique for each box)

1. **Serial Port Mappings** - Hardware-specific Teensy device IDs:
   - `RPI5/JSONS/configParser.json` (if00 - commands)
   - `RPI5/JSONS/configDebug.json` (if02 - debug)
   - `RPI5/JSONS/configThermalCamera.json` (if04 - camera)
   - Find device IDs: `ls -la /dev/serial/by-id/ | grep -i teensy`

2. **Environment Variables** (`.env`):
   - `DRYBOX_HOME`: Installation path (for reference only - **not used by code**, paths are calculated dynamically)
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL credentials
   - **IMPORTANT**: Passwords with special characters (`$`, `!`, etc.) must be escaped when the `.env` file is sourced by bash
     - Use `\$\$` instead of `$$` (bash interprets `$$` as process ID)
     - Or use single quotes: `DB_PASSWORD='MyPass$$'`

### Process Configuration (Per test/experiment)

- **`RPI5/JSONS/shellJson.json`**: Defines shell layers with time-series data
  - Layer name
  - Ambient temperature setpoints (arrays for time steps)
  - Shell temperature setpoints
  - Humidity targets
  - Duration for each step (minutes)
  - Shell rotation speed (RPM)
  - Fan speed (CFM)
  - Uploaded via web interface

- **`RPI5/JSONS/idleConfig.json`**: Post-process idle state parameters

## Development Workflows

### Building & Flashing Teensy Firmware

```bash
# Activate PlatformIO environment
source ~/pio-env/bin/activate

# Navigate to firmware directory
cd PlatformIO/Teensys

# Build all environments
pio run

# Flash specific Teensy
pio run -e TeensyHVAC --target upload
pio run -e TeensyLeft --target upload
pio run -e TeensyRight --target upload

# Or flash all at once
pio run --target upload
```

### Starting/Stopping the System

**Production (as systemd service):**
```bash
sudo systemctl start drybox-web-control
sudo systemctl stop drybox-web-control
sudo systemctl status drybox-web-control
sudo journalctl -u drybox-web-control -f  # View logs
```

**Manual (for testing):**
```bash
cd RPI5/Scripts
./start_drybox.sh      # Production mode
./stop_drybox.sh       # Sends ALLOFF to all Teensys

# Or development mode (no GPIO, port 5001)
cd RPI5/Python
python3 dev_drybox_web_control.py
```

### Monitoring Serial Output

```bash
# View command interface (if00)
cat /dev/serial/by-id/usb-Teensyduino_USB_Serial_XXXXX-if00

# View debug interface (if02)
cat /dev/serial/by-id/usb-Teensyduino_USB_Serial_XXXXX-if02

# View thermal camera data (if04)
cat /dev/serial/by-id/usb-Teensyduino_USB_Serial_XXXXX-if04
```

### Database Logging

Database connection configured in `RPI5/JSONS/configLogDB.json` with environment variables:
- Reads from log files in `DataLogging/`
- Stores parsed sensor data to PostgreSQL
- Tracks file positions to avoid duplicate entries

## Coding Conventions & Standards

### Python Code Style
- Follow PEP 8 style guidelines
- Use descriptive variable names (e.g., `serial_port`, not `sp`)
- Keep functions focused and modular
- Add docstrings to complex functions
- Handle exceptions gracefully with proper logging
- Use `logging` module instead of print statements for production code

### C++ (Teensy Firmware) Style
- Follow Arduino naming conventions
- Use `camelCase` for function names
- Use `UPPER_CASE` for constants and pin definitions
- Keep `loop()` function lean - delegate to separate handler functions
- Document pin assignments in `pinmap.h`
- Use non-blocking code patterns (avoid `delay()`)
- Prefix global variables with descriptive context (e.g., `hvacFanSpeed`)

### File Organization
- **Always prefer editing existing files** over creating new ones
- Group related functionality in modules
- Use `pinmap.h` for hardware pin definitions in Teensy code
- Separate command parsing, sensor reading, and control logic
- Configuration goes in `RPI5/JSONS/`, not hardcoded

### Serial Communication Protocol
- Commands are newline-terminated strings
- Teensy responses include device identifier
- Debug output (if02) includes timestamps
- Format: `[TeensyName] Sensor: value, Sensor: value, ...`

## Common Tasks

### Adding a New Sensor to Teensy

1. Add pin definition to `src/Teensy*/pinmap.h`
2. Add sensor initialization in `setup()`
3. Add sensor reading function in `sensors.cpp`/`sensors.h`
4. Add reading to debug output in `send_readings.cpp`
5. Update command parser if sensor needs control
6. Document sensor type, wiring, and I2C address (if applicable)

### Adding a New Command

1. Update `command_parser.cpp` in relevant Teensy firmware
2. Add command handler function
3. Update `START` command parameters if needed
4. Update `JSONparse.py` to send new command/parameters
5. Update `shellJson.json` schema if adding new layer parameters
6. Test via web interface or serial monitor

### Modifying Web Interface

1. Flask routes in `drybox_web_control.py`
2. HTML templates in `RPI5/Python/templates/`
3. CSS styling in `RPI5/Python/static/styles.css`
4. Use AJAX for dynamic updates without page reload
5. Test with both production and dev servers

### Deploying to a New Box

Follow the comprehensive guide in `DEPLOYMENT.md`:
1. Clone repository
2. Configure `.env` with database and paths
3. Discover and configure Teensy serial IDs in JSON configs
4. Install Python dependencies
5. Install PlatformIO for firmware flashing
6. Install systemd service
7. Start and verify

## Safety & Error Handling

### Hardware Safety
- **E-Stop button (GPIO 22)**: Immediately sends ALLOFF to all Teensys
- **Graceful shutdown**: Always use `stop_drybox.sh` or web interface to stop
- **Connection monitoring**: Auto-reconnect on serial port failures
- **Watchdog timers**: Teensys reset outputs if no commands received

### Error Handling Patterns
- All serial operations wrapped in try-except blocks
- Log errors with context (timestamps, device names)
- Retry logic for transient failures
- Signal handlers (SIGTERM/SIGINT) for clean shutdown
- Validate JSON schemas before parsing

### Known Gotchas
- **Bash special characters in passwords**: `service_wrapper.sh` uses `source` to load `.env`, which means bash expands special variables:
  - `$$` becomes the process ID - use `\$\$` or single quotes
  - `!` triggers history expansion in interactive shells
  - Always escape special characters or use quotes in `.env` values
- **Dynamic paths**: All Python scripts calculate paths relative to their location - `DRYBOX_HOME` in `.env` is not actually used
- **`.env` file loading**: `load_dotenv()` in Python loads from `{drybox_root}/.env` explicitly (two directories up from the script)
- Teensy USB IDs change if moved to different USB ports - use `/dev/serial/by-id/`
- User must be in `dialout` group for serial access: `sudo usermod -a -G dialout $USER`
- PlatformIO requires virtual environment activation before use
- GPIO library requires root or proper permissions - use `dev_` versions for non-Pi testing

## Testing Strategy

### Unit Testing (Hardware)
- Individual sensor test projects in `PlatformIO/Sensor Individual Test/`
- Test each actuator/sensor independently before integration
- Verify sensor readings with known references

### Integration Testing
1. Start system with minimal configuration
2. Verify each Teensy connects and responds
3. Test command/response cycle
4. Verify sensor readings in web interface
5. Test layer progression with short durations
6. Verify data logging to database

### Development Environment
- Use `dev_drybox_web_control.py` for testing without Raspberry Pi GPIO
- Mock data available for web interface testing
- Test with single layer configurations first

## Documentation

- **DEPLOYMENT.md**: Complete deployment and configuration guide
- **Remember.md**: Quick command reference for developers
- **This file (CLAUDE.md)**: Architecture and development context
- Code comments: Focus on "why" not "what" - explain non-obvious logic

## Related Systems

This codebase is part of a larger ecosystem:
- **pdr2000_logger**: Separate service for PDR2000 device logging (in parent directory)
- **uStreamer_Webserver**: Camera streaming service (in parent directory)
- Both use similar systemd service patterns

## Support & Troubleshooting

See `DEPLOYMENT.md` for detailed troubleshooting of:
- Service startup issues
- Teensy device discovery
- Database connection problems
- Permission errors
- Web interface access

### Troubleshooting Database Connection Issues

If you see `FATAL: password authentication failed` errors in `logDB.log`:

**1. Verify the password is being loaded correctly:**
```bash
# Check what the service wrapper is loading
sudo journalctl -u drybox-web-control -n 50 --no-pager | grep "DB_PASSWORD"

# The wrapper shows first 2 and last 2 characters for debugging
# For "MyPass$$", should show: Length: 8, Starts: My**, Ends: **$$
```

**2. Check for bash variable expansion:**
```bash
# If password ends with process ID digits instead of expected characters,
# bash is expanding special variables like $$, $!, etc.

# Fix: Escape special characters in .env
DB_PASSWORD=MyPass\$\$

# Or use single quotes
DB_PASSWORD='MyPass$$'
```

**3. Verify the actual .env file content:**
```bash
# On the Pi, check the raw file
cat -n /home/FBR-PI/software/controls/drybox/.env

# Look for multiple DB_PASSWORD lines (bash uses the last one)
grep -n DB_PASSWORD /home/FBR-PI/software/controls/drybox/.env
```

**4. Test PostgreSQL connection manually:**
```bash
# On the Pi, test with psql
PGPASSWORD='YourPassword' psql -h 192.168.48.157 -U admin -d FabriSenseDB

# If this fails, the password in PostgreSQL doesn't match .env
```

**5. Reset PostgreSQL password if needed:**
```sql
-- On the PostgreSQL server
sudo -u postgres psql
ALTER USER admin WITH PASSWORD 'YourPassword';
```

## Version Control

- **Main branch**: `master`
- **Current branch**: `dynamic-drybox-deployment`
- Use descriptive commit messages
- Test changes on development system before production deployment
- Update DEPLOYMENT.md when adding new configuration requirements
