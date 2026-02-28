import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# --- DATABASE CONNECTION LOGIC (FIXED) ---
def get_db_connection():
    """
    Establishes a connection to the 'brain.db' file.
    It locates the database by looking one directory UP from this file's location.
    path: .../Life Tracker/modules/tools_chat.py -> .../Life Tracker/brain.db
    """
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    db_path = project_root / 'brain.db'
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

# --- CHAT TOOLS ---

def create_session(title="New Conversation"):
    conn = get_db_connection()
    cursor = conn.cursor()
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            created_at TEXT,
            is_archived INTEGER DEFAULT 0,
            tags TEXT,
            linked_goal_id INTEGER,
            linked_project_id INTEGER,
            linked_contact_id INTEGER
        )
    """)
    
    cursor.execute("INSERT INTO chat_sessions (title, created_at) VALUES (?, ?)", (title, created))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def save_message(session_id, role, content, tool_usage=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tool_json = json.dumps(tool_usage) if tool_usage else None
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            tool_usage TEXT,
            created_at TEXT
        )
    """)
    
    cursor.execute("""
        INSERT INTO chat_messages (session_id, role, content, tool_usage, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, role, content, tool_json, created))
    
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
    if not cursor.fetchone():
        conn.close()
        return []

    cursor.execute("SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

def list_sessions():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
    if not cursor.fetchone():
        conn.close()
        return []

    cursor.execute("SELECT id, title, created_at FROM chat_sessions WHERE is_archived=0 ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check tables exist first
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
    if cursor.fetchone():
        cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
    if cursor.fetchone():
        cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        
    conn.commit()
    conn.close()

def search_sessions(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    search_pattern = f"%{query}%"
    
    # Check tables exist first
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
    if not cursor.fetchone():
        conn.close()
        return []

    cursor.execute("""
        SELECT DISTINCT s.id, s.title, s.created_at 
        FROM chat_sessions s
        LEFT JOIN chat_messages m ON s.id = m.session_id
        WHERE (s.title LIKE ? OR m.content LIKE ?) AND s.is_archived = 0
        ORDER BY s.id DESC
    """, (search_pattern, search_pattern))
    
    rows = cursor.fetchall()
    conn.close()
    return rows
