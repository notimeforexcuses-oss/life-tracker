import time
import schedule
import logging
from datetime import datetime
# FIX: Using the standard spelling 'brain_daemon'
from brain_daemon import run_automator

# Configure Logging
logging.basicConfig(
    filename='brain_pulse.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def job():
    print(f"\n💓 PULSE: Initiating Brain Daemon at {datetime.now().strftime('%H:%M')}...")
    logging.info("Pulse triggered.")
    
    try:
        run_automator()
        logging.info("Daemon execution successful.")
    except Exception as e:
        print(f"❌ ERROR: Daemon failed: {e}")
        logging.error(f"Daemon failed: {e}")

    print("💤 PULSE: Sleeping...")

# --- CONFIGURATION ---
# Run every 30 minutes
schedule.every(30).minutes.do(job)

# Also run once immediately on startup
if __name__ == "__main__":
    print("🚀 SYSTEM START: Pulse Scheduler Online.")
    job() # First run
    
    while True:
        schedule.run_pending()
        time.sleep(1)