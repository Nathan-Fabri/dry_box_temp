import serial

PORT = "COM5"
BAUD = 115200
LOG_FILE = r"C:/Users/nathan/Desktop/Controls_Code/src/controls/drybox/DataLogging/serialDebug.log"

ser = serial.Serial(PORT, BAUD, timeout=1)

print(f"Logging {PORT} → {LOG_FILE}")

with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(line)
            f.write(line + "\n")
