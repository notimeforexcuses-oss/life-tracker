import sqlite3
import datetime
from pathlib import Path
from .tools_calendar import list_calendar_events, add_calendar_event

# --- DATABASE CONNECTION ---
def get_db_connection():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    db_path = project_root / 'brain.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def get_day_schedule(date_str):
    """
    Returns a merged list of:
    1. Google Calendar Events (Real)
    2. Local Tasks scheduled for this day
    Sorted by start time.
    """
    schedule_items = []
    
    # 1. Fetch Local Scheduled Tasks
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, scheduled_start, estimated_duration, status 
        FROM tasks 
        WHERE scheduled_start LIKE ? AND status != 'COMPLETED'
    """, (f"{date_str}%",))
    
    tasks = cursor.fetchall()
    conn.close()
    
    for t in tasks:
        # Convert to unified structure
        start_time_obj = datetime.datetime.strptime(t['scheduled_start'], "%Y-%m-%d %H:%M")
        schedule_items.append({
            'type': 'task',
            'id': t['id'],
            'title': t['title'],
            'start_time': start_time_obj.strftime("%H:%M"),
            'sort_key': start_time_obj,
            'duration': t['estimated_duration'] or 30,
            'status': t['status']
        })

    # 2. Fetch Google Calendar Events (If available)
    # Note: list_calendar_events returns a string list, we need raw data.
    # We'll use a safer approach: try the API, fallback gracefully.
    try:
        from .tools_calendar import get_calendar_service
        service = get_calendar_service()
        if service:
            # Parse date for API
            start_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            end_dt = start_dt + datetime.timedelta(days=1)
            
            events_result = service.events().list(
                calendarId='primary', 
                timeMin=start_dt.isoformat() + 'Z',
                timeMax=end_dt.isoformat() + 'Z', 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            for event in events_result.get('items', []):
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Handle all-day events (YYYY-MM-DD) vs timed (ISO)
                if 'T' in start:
                    dt_obj = datetime.datetime.fromisoformat(start)
                    time_str = dt_obj.strftime("%H:%M")
                else:
                    dt_obj = datetime.datetime.strptime(start, "%Y-%m-%d")
                    time_str = "All Day"
                
                schedule_items.append({
                    'type': 'event',
                    'id': event['id'],
                    'title': event.get('summary', '(No Title)'),
                    'start_time': time_str,
                    'sort_key': dt_obj,
                    'duration': 60, # Placeholder
                    'status': 'confirmed'
                })
    except Exception as e:
        print(f"Calendar fetch error: {e}")

    # 3. Sort by Time
    schedule_items.sort(key=lambda x: x['sort_key'])
    return schedule_items

def get_unscheduled_tasks():
    """Returns tasks that are PENDING and have NO scheduled_start."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, priority, due_date, estimated_duration 
        FROM tasks 
        WHERE status='PENDING' AND (scheduled_start IS NULL OR scheduled_start = '')
        ORDER BY 
            CASE WHEN due_date = date('now') THEN 0 ELSE 1 END,
            priority DESC
    """)
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

def schedule_task_block(task_id, date_str, time_str, duration):
    """Updates a task with a scheduled start time."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    full_start = f"{date_str} {time_str}"
    
    cursor.execute("""
        UPDATE tasks 
        SET scheduled_start = ?, estimated_duration = ?
        WHERE id = ?
    """, (full_start, duration, task_id))
    
    conn.commit()
    conn.close()
    return True

def unschedule_task_block(task_id):
    """Removes a task from the schedule (back to Inbox)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET scheduled_start = NULL WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return True
