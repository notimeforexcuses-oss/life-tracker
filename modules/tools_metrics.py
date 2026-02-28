import sqlite3
from datetime import datetime
from typing import Optional

DB_FILE = "brain.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_columns_exist():
    """Auto-migration to add new objective fields if missing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE daily_metrics ADD COLUMN hrv INTEGER")
        cursor.execute("ALTER TABLE daily_metrics ADD COLUMN resting_hr INTEGER")
        conn.commit()
    except:
        pass # Columns likely exist
    finally:
        conn.close()

def log_morning_metrics(sleep_hours: float, sleep_quality: int, morning_mood: int, readiness_score: int, 
                        hrv: Optional[int] = None, resting_hr: Optional[int] = None,
                        deep_min: int = 0, rem_min: int = 0, light_min: int = 0, awake_min: int = 0,
                        linked_project_id: Optional[int] = None, linked_goal_id: Optional[int] = None):
    """
    Logs the morning readiness data.
    New optional fields: hrv (ms), resting_hr (bpm), and sleep phases (min).
    """
    ensure_columns_exist() # Safety check
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Check if entry exists to update instead of insert
    cursor.execute("SELECT id FROM daily_metrics WHERE date = ? AND type = 'Morning'", (date_str,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE daily_metrics 
            SET sleep_hours=?, sleep_quality=?, morning_mood=?, readiness_score=?, hrv=?, resting_hr=?,
                sleep_deep_min=?, sleep_rem_min=?, sleep_light_min=?, sleep_awake_min=?
            WHERE date=? AND type='Morning'
        """, (sleep_hours, sleep_quality, morning_mood, readiness_score, hrv, resting_hr, 
              deep_min, rem_min, light_min, awake_min, date_str))
        msg = f"Updated morning metrics for {date_str}."
    else:
        cursor.execute("""
            INSERT INTO daily_metrics 
            (date, type, sleep_hours, sleep_quality, morning_mood, readiness_score, hrv, resting_hr, 
             sleep_deep_min, sleep_rem_min, sleep_light_min, sleep_awake_min, linked_project_id, linked_goal_id)
            VALUES (?, 'Morning', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, sleep_hours, sleep_quality, morning_mood, readiness_score, hrv, resting_hr, 
              deep_min, rem_min, light_min, awake_min, linked_project_id, linked_goal_id))
        msg = f"Morning metrics logged for {date_str}."
    
    conn.commit()
    conn.close()
    return msg

def log_evening_metrics(stress_level: int, productivity_score: int, evening_mood: int, diet_quality: int, 
                        win_of_the_day: str = None, primary_obstacle: str = None,
                        linked_project_id: Optional[int] = None, linked_goal_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT id FROM daily_metrics WHERE date = ? AND type = 'Evening'", (date_str,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE daily_metrics 
            SET stress_level=?, productivity_score=?, evening_mood=?, diet_quality=?, win_of_the_day=?, primary_obstacle=?
            WHERE date=? AND type='Evening'
        """, (stress_level, productivity_score, evening_mood, diet_quality, win_of_the_day, primary_obstacle, date_str))
        msg = f"Updated evening metrics for {date_str}."
    else:
        cursor.execute("""
            INSERT INTO daily_metrics 
            (date, type, stress_level, productivity_score, evening_mood, diet_quality, 
             win_of_the_day, primary_obstacle, linked_project_id, linked_goal_id)
            VALUES (?, 'Evening', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, stress_level, productivity_score, evening_mood, diet_quality, 
              win_of_the_day, primary_obstacle, linked_project_id, linked_goal_id))
        msg = f"Evening metrics logged for {date_str}."
    
    conn.commit()
    conn.close()
    return msg

def log_flexible_data(category: str, metric: str, value: str, notes: str = "",
                      linked_project_id: Optional[int] = None, linked_contact_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO flexible_tracker 
        (date, category, metric, value, notes, linked_project_id, linked_contact_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date_str, category, metric, value, notes, linked_project_id, linked_contact_id))
    
    conn.commit()
    conn.close()
    return f"Logged to Flexible Tracker: {category} - {metric}: {value}"