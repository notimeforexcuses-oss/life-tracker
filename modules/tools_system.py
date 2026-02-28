import sqlite3
import re
from datetime import datetime
from modules.database_utils import get_db_connection
from modules.vector_utils import get_vector_stats, backfill_vectors, delete_vector_index

# ==========================================
# 0. GOVERNANCE POLICY
# ==========================================

# Tier 1: Safe to execute autonomously in the background.
# Tier 2: Requires human approval (via propose_automation).
AUTONOMY_POLICY = {
    # MAINTENANCE & MAINTENANCE
    "manage_vectors": 1,
    "run_safe_query": 1,
    "add_system_notification": 1,
    "propose_automation": 1,
    "update_record": 1,
    
    # ENRICHMENT & RESEARCH
    "search_web": 1,
    "read_website": 1,
    "add_note": 1,
    "add_memory": 1,
    "retrieve_memories": 1,
    "link_items": 1,
    "search_knowledge_base": 1,
    "read_note": 1,
    "analyze_note_attachment": 1,
    "read_doc": 1,
    "read_sheet": 1,
    
    # LOGGING (Additive only)
    "log_morning_metrics": 1,
    "log_evening_metrics": 1,
    "log_flexible_data": 1,
    "add_journal_entry": 1,
    "add_timeline_block": 1,
    "log_focus": 1,
    "log_workout": 1,
    "add_exercise": 1,
    "log_nutrition": 1,
    
    # READ-ONLY
    "list_areas": 1,
    "list_projects": 1,
    "get_project_details": 1,
    "list_google_tasks": 1,
    "get_task_history": 1,
    "search_contacts": 1,
    "get_contact_details": 1,
    "check_budget_status": 1,
    "list_calendar_events": 1,
    "fetch_unread_emails": 1,
    
    # --- TIER 2: SENSITIVE (RESTRICTED) ---
    "add_transaction": 2,
    "transfer_budget": 2,
    "send_email": 2,
    "delete_record": 2,
    "create_area": 2,
    "add_goal": 2,
    "add_project": 2,
    "add_google_task": 2,
    "update_google_task": 2,
    "complete_google_task": 2,
    "delete_google_task": 2,
    "add_calendar_event": 2,
    "update_calendar_event": 2,
    "delete_calendar_event": 2,
    "create_doc": 2,
    "create_sheet": 2,
    "delete_drive_file": 2,
    "archive_project": 2 # Archiving is safer than deleting but still a state change
}

# ==========================================
# 3. MAINTENANCE TOOLS
# ==========================================

def manage_vectors(action: str, target_id: int = None, target_type: str = None):
    """
    Manages the Semantic Vector Index.
    action: 'stats' (view coverage), 'backfill' (index pending items), 'delete' (remove an index).
    """
    if action == 'stats':
        return get_vector_stats()
    
    elif action == 'backfill':
        return backfill_vectors(limit=50) # Safe batch size
        
    elif action == 'delete':
        if not target_id or not target_type:
            return "Error: 'delete' requires target_id and target_type."
        return delete_vector_index(target_id, target_type)
        
    return f"Error: Unknown action '{action}'. Use 'stats', 'backfill', or 'delete'."

def delete_record(table_name: str, record_id: int):
    """
    Deletes a record from the database and its corresponding semantic vector.
    """
    # Safety Whitelist
    ALLOWED_DELETES = [
        "notes", "journal_entries", "tasks", "goals", "projects", 
        "contacts", "interactions", "workouts", "nutrition_logs",
        "transactions", "proposed_automations", "timeline_blocks", "areas",
        "exercises"
    ]
    
    if table_name not in ALLOWED_DELETES:
        return f"Error: Deletion of table '{table_name}' is not permitted via this tool."

    # 1. Integrity Check for Areas
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if table_name == 'areas':
            # Check for linked goals
            cursor.execute("SELECT COUNT(*) FROM goals WHERE area_id = ?", (record_id,))
            goal_count = cursor.fetchone()[0]
            if goal_count > 0:
                return f"Error: Cannot delete Area ID {record_id}. It contains {goal_count} linked Goal(s). Please reassign or delete the goals first."
    except Exception as integrity_err:
        return f"Integrity Check Error: {integrity_err}"
    finally:
        conn.close()

    # 2. First, delete the vector (External tool with its own connection)
    # This prevents the main transaction from being held open while the vector tool runs.
    target_type = table_name.rstrip('s') 
    if table_name == 'journal_entries': target_type = 'journal'
    if table_name == 'areas': target_type = 'area'
    if table_name == 'timeline_blocks': target_type = 'timeline'
    
    try:
        delete_vector_index(record_id, target_type)
    except Exception as v_err:
        print(f"Warning: Could not delete vector index: {v_err}")

    # 3. Now perform the database deletion
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if record exists
        cursor.execute(f"SELECT id FROM {table_name} WHERE id = ?", (record_id,))
        if not cursor.fetchone():
            return f"Error: Record {record_id} not found in {table_name}."

        # Delete Record
        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        conn.commit()
        return f"Success: Deleted {table_name} ID {record_id} and its semantic index."
        
    except Exception as e:
        return f"Delete Error: {e}"
    finally:
        conn.close()

# ==========================================
# 1. LEGISLATIVE TOOLS (Shared by Agent & Daemon)
# ==========================================

def propose_automation(trigger_condition: str, proposed_action: str, recurrence: str = "ONE_TIME", intended_tool: str = None):
    """
    Proposes a new background rule or automation. 
    Tier 1 tools are auto-approved to reduce friction.
    intended_tool: The name of the tool this rule aims to run (e.g., 'manage_vectors').
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        created = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Determine Status based on Governance Policy
        status = 'PENDING'
        auto_notif = False
        
        if intended_tool and AUTONOMY_POLICY.get(intended_tool) == 1:
            status = 'APPROVED'
            auto_notif = True
            
        cursor.execute("""
            INSERT INTO proposed_automations (trigger_condition, proposed_action, recurrence, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (trigger_condition, proposed_action, recurrence, status, created))
        
        conn.commit()
        
        if auto_notif:
            # We import here to avoid circular dependencies
            # (Assuming add_system_notification exists in this file or similar context)
            # Since add_system_notification is actually usually added via brain_daemon wrapper,
            # we'll post it directly to the DB here for dashboard visibility.
            cursor.execute("""
                INSERT INTO system_notifications (type, content, severity, created_at)
                VALUES ('Insight', ?, 'Info', ?)
            """, (f"Autonomous Rule Activated: {proposed_action}", created))
            conn.commit()
            return f"Automation Activated: '{proposed_action}' was auto-approved per Tier 1 safety policy."
            
        return f"Proposal saved. The user must approve '{proposed_action}' in the Dashboard."
    except Exception as e:
        return f"Error proposing automation: {e}"
    finally:
        conn.close()

# ==========================================
# 2. ANALYTICAL TOOLS (Safe Querying)
# ==========================================

def run_safe_query(sql_query: str):
    """
    Runs a READ-ONLY SQL query to answer complex questions.
    RESTRICTION: Only SELECT statements are allowed. No modifications.
    """
    # 1. Safety Filter
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE"]
    if any(word in sql_query.upper() for word in forbidden):
        return "Error: Unsafe query detected. Only SELECT statements are allowed."
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        if not rows: return "Query executed. No results found."
        
        # Format results nicely
        # Get column names
        col_names = [description[0] for description in cursor.description]
        output = [f"Found {len(rows)} results:"]
        
        # Limit output to prevent flooding context window
        if len(rows) > 20: 
            output.append("(Showing first 20 rows only)")
            rows = rows[:20]
            
        for row in rows:
            # Convert row to dict-like string for readability
            row_dict = {col_names[i]: row[i] for i in range(len(col_names))}
            output.append(str(row_dict))
            
        return "\n".join(output)
        
    except Exception as e:
        return f"Query Error: {e}"
    finally:
        conn.close()