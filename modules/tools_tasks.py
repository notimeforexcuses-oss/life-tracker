import sys
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from googleapiclient.discovery import build
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.auth_google import authenticate_google
from modules.vector_utils import update_vector_index

# --- ROBUST PATH LOGIC ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
DB_FILE = project_root / 'brain.db'

def get_db_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

# --- GOOGLE TASKS (API) ---

def get_tasks_service():
    creds = authenticate_google()
    return build('tasks', 'v1', credentials=creds)

def get_default_tasklist_id(service):
    """Helper to get the primary task list."""
    results = service.tasklists().list(maxResults=1).execute()
    items = results.get('items', [])
    if not items: return None
    return items[0]['id']

def list_google_tasks(limit: int = 10):
    try:
        service = get_tasks_service()
        tasklist_id = get_default_tasklist_id(service)
        if not tasklist_id: return "No task lists found."
        
        tasks = service.tasks().list(tasklist=tasklist_id, maxResults=limit, showCompleted=False).execute().get('items', [])
        if not tasks: return "No pending tasks."
        
        output = []
        for t in tasks:
            due = t.get('due', '')[:10] if t.get('due') else "No Date"
            output.append(f"ID: {t['id']} | {due} | ☐ {t['title']}")
        return "\n".join(output)
    except Exception as e: return f"Error: {e}"

def add_google_task(title: str, notes: str = "", due_date: str = None):
    """
    due_date format: 'YYYY-MM-DD'
    """
    try:
        service = get_tasks_service()
        tasklist_id = get_default_tasklist_id(service)
        
        body = {'title': title, 'notes': notes}
        if due_date:
            # Google Tasks requires RFC3339 timestamp (e.g., 2023-10-01T00:00:00.000Z)
            dt = datetime.strptime(due_date, "%Y-%m-%d")
            body['due'] = dt.isoformat() + 'Z'
            
        result = service.tasks().insert(tasklist=tasklist_id, body=body).execute()
        return f"Success: Added '{title}' (ID: {result.get('id')})."
    except Exception as e: return f"Error: {e}"

def complete_google_task(task_id: str):
    try:
        service = get_tasks_service()
        tasklist_id = get_default_tasklist_id(service)
        service.tasks().patch(tasklist=tasklist_id, task=task_id, body={'status': 'completed'}).execute()
        return f"Success: Task {task_id} completed."
    except Exception as e: return f"Error: {e}"

def delete_google_task(task_id: str):
    """
    Permanently deletes a Google Task.
    """
    try:
        service = get_tasks_service()
        tasklist_id = get_default_tasklist_id(service)
        service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
        return f"Success: Task {task_id} deleted."
    except Exception as e: return f"Error: {e}"

def update_google_task(task_id: str, new_title: str = None, new_due_date: str = None, new_notes: str = None):
    """
    Updates an existing task.
    new_due_date: 'YYYY-MM-DD'
    """
    try:
        service = get_tasks_service()
        tasklist_id = get_default_tasklist_id(service)
        
        body = {}
        if new_title: body['title'] = new_title
        if new_notes: body['notes'] = new_notes
        if new_due_date:
            dt = datetime.strptime(new_due_date, "%Y-%m-%d")
            body['due'] = dt.isoformat() + 'Z'
            
        service.tasks().patch(tasklist=tasklist_id, task=task_id, body=body).execute()
        return f"Success: Updated task {task_id}."
    except Exception as e: return f"Error: {e}"

def defer_overdue_tasks(target_date: str):
    """
    Batch moves ALL overdue Google Tasks to a specific target date.
    target_date: 'YYYY-MM-DD' (e.g., '2025-10-25' or just 'today')
    """
    try:
        if target_date.lower() == 'today':
            target_date = datetime.now().strftime("%Y-%m-%d")
            
        service = get_tasks_service()
        tasklist_id = get_default_tasklist_id(service)
        
        # 1. Get all tasks
        tasks = service.tasks().list(tasklist=tasklist_id, showCompleted=False).execute().get('items', [])
        if not tasks: return "No pending tasks to check."
        
        moved_count = 0
        now = datetime.utcnow().isoformat() + 'Z' # Current UTC time for comparison
        
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        target_iso = target_dt.isoformat() + 'Z'
        
        for t in tasks:
            due = t.get('due')
            if due and due < now: # If Due Date is in the past
                # Update it
                service.tasks().patch(tasklist=tasklist_id, task=t['id'], body={'due': target_iso}).execute()
                moved_count += 1
                
        if moved_count == 0:
            return "No overdue tasks found."
            
        return f"Success: Moved {moved_count} overdue tasks to {target_date}."

    except Exception as e: return f"Error: {e}"

# --- PROJECT TASKS (SQL) ---
# (These remain unchanged from previous versions, kept for compatibility)

def update_task_priority(task_id: int, new_priority: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tasks SET priority = ? WHERE id = ?", (new_priority, task_id))
        conn.commit()
        
        # Update Vector
        cursor.execute("SELECT title, status FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            text = f"Task: {row['title']}\nStatus: {row['status']}\nPriority: {new_priority}"
            update_vector_index(task_id, 'task', text)
            
        return f"Task {task_id} priority set to {new_priority}."
    except Exception as e: return f"Error: {e}"
    finally: conn.close()

def log_task_update(task_id: int, content: str, confidence_level: str = "Medium"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        created = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
            INSERT INTO task_updates (task_id, date, content, confidence_level, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, created, content, confidence_level, created))
        conn.commit()
        return f"Update logged for Task {task_id}."
    except Exception as e: return f"Error: {e}"
    finally: conn.close()

def get_task_history(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT date, content, confidence_level FROM task_updates WHERE task_id = ? ORDER BY created_at DESC", (task_id,))
        rows = cursor.fetchall()
        if not rows: return "No updates found for this task."
        return "\n".join([f"[{r['date']}] {r['content']} (Status: {r['confidence_level']})" for r in rows])
    finally: conn.close()