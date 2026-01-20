Check if Web Server is running
sudo systemctl status drybox-web-control.service

Stop:
sudo systemctl stop drybox-web-control.service

Activate PIO:
source ~/pio-env/bin/activate

All Upload:
pio run --target upload

Target Upoad:
HVAC:
pio run -e TeensyHVAC --target upload
Towers:
pio run -e TeensyLeft --target upload
pio run -e TeensyRight --target upload

Serial Monitor:
Teensy HVAC:
cat /dev/serial/by-id/usb-Teensyduino_USB_Serial_13143020-if00

Teensy Right:
cat /dev/serial/by-id/usb-Teensyduino_USB_Serial_13142880-if00

Teensy Left:
cat /dev/serial/by-id/usb-Teensyduino_USB_Serial_13142960-if00

Logging stuff:
Log serial monitor:
nohup cat /dev/serial/by-id/usb-Teensyduino_USB_Serial_13143020-if00 > teensy_log.txt &

Check if running:
ps aux | grep cat

To kill:
kill 2525

Clean Shutdown:
sudo shutdown -h now

Manual Upload Method:

TeensyHVAC:
sudo ~/teensy_loader_cli/teensy_loader_cli -mmcu=TEENSY41 -w -v ~/Desktop/DryBox/drybox/PlatformIO/TeensyHVAC/.pio/build/TeensyHVAC/firmware.hex

TeensyTower:
Left:
sudo ~/teensy_loader_cli/teensy_loader_cli -mmcu=TEENSY41 -w -v ~/Desktop/DryBox/drybox/PlatformIO/TeensyTowerLeft/.pio/build/TeensyTowerLeft/firmware.hex
Right:
sudo ~/teensy_loader_cli/teensy_loader_cli -mmcu=TEENSY41 -w -v ~/Desktop/DryBox/drybox/PlatformIO/TeensyTowerRight/.pio/build/TeensyTowerRight/firmware.hex

Change Dev Rules for Teensy/PI Connection:
    sudo nano /etc/udev/rules.d/99-teensy.rules
    sudo udevadm control --reload
    sudo udevadm trigger

DryBox - 00 Teensy Serial UID:
SUBSYSTEM=="tty", ATTRS{serial}=="13142870", SYMLINK+="teensyHVAC"
SUBSYSTEM=="tty", ATTRS{serial}=="13143020", SYMLINK+="teensyHVAC"
SUBSYSTEM=="tty", ATTRS{serial}=="13142960", SYMLINK+="teensyLEFT"
SUBSYSTEM=="tty", ATTRS{serial}=="13142880", SYMLINK+="teensyRIGHT"