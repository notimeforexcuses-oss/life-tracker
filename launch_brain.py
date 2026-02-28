import subprocess
import sys
import time
import os

DAEMON_SCRIPT = "brain_daemon.py"

def launch():
    print(f"Initializing {DAEMON_SCRIPT}...")
    try:
        # Launch as a separate process
        if sys.platform == 'win32':
            # creationflags=subprocess.CREATE_NEW_CONSOLE opens a new window
            process = subprocess.Popen([sys.executable, DAEMON_SCRIPT], 
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            process = subprocess.Popen([sys.executable, DAEMON_SCRIPT])
            
        print(f"Daemon started (PID: {process.pid}).")
        print("Check 'brain_pulse.log' for activity.")
        print("Close the new window to stop the daemon.")
        
    except Exception as e:
        print(f"Failed to launch: {e}")

if __name__ == "__main__":
    launch()
