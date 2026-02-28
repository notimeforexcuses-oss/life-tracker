import sqlite3
import json
import os
import sys
from modules.database_utils import get_db_connection

def validate_json(text):
    if not text: return True
    try:
        json.loads(text)
        return True
    except:
        return False

def check_broken_links(cursor, table_name, link_col, ref_table):
    issues = []
    try:
        query = f"""
            SELECT id, {link_col} FROM {table_name} 
            WHERE {link_col} IS NOT NULL 
            AND {link_col} NOT IN (SELECT id FROM {ref_table})
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for r in rows:
            issues.append(f"[{table_name.upper()}] ID {r[0]}: Links to non-existent {ref_table[:-1]} (ID {r[1]}).")
    except:
        pass
    return issues

def perform_audit_range(days_back: int = 30):
    conn = get_db_connection()
    issues = []
    
    try:
        cursor = conn.cursor()
        
        # 1. JSON INTEGRITY
        cursor.execute("SELECT id, content, tags FROM memories")
        for m in cursor.fetchall():
            if not validate_json(m[2]): issues.append(f"[MEMORY] ID {m[0]}: Invalid JSON tags.")

        cursor.execute("SELECT id, title, tags FROM notes")
        for n in cursor.fetchall():
            if not validate_json(n[2]): issues.append(f"[NOTE] ID {n[0]}: Invalid JSON tags.")
        
        # 2. BROKEN LINK DETECTION (Updated for V3)
        # Core
        issues.extend(check_broken_links(cursor, "notes", "linked_project_id", "projects"))
        issues.extend(check_broken_links(cursor, "notes", "linked_goal_id", "goals"))
        issues.extend(check_broken_links(cursor, "tasks", "linked_project_id", "projects"))
        issues.extend(check_broken_links(cursor, "interactions", "contact_id", "contacts"))
        # V2 (Finance/Tasks)
        issues.extend(check_broken_links(cursor, "budgets", "linked_project_id", "projects"))
        issues.extend(check_broken_links(cursor, "task_updates", "task_id", "tasks"))
        # V3 (Focus)
        issues.extend(check_broken_links(cursor, "focus_logs", "linked_project_id", "projects"))

        # 3. HEALTH CHECK
        try:
            cursor.execute("""
                SELECT date, sleep_hours, sleep_deep_min, readiness_score 
                FROM daily_metrics 
                WHERE type='Morning' OR (sleep_hours IS NOT NULL AND type IS NULL)
                ORDER BY date DESC LIMIT 7
            """)
            metrics = cursor.fetchall()
            for m in metrics:
                if m[1] is None: issues.append(f"[METRICS] {m[0]}: Missing Sleep Hours.")
                if m[2] == 0 or m[2] is None: issues.append(f"[METRICS] {m[0]}: Missing Sleep Phase Detail (Deep Sleep).")
        except: pass

        if not issues:
            return "Audit Complete: System Nominal. No broken links."
        else:
            return "Audit Complete. Issues Found:\n" + "\n".join(issues)

    except Exception as e:
        return f"Audit Failed: {e}"
    finally:
        conn.close()