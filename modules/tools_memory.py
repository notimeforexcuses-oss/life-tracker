import sys
import os
import sqlite3
import json
from datetime import datetime

# Path Fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.database_utils import get_db_connection

# ==========================================
# 1. CORE MEMORY FUNCTIONS
# ==========================================

def add_memory(category: str, content: str, tags: str = "[]"):
    """
    Saves a persistent memory about the user.
    category: 'preference', 'fact', 'rule'
    tags: JSON list string, e.g. '["food", "health"]'
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Validate JSON
        try:
            json.loads(tags)
        except:
            tags = "[]"
        
        # Duplicate check (Table name: memories)
        cursor.execute("SELECT id FROM memories WHERE content = ?", (content,))
        if cursor.fetchone():
            return "Memory already exists."

        cursor.execute("""
            INSERT INTO memories (category, content, tags, created_at)
            VALUES (?, ?, ?, ?)
        """, (category, content, tags, now))
        conn.commit()
        return f"Memory stored: [{category}] {content} (Tags: {tags})"
    except Exception as e:
        return f"Error storing memory: {e}"
    finally:
        conn.close()

def retrieve_memories(filter_tag: str = None, limit: int = 10):
    """
    Retrieves active memories. 
    filter_tag: Optional keyword to filter by (e.g., 'food' will find tags containing 'food').
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if filter_tag:
            term = f"%{filter_tag}%"
            # Table name: memories
            cursor.execute("""
                SELECT category, content, tags FROM memories 
                WHERE tags LIKE ? OR category LIKE ? OR content LIKE ?
                ORDER BY created_at DESC LIMIT ?
            """, (term, term, term, limit))
        else:
            # Table name: memories
            cursor.execute("SELECT category, content, tags FROM memories ORDER BY created_at DESC LIMIT ?", (limit,))
        
        rows = cursor.fetchall()
        if not rows: return "No memories found."
        
        return "\n".join([f"- [{r[0].upper()}] {r[1]} (Tags: {r[2]})" for r in rows])
    except Exception as e:
        return f"Error retrieving memories: {e}"
    finally:
        conn.close()

# ==========================================
# 2. CONVERSATION ARCHIVING
# ==========================================

def flush_chat_context(chat_history: str):
    """
    Saves the current conversation text to Google Drive and returns a success message.
    Used to clear the AI's 'Working Memory' while preserving the record.
    """
    # Import inside function to avoid circular dependency issues
    from modules.tools_backup import get_drive_service, find_or_create_folder
    from googleapiclient.http import MediaIoBaseUpload
    import io

    ARCHIVE_FOLDER = "Chat_Archives"
    
    try:
        service = get_drive_service()
        folder_id = find_or_create_folder(service, ARCHIVE_FOLDER)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"Chat_{timestamp}.txt"
        
        # Create a file stream in memory (no disk write needed)
        file_stream = io.BytesIO(chat_history.encode('utf-8'))
        media = MediaIoBaseUpload(file_stream, mimetype='text/plain')
        
        file_metadata = {'name': filename, 'parents': [folder_id]}
        
        service.files().create(body=file_metadata, media_body=media).execute()
        
        return "Chat History Archived. You may now clear the window."
        
    except Exception as e:
        return f"Archive Error: {e}"

# ==========================================
# 3. POLYMORPHIC LINKING
# ==========================================

def link_items(source_id: int, source_type: str, target_id: int, target_type: str):
    """
    Creates a polymorphic link between any two items in the system.
    Valid types: 'note', 'journal', 'project', 'goal', 'contact', 'interaction', 'task'
    """
    valid_types = ['note', 'journal', 'project', 'goal', 'contact', 'interaction', 'task']
    if source_type not in valid_types or target_type not in valid_types:
        return f"Error: Invalid type. Must be one of {valid_types}"

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if link exists
        cursor.execute("""
            SELECT id FROM memory_links 
            WHERE source_id = ? AND source_type = ? AND target_id = ? AND target_type = ?
        """, (source_id, source_type, target_id, target_type))
        
        if cursor.fetchone():
            return "Link already exists."

        cursor.execute("""
            INSERT INTO memory_links (source_id, source_type, target_id, target_type, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (source_id, source_type, target_id, target_type))
        
        conn.commit()
        return f"Successfully linked {source_type} #{source_id} to {target_type} #{target_id}."
        
    except Exception as e:
        return f"Error creating link: {e}"
    finally:
        conn.close()