import sqlite3
from datetime import datetime
import json
from pathlib import Path
from typing import Optional
from modules.vector_utils import update_vector_index

# --- ROBUST PATH LOGIC ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
DB_FILE = project_root / 'brain.db'

def get_db_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def add_journal_entry(content: str, tags: str = "[]", 
                      linked_project_id: Optional[int] = None, linked_goal_id: Optional[int] = None, 
                      linked_contact_id: Optional[int] = None, linked_task_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validation
    try:
        json.loads(tags)
    except:
        tags = "[]"
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    
    cursor.execute("""
        INSERT INTO journal_entries 
        (date, time, content, tags, linked_project_id, linked_goal_id, linked_contact_id, linked_task_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, time_str, content, tags, linked_project_id, linked_goal_id, linked_contact_id, linked_task_id))
    
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    update_vector_index(entry_id, 'journal', f"Journal: {content}\nTags: {tags}")
    return f"Journal entry saved (ID: {entry_id})."