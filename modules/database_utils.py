import sqlite3
import os
from pathlib import Path

# --- PATH LOGIC ---
# 1. Get the path of THIS file (database_utils.py) inside 'modules'
CURRENT_DIR = Path(__file__).resolve().parent

# 2. Go up one level to find the 'Life Tracker' root folder
# modules/../brain.db
DB_PATH = CURRENT_DIR.parent / 'brain.db'

def get_db_connection():
    """
    Returns a connection to the main brain.db, ensuring consistent
    access regardless of where the script is run from.
    """
    # Debug print to confirm it's working (you'll see this in the console)
    # print(f"🔌 TOOL CONNECTING TO: {DB_PATH}") 
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn