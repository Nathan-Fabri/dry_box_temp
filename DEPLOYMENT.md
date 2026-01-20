# DryBox Deployment Guide

This guide explains how to deploy the DryBox system to multiple Raspberry Pi boxes.

## Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS installed
- Python 3.x installed
- Three Teensy 4.1 microcontrollers connected
- PostgreSQL database accessible on the network

## Deployment Steps

### 1. Clone the Repository

```bash
cd ~/Desktop
git clone <your-repository-url> DryBox
cd DryBox/drybox
```

### 2. Configure Environment Variables

Copy the template and edit with your specific settings:

```bash
cp .env.template .env
nano .env
```

Update these variables in `.env`:
- `DRYBOX_HOME`: Path where you installed the code (e.g., `/home/FBR-PI/Desktop/DryBox/drybox/RPI5`)
- `DB_HOST`: Your PostgreSQL server IP address
- `DB_PORT`: Database port (typically 5432)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

**Note:** The `.env` file path in the systemd service is currently hardcoded. If you install to a different location, update line 7 in `RPI5/drybox-web-control.service`:
```ini
EnvironmentFile=/home/FBR-PI/Desktop/DryBox/drybox/.env
```

### 3. Discover Teensy Hardware

Run the discovery script to find your Teensy serial device IDs:

```bash
cd RPI5/Scripts
./discover_hardware.sh
```

Or manually list them:
```bash
ls -la /dev/serial/by-id/ | grep -i teensy
```

### 4. Update Serial Port Configurations

Edit the following files with your specific Teensy device IDs:

**RPI5/JSONS/configParser.json** - Teensy interface 00 (main communication)
```json
{
  "serial_ports": [
    {
      "port": "/dev/serial/by-id/usb-Teensyduino_Triple_Serial_XXXXX-if00",
      "baud_rate": 115200,
      "name": "TeensyHVAC"
    },
    ...
  ]
}
```

**RPI5/JSONS/configDebug.json** - Teensy interface 02 (debug)
- Update serial ports with `-if02` suffix

**RPI5/JSONS/configThermalCamera.json** - Teensy interface 04 (thermal camera)
- Update serial ports with `-if04` suffix

### 5. Install Python Dependencies

```bash
cd ~/Desktop/DryBox/drybox/RPI5
pip3 install flask jsonschema opencv-python pyserial psycopg2-binary python-dotenv RPi.GPIO
```

Or if you have a requirements.txt:
```bash
pip3 install -r requirements.txt
```

### 6. Install PlatformIO (for flashing Teensy firmware)

```bash
# Create virtual environment for PlatformIO
python3 -m venv ~/pio-env
source ~/pio-env/bin/activate
pip install platformio

# Test installation
pio --version
```

### 7. Install the Systemd Service

```bash
cd ~/Desktop/DryBox/drybox/RPI5
sudo cp drybox-web-control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable drybox-web-control
```

### 8. Start the Service

```bash
sudo systemctl start drybox-web-control
```

Check status:
```bash
sudo systemctl status drybox-web-control
```

View logs:
```bash
sudo journalctl -u drybox-web-control -f
```

## Updating the Code

When you make changes to the code, update each box:

```bash
cd ~/Desktop/DryBox/drybox
git pull
sudo systemctl restart drybox-web-control
```

## Per-Box Configuration Summary

Each box needs unique configuration for:

### 1. **Serial Port IDs** (Hardware-specific)
- `RPI5/JSONS/configParser.json`
- `RPI5/JSONS/configDebug.json`
- `RPI5/JSONS/configThermalCamera.json`

Run `ls -la /dev/serial/by-id/` on each box to find the correct serial IDs.

### 2. **Installation Path** (if different from default)
- `.env` - Set `DRYBOX_HOME`
- `RPI5/drybox-web-control.service` - Update `EnvironmentFile` path if needed

### 3. **Database Configuration** (can be shared or unique)
- `.env` - Set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

### 4. **Process Configuration** (optional, per-test)
- `RPI5/JSONS/shellJson.json` - Contains layer/step definitions, temperatures, timing

## What's Already Dynamic

These components automatically adapt to the installation location:
- All Python scripts use relative paths based on script location
- Bash scripts (`start_drybox.sh`, `stop_drybox.sh`, `flash_teensy.sh`) use dynamic path resolution
- Log files are automatically created in `RPI5/DataLogging/`

## Troubleshooting

### Service won't start
1. Check the .env file path in the service file matches your installation
2. Verify DRYBOX_HOME in .env points to the correct directory
3. Check systemd logs: `sudo journalctl -u drybox-web-control -n 50`

### Can't find Teensy devices
1. Run `ls /dev/serial/by-id/` to verify devices are connected
2. Ensure user has permissions: `sudo usermod -a -G dialout $USER` (logout/login required)
3. Verify USB cable is data-capable (not power-only)

### Database connection errors
1. Verify database is accessible from the Pi: `ping <DB_HOST>`
2. Check database credentials in .env
3. Ensure PostgreSQL allows connections from the Pi's IP
4. Check logs: `cat ~/Desktop/DryBox/drybox/RPI5/DataLogging/logDB.log`

### Python import errors
1. Install missing packages: `pip3 install <package-name>`
2. For GPIO errors on non-Pi systems, use the dev version: `dev_drybox_web_control.py`

## Web Interface

Once running, access the web interface at:
- `http://<raspberry-pi-ip>:5000` (production)
- `http://<raspberry-pi-ip>:5001` (development mode)

## Development Mode

For testing without hardware:
```bash
cd ~/Desktop/DryBox/drybox/RPI5/Python
python3 dev_drybox_web_control.py
```

This runs a mock version with simulated data on port 5001.
