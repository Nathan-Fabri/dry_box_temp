#!/bin/bash
# Install DryBox systemd service
# This script installs the drybox-web-control service and enables it to start on boot

# Get the directory where this script is located (Scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up one level to get RPI5 directory
RPI5_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_FILE="$RPI5_DIR/drybox-web-control.service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "DryBox Service Installation"
echo "=========================================="
echo ""

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}Error: Service file not found at $SERVICE_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found service file: $SERVICE_FILE"

# Check if .env file exists
ENV_FILE="$(dirname "$RPI5_DIR")/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠${NC}  Warning: .env file not found at $ENV_FILE"
    echo "   Make sure to create it from .env.template before starting the service"
else
    echo -e "${GREEN}✓${NC} Found .env file: $ENV_FILE"
fi

# Check if running as root (needed for systemd operations)
if [ "$EUID" -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}This script needs sudo privileges to install the systemd service.${NC}"
    echo "Re-running with sudo..."
    sudo "$0" "$@"
    exit $?
fi

echo ""
echo "Installing service file..."

# Copy service file to systemd directory
cp "$SERVICE_FILE" /etc/systemd/system/drybox-web-control.service

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Service file copied to /etc/systemd/system/"
else
    echo -e "${RED}✗${NC} Failed to copy service file"
    exit 1
fi

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Systemd daemon reloaded"
else
    echo -e "${RED}✗${NC} Failed to reload systemd daemon"
    exit 1
fi

# Enable service to start on boot
echo "Enabling service to start on boot..."
systemctl enable drybox-web-control.service

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Service enabled (will start automatically on boot)"
else
    echo -e "${RED}✗${NC} Failed to enable service"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Service Management Commands:"
echo "  Start service:   sudo systemctl start drybox-web-control"
echo "  Stop service:    sudo systemctl stop drybox-web-control"
echo "  Restart service: sudo systemctl restart drybox-web-control"
echo "  Service status:  sudo systemctl status drybox-web-control"
echo "  View logs:       sudo journalctl -u drybox-web-control -f"
echo "  Disable service: sudo systemctl disable drybox-web-control"
echo ""

# Ask if user wants to start the service now
read -p "Do you want to start the service now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting drybox-web-control service..."
    systemctl start drybox-web-control.service

    # Wait a moment for service to start
    sleep 2

    # Check if service is running
    if systemctl is-active --quiet drybox-web-control.service; then
        echo -e "${GREEN}✓${NC} Service is running"
        echo ""
        echo "Check status with: sudo systemctl status drybox-web-control"
    else
        echo -e "${RED}✗${NC} Service failed to start"
        echo ""
        echo "Check logs with: sudo journalctl -u drybox-web-control -n 50"
        exit 1
    fi
else
    echo "Service not started. Start it manually with:"
    echo "  sudo systemctl start drybox-web-control"
fi

echo ""
echo "The service will now automatically start on every boot."
echo ""
