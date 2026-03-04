import serial

PORT = "/dev/ttyACM0"
BAUD = 115200
LOG_FILE = r"/home/fabriusa/dry_box_temp/DataLogging/serialDebug.log"

ser = serial.Serial(PORT, BAUD, timeout=1)

print(f"Logging {PORT} → {LOG_FILE}")

with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(line)
            f.write(line + "\n")
            f.flush()
