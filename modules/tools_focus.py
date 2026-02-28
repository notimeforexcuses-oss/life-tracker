import sqlite3
from datetime import datetime
from typing import Optional

DB_FILE = "brain.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def log_focus(focus_level: int, energy_level: int, notes: str = "", linked_project_id: Optional[int] = None):
    """
    Logs subjective Focus and Energy levels during the day.
    Levels are 1 (Low) to 10 (High).
    """
    if not (1 <= focus_level <= 10) or not (1 <= energy_level <= 10):
        return "Error: Levels must be between 1 and 10."

    conn = get_db_connection()
    cursor = conn.cursor()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    
    cursor.execute("""
        INSERT INTO focus_logs (date, time, focus_level, energy_level, notes, linked_project_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, time_str, focus_level, energy_level, notes, linked_project_id))
    
    conn.commit()
    conn.close()
    return f"Logged: Focus {focus_level}/10, Energy {energy_level}/10 at {time_str}."

def get_todays_focus():
    """Retrieves today's focus logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT time, focus_level, energy_level, notes FROM focus_logs WHERE date = ? ORDER BY time ASC", (date_str,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows: return "No focus data logged today."
    
    return "\n".join([f"{r['time']}: Focus {r['focus_level']}, Energy {r['energy_level']} ({r['notes']})" for r in rows])