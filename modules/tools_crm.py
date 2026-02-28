import sqlite3
from datetime import datetime
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

# --- WRITERS ---

def add_contact(name: str, relationship: str, email: str = "", phone: str = "", notes: str = "", 
                organization: str = "", job_title: str = "", next_contact_date: str = "", linkedin_url: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT id FROM contacts WHERE name = ?", (name,))
    if cursor.fetchone():
        conn.close()
        return f"Contact '{name}' already exists."

    cursor.execute("""
        INSERT INTO contacts (name, relationship, email, phone, notes, organization, job_title, next_contact_date, linkedin_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, relationship, email, phone, notes, organization, job_title, next_contact_date, linkedin_url, date_str))
    
    contact_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    update_vector_index(contact_id, 'contact', f"Contact: {name}\nOrg: {organization}\nNotes: {notes}")
    return f"Contact {name} added (ID: {contact_id})."

def add_contact_detail(contact_id: int, type: str, value: str, label: str = "Work"):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS contact_details (id INTEGER PRIMARY KEY, contact_id INTEGER, type TEXT, value TEXT, label TEXT)")
        
        cursor.execute("SELECT id FROM contact_details WHERE contact_id = ? AND value = ?", (contact_id, value))
        if cursor.fetchone():
             return f"Detail '{value}' already exists for this contact."
             
        cursor.execute("INSERT INTO contact_details (contact_id, type, value, label) VALUES (?, ?, ?, ?)", 
                       (contact_id, type, value, label))
        conn.commit()
        return f"Added {type}: {value} to Contact ID {contact_id}."
    except Exception as e:
        return f"Error adding detail: {e}"
    finally:
        conn.close()

def log_interaction(contact_id: int, type: str, notes: str, 
                    linked_project_id: Optional[int] = None, linked_goal_id: Optional[int] = None):
    """
    Logs an interaction with a contact.
    IDs are Optional[int] to allow general networking logs.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT id FROM interactions 
        WHERE contact_id = ? AND notes = ? AND date = ?
    """, (contact_id, notes, date_str))
    
    if cursor.fetchone():
        conn.close()
        return f"Interaction already logged for today."

    cursor.execute("""
        INSERT INTO interactions (date, contact_id, type, notes, linked_project_id, linked_goal_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, contact_id, type, notes, linked_project_id, linked_goal_id))
    
    interaction_id = cursor.lastrowid
    cursor.execute("UPDATE contacts SET last_contact_date = ? WHERE id = ?", (date_str, contact_id))
    
    conn.commit()
    conn.close()
    
    update_vector_index(interaction_id, 'interaction', f"Interaction: {type}\nNotes: {notes}")
    return f"Interaction logged for Contact ID {contact_id}."

# --- READERS ---

def search_contacts(name_query: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, relationship, organization FROM contacts WHERE name LIKE ?", (f"%{name_query}%",))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows: return "No contacts found."
    return "\n".join([f"[ID: {r['id']}] {r['name']} ({r['organization'] or 'No Org'}) - {r['relationship']}" for r in rows])

def get_contact_details(contact_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
    c = cursor.fetchone()
    if not c: return "Contact not found."
    
    report = [f"CONTACT: {c['name']} (ID: {c['id']})", 
              f"Org: {c['organization']} ({c['job_title'] or 'No Title'})", 
              f"Rel: {c['relationship']}", 
              f"Next Contact: {c['next_contact_date'] or 'Not Scheduled'}",
              f"LinkedIn: {c['linkedin_url'] or 'Not provided'}",
              f"Notes: {c['notes']}", "-"*20]
    
    try:
        cursor.execute("SELECT type, value, label FROM contact_details WHERE contact_id = ?", (contact_id,))
        details = cursor.fetchall()
        for d in details: report.append(f"{d['type']} ({d['label']}): {d['value']}")
    except: pass 
    
    cursor.execute("SELECT DISTINCT date, type, notes FROM interactions WHERE contact_id = ? ORDER BY date DESC LIMIT 5", (contact_id,))
    interactions = cursor.fetchall()
    if interactions:
        report.append("\nRECENT INTERACTIONS:")
        for i in interactions: report.append(f"- {i['date']} [{i['type']}]: {i['notes']}")
        
    conn.close()
    return "\n".join(report)