import sqlite3
from datetime import datetime
from pathlib import Path
from modules.vector_utils import update_vector_index, delete_vector_index

# --- ROBUST PATH LOGIC ---
# Ensures we find the DB in the Project Root, regardless of where this script runs.
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
DB_PATH = project_root / 'brain.db'

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# --- WRITERS ---

def create_area(name: str):
    """Creates a new Area of Responsibility (e.g., Health, Finance)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Duplicate check
    cursor.execute("SELECT id FROM areas WHERE name = ?", (name,))
    if cursor.fetchone():
        conn.close()
        return f"Area '{name}' already exists."

    created = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO areas (name, created_at) VALUES (?, ?)", (name, created))
    aid = cursor.lastrowid
    conn.commit()
    conn.close()
    
    update_vector_index(aid, 'area', f"Area: {name}")
    return f"Area '{name}' created (ID: {aid})."

def move_goal_to_area(goal_id: int, area_id: int):
    """Moves an existing Goal into a specific Area."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate Area
    cursor.execute("SELECT name FROM areas WHERE id = ?", (area_id,))
    area = cursor.fetchone()
    if not area:
        conn.close()
        return f"Error: Area ID {area_id} not found."

    cursor.execute("UPDATE goals SET area_id = ? WHERE id = ?", (area_id, goal_id))
    if cursor.rowcount == 0:
        conn.close()
        return f"Error: Goal ID {goal_id} not found."
        
    conn.commit()
    conn.close()
    return f"Success: Goal {goal_id} moved to Area '{area['name']}'."

def add_goal(title: str, description: str = "", status: str = "ACTIVE", area_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM goals WHERE title = ?", (title,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return f"Goal '{title}' already exists (ID: {existing['id']})."

    created = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO goals (title, description, status, created_at, area_id) 
        VALUES (?, ?, ?, ?, ?)
    """, (title, description, status, created, area_id))
    
    goal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    update_vector_index(goal_id, 'goal', f"Goal: {title}\nDescription: {description}")
    return f"Goal '{title}' created (ID: {goal_id})."

def add_project(title: str, goal_id: int = None, description: str = "", status: str = "ACTIVE"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM projects WHERE title = ?", (title,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return f"Project '{title}' already exists (ID: {existing['id']})."

    created = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO projects (title, goal_id, description, status, created_at) VALUES (?, ?, ?, ?, ?)", 
                   (title, goal_id, description, status, created))
    
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    
    update_vector_index(pid, 'project', f"Project: {title}\nDescription: {description}")
    return f"Project '{title}' created (ID: {pid})."

def archive_project(project_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET status = 'ARCHIVED' WHERE id = ?", (project_id,))
    conn.commit()
    
    # Re-vector
    cursor.execute("SELECT title, description FROM projects WHERE id=?", (project_id,))
    row = cursor.fetchone()
    if row:
        text = f"Project: {row['title']}\nDescription: {row['description']}\nStatus: ARCHIVED"
        update_vector_index(project_id, 'project', text)
        
    conn.close()
    return f"Project {project_id} archived."

def add_project_task(title: str, project_id: int = None, due_date: str = None, 
                     linked_goal_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM tasks WHERE title = ? AND linked_project_id = ?", (title, project_id))
    if cursor.fetchone():
        conn.close()
        return f"Task '{title}' already exists for this project."

    created = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO tasks (title, status, due_date, created_at, linked_project_id, linked_goal_id)
        VALUES (?, 'PENDING', ?, ?, ?, ?)
    """, (title, due_date, created, project_id, linked_goal_id))
    
    tid = cursor.lastrowid
    conn.commit()
    conn.close()
    
    update_vector_index(tid, 'task', f"Task: {title}")
    return f"Task '{title}' added (ID: {tid})."

def delete_project_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    try: delete_vector_index(task_id, 'task')
    except: pass
    
    return f"Task {task_id} deleted."

# --- READERS ---

def list_areas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM areas ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "No Areas defined."
    return "\n".join([f"[ID: {r['id']}] {r['name']}" for r in rows])

def list_projects(status: str = "ACTIVE"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, status FROM projects WHERE status = ?", (status,))
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "No active projects."
    return "\n".join(sorted(list(set([f"[ID: {r['id']}] {r['title']}" for r in rows]))))

def get_project_details(project_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    proj = cursor.fetchone()
    if not proj: return "Project not found."
    
    report = [f"PROJECT: {proj['title']} (ID: {proj['id']})", f"Status: {proj['status']}", "-"*20]
    
    cursor.execute("SELECT id, title, status FROM tasks WHERE linked_project_id = ? AND status != 'COMPLETED'", (project_id,))
    tasks = cursor.fetchall()
    if tasks:
        report.append("\nOPEN TASKS:")
        for t in tasks: report.append(f"☐ {t['title']} (ID: {t['id']})")
        
    cursor.execute("SELECT id, title FROM notes WHERE linked_project_id = ?", (project_id,))
    notes = cursor.fetchall()
    if notes:
        report.append("\nLINKED NOTES:")
        for n in notes: report.append(f"- {n['title']} (ID: {n['id']})")

    cursor.execute("SELECT date, content FROM journal_entries WHERE linked_project_id = ? ORDER BY date DESC LIMIT 3", (project_id,))
    entries = cursor.fetchall()
    if entries:
        report.append("\nRECENT JOURNAL ENTRIES:")
        for e in entries: report.append(f"- {e['date']}: {e['content'][:50]}...")
        
    conn.close()
    return "\n".join(report)