import time
import subprocess
from datetime import datetime

# Configuration
STACK_ID = 0 
FILENAME = "RTD.log"
INTERVAL = 5 

def get_rtd_temp(stack, channel):
    """Runs the 'rtd' command line tool and captures the output"""
    try:
        # Executes: rtd <stack> read <channel>
        result = subprocess.run(['rtd', str(stack), 'read', str(channel)], 
                                capture_output=True, text=True, check=True)
        # Convert the string output (e.g., "23.50") to a float
        return float(result.stdout.strip())
    except Exception:
        return None

print(f"Logging data to {FILENAME}. Press Ctrl+C to exit.")

try:
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #log_entry = f"--- Scan at {now} ---\n"
        log_entry="✅ DATA: Sequent_RTD: "
        # Read Channels 1, 2, and 3
        for ch in range(1, 4):
            temp = get_rtd_temp(STACK_ID, ch)
            
            if temp is not None:
                log_entry += f"Channel {ch}: {temp:.2f} C "
            else:
                log_entry += f"Channel {ch}: SENSOR ERROR "
        
        #log_entry += "---------------------------\n\n"
        log_entry += "\n"
        with open(FILENAME, "a") as f:
            f.write(log_entry)
        
        print(f"Saved entry at {now}")
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nLogging stopped.")
