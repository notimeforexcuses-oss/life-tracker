# modules/tools_update.py
from modules.database_utils import get_db_connection
from modules.vector_utils import update_vector_index

# Whitelist of allowed tables and columns to prevent accidental damage
ALLOWED_UPDATES = {
    "projects": ["title", "description", "status", "priority", "percent_complete", "due_date"],
    "tasks": ["title", "description", "status", "due_date", "priority"],
    "workouts": ["type", "duration_min", "notes"],
    "daily_metrics": ["sleep_hours", "morning_mood", "stress_level", "productivity_score", "win_of_the_day"],
    "contacts": ["name", "organization", "relationship", "email", "notes", "phone"],
    "timeline_blocks": ["activity", "start_datetime", "end_datetime"],
    "notes": ["title", "content", "tags"],
    "journal_entries": ["content", "tags"],
    "goals": ["title", "description", "status", "target_date"],
    "transactions": ["description", "amount", "category", "date", "status"],
    "areas": ["name"],
            "nutrition_logs": ["food_item", "meal_type", "calories"],
    "interactions": ["description", "interaction_type", "date"],
    "exercises": ["name", "category", "notes"],
    "nutrition_logs": ["food_item", "calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg", "cholesterol_mg", "meal_type"]
}

def update_record(table_name: str, record_id: int, field_name: str, new_value: str):
    """
    Updates a specific field in a specific record and syncs with vector index if needed.
    """
    # 1. Safety Checks
    if table_name not in ALLOWED_UPDATES:
        return f"Error: Updating table '{table_name}' is not allowed via this tool."
    
    if field_name not in ALLOWED_UPDATES[table_name]:
        return f"Error: Updating field '{field_name}' in '{table_name}' is restricted."

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 2. Check if record exists
        if table_name == 'daily_metrics':
            return "Error: Use specialized tools to update daily stats."
        
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if not row:
            return f"Error: Record ID {record_id} not found in {table_name}."

        # 3. Execute Update
        sql = f"UPDATE {table_name} SET {field_name} = ? WHERE id = ?"
        cursor.execute(sql, (new_value, record_id))
        conn.commit()
        
        # 4. Sync Vector Index if a semantic field changed
        # Define what triggers a re-index for each type
        semantic_triggers = {
            "notes": ["title", "content", "tags"],
            "journal_entries": ["content", "tags"],
            "projects": ["title", "description"],
            "goals": ["title", "description"],
            "tasks": ["title", "description"],
            "contacts": ["name", "notes", "organization"],
            "workouts": ["notes", "type"],
            "interactions": ["description"],
            "timeline_blocks": ["activity"],
            "exercises": ["name", "notes"],
            "transactions": ["description", "category"],
            "areas": ["name"],
            "nutrition_logs": ["food_item", "meal_type", "calories"]
        }
        
        if table_name in semantic_triggers and field_name in semantic_triggers[table_name]:
            # Fetch updated state
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
            updated_row = cursor.fetchone()
            
            # Construct text based on type (matching backfill logic)
            text = ""
            if table_name == 'notes':
                text = f"Title: {updated_row['title']}\nTags: {updated_row['tags']}\nContent: {updated_row['content']}"
            elif table_name == 'journal_entries':
                text = f"Journal: {updated_row['content']}\nTags: {updated_row['tags']}"
            elif table_name == 'projects':
                text = f"Project: {updated_row['title']}\nDescription: {updated_row['description']}"
            elif table_name == 'goals':
                text = f"Goal: {updated_row['title']}\nDescription: {updated_row['description']}"
            elif table_name == 'tasks':
                text = f"Task: {updated_row['title']}"
            elif table_name == 'contacts':
                text = f"Contact: {updated_row['name']}\nOrg: {updated_row['organization']}\nNotes: {updated_row['notes']}"
            elif table_name == 'workouts':
                text = f"Workout: {updated_row['type']}\nNotes: {updated_row['notes']}"
            elif table_name == 'interactions':
                text = f"Interaction: {updated_row['description']}"
            elif table_name == 'timeline_blocks':
                text = f"Timeline: {updated_row['activity']}"
            elif table_name == 'exercises':
                text = f"Exercise: {updated_row['name']}\nNotes: {updated_row['notes']}"
            elif table_name == 'transactions':
                text = f"Transaction: {updated_row['description']} ({updated_row['category']})"
            elif table_name == 'areas':
                text = f"Area: {updated_row['name']}"
            elif table_name == 'nutrition_logs':
                text = f"Nutrition: {updated_row['food_item']} ({updated_row['calories']} kcal)\nType: {updated_row['meal_type']}"
            
            if text:
                # Map table name to target_type if different
                target_type = table_name.rstrip('s') # projects -> project
                if table_name == 'journal_entries': target_type = 'journal'
                if table_name == 'areas': target_type = 'area'
                if table_name == 'nutrition_logs': target_type = 'nutrition'
                if table_name == 'timeline_blocks': target_type = 'timeline'
                
                update_vector_index(record_id, target_type, text)
        
        return f"Success: Updated {table_name} ID {record_id}. Set {field_name} = '{new_value}'."
        
    except Exception as e:
        return f"Update Error: {e}"
    finally:
        conn.close()



