#!/bin/bash
# Service wrapper that loads .env and starts drybox_web_control.py
# This allows the service to be path-independent

# Find the script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPI5_DIR="$(dirname "$SCRIPT_DIR")"
DRYBOX_DIR="$(dirname "$RPI5_DIR")"

# Load environment variables from .env
if [ -f "$DRYBOX_DIR/.env" ]; then
    set -a  # automatically export all variables
    source "$DRYBOX_DIR/.env"
    set +a
fi

# Change to RPI5 directory
cd "$RPI5_DIR"

# Execute the Python script
exec /usr/bin/python3 "$RPI5_DIR/Python/drybox_web_control.py"
