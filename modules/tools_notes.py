import sqlite3
import os
from datetime import datetime
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from modules.vector_utils import update_vector_index, search_vectors

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# --- ROBUST PATH LOGIC ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
DB_FILE = project_root / 'brain.db'

def get_db_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def add_note(title: str, content: str, tags: str = "", 
             linked_project_id: Optional[int] = None, linked_goal_id: Optional[int] = None, 
             linked_contact_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM notes WHERE title = ? AND content = ?", (title, content))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return f"Note already exists (ID: {existing['id']})."

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    cursor.execute("""
        INSERT INTO notes 
        (title, content, tags, created_at, linked_project_id, linked_goal_id, linked_contact_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, content, tags, created_at, linked_project_id, linked_goal_id, linked_contact_id))
    
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Update Vector Index
    full_text = f"Title: {title}\nTags: {tags}\nContent: {content}"
    update_vector_index(note_id, 'note', full_text)
    
    return f"Note '{title}' saved (ID: {note_id})."

def search_knowledge_base(query: str, target_type: Optional[str] = None):
    """
    Performs a UNIVERSAL HYBRID search across Notes, Tasks, Journals, Projects, Goals, and Contacts.
    Combines SQL Keyword search (for Notes) with Semantic Vector search (for Everything).
    target_type: Optional filter (e.g., 'task', 'note', 'journal').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. SQL Search (Notes Primary - exact text match)
    # Only run SQL search if no target_type is specified or if target_type is 'note'
    note_rows = []
    if not target_type or target_type == 'note':
        cursor.execute("SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?", 
                       (f'%{query}%', f'%{query}%', f'%{query}%'))
        note_rows = cursor.fetchall()
    
    # 2. Vector Search (Universal or Filtered - concept match)
    # We use a min_score of 0.4 to filter out low-relevance matches
    vector_results = search_vectors(query, target_type=target_type, limit=15, min_score=0.4) 
    
    output = []
    seen_ids = set() # Set of (type, id) tuples
    
    # Process SQL Note Matches
    for row in note_rows:
        seen_ids.add(('note', row['id']))
        # Fetch attachments
        cursor.execute("SELECT id, file_name FROM note_attachments WHERE note_id = ?", (row['id'],))
        atts = cursor.fetchall()
        att_str = ""
        if atts:
            att_list = [f"{a['file_name']} (ID: {a['id']})" for a in atts]
            att_str = f" [Attachments: {', '.join(att_list)}]"
            
        output.append(f"[NOTE:{row['id']}] {row['title']} (Tags: {row['tags']}){att_str}")

    # Process Vector Matches (Universal)
    for res in vector_results:
        rtype = res['type']
        rid = res['id']
        if (rtype, rid) in seen_ids: continue
        
        seen_ids.add((rtype, rid))
        
        try:
            # Fetch details based on type
            if rtype == 'note':
                cursor.execute("SELECT title, tags FROM notes WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[NOTE:{rid}] {row['title']} (Tags: {row['tags']}) (Semantic)")
                
            elif rtype == 'task':
                cursor.execute("SELECT title, status FROM tasks WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[TASK:{rid}] {row['title']} ({row['status']}) (Semantic)")
                
            elif rtype == 'journal':
                cursor.execute("SELECT date, content FROM journal_entries WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[JOURNAL:{rid}] {row['date']}: {row['content'][:50]}... (Semantic)")
                
            elif rtype == 'project':
                cursor.execute("SELECT title, status FROM projects WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[PROJECT:{rid}] {row['title']} ({row['status']}) (Semantic)")
                
            elif rtype == 'goal':
                cursor.execute("SELECT title, status FROM goals WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[GOAL:{rid}] {row['title']} ({row['status']}) (Semantic)")
                
            elif rtype == 'contact':
                cursor.execute("SELECT name, organization FROM contacts WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[CONTACT:{rid}] {row['name']} ({row['organization']}) (Semantic)")

            elif rtype == 'nutrition':
                cursor.execute("SELECT food_item, calories, date FROM nutrition_logs WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[NUTRITION:{rid}] {row['date']}: {row['food_item']} ({row['calories']} kcal) (Semantic)")

            elif rtype == 'workout':
                cursor.execute("SELECT start_datetime, type FROM workouts WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: 
                    date_val = row['start_datetime'].split('T')[0] if 'T' in row['start_datetime'] else row['start_datetime']
                    output.append(f"[WORKOUT:{rid}] {date_val}: {row['type']} (Semantic)")

            elif rtype == 'exercise':
                cursor.execute("SELECT name FROM exercises WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row: output.append(f"[EXERCISE:{rid}] {row['name']} (Semantic)")

            elif rtype == 'timeline':
                cursor.execute("SELECT activity, start_datetime FROM timeline_blocks WHERE id=?", (rid,))
                row = cursor.fetchone()
                if row:
                    date_val = row['start_datetime'].split('T')[0] if 'T' in row['start_datetime'] else row['start_datetime']
                    output.append(f"[TIMELINE:{rid}] {date_val}: {row['activity']} (Semantic)")
        except:
            continue

    conn.close()
    
    if not output: return "No knowledge found."
    return "\n".join(sorted(output))

def read_note(note_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    
    if not row: 
        conn.close()
        return "Note not found."
        
    # Fetch attachments
    cursor.execute("SELECT id, file_name, uploaded_at FROM note_attachments WHERE note_id = ?", (note_id,))
    atts = cursor.fetchall()
    att_str = ""
    if atts:
        att_lines = ["\nAttachments:"]
        for a in atts:
            att_lines.append(f"- ID: {a['id']  } | {a['file_name']} (Uploaded: {a['uploaded_at']})")
        att_str = "\n".join(att_lines)

    conn.close()
    return f"Title: {row['title']}\nContent:\n{row['content']}\nTags: {row['tags']}{att_str}"

def analyze_note_attachment(attachment_id: int, query: str):
    """
    Analyzes an attached file using AI vision/document understanding.
    """
    if not API_KEY:
        return "Error: GEMINI_API_KEY not set."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, file_name FROM note_attachments WHERE id = ?", (attachment_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "Attachment not found."

    # Convert web path to local path
    # DB: /media/attachments/...
    # Local: second_brain_web/media/attachments/...
    rel_path = row['file_path'].lstrip('/') # media/attachments/...
    if rel_path.startswith('media/'):
        rel_path = rel_path[6:] # attachments/...
        
    local_path = os.path.join("second_brain_web", "media", rel_path)
    
    if not os.path.exists(local_path):
        return f"Error: File not found on disk at {local_path}"

    try:
        client = genai.Client(api_key=API_KEY)
        
        # Upload file
        file_ref = client.files.upload(path=local_path)
        
        # Generate analysis
        # Using gemini-2.0-flash as a fast, multimodal capable model
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[file_ref, query]
        )
        
        return f"Analysis of {row['file_name']}:\n{response.text}"

    except Exception as e:
        return f"AI Analysis Failed: {str(e)}"