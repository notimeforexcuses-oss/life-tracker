# modules/tools_timeline.py
from datetime import datetime, timedelta
from modules.database_utils import get_db_connection
from modules.vector_utils import update_vector_index

def add_timeline_block(activity: str, duration_mins: int = 60, 

                       workout_id: int = None, project_id: int = None, 

                       task_id: int = None, interaction_id: int = None,

                       start_time_override: str = None):

    """

    Creates a 'Time Block' representing time spent.

    Links to specific activities (Workout, Project, Meeting) for auditing.

    """

    conn = get_db_connection()

    

    # Time calculation

    if start_time_override:

        try:

            # Expecting ISO format or YYYY-MM-DD HH:MM

            if 'T' in start_time_override:

                start_dt = datetime.fromisoformat(start_time_override)

            else:

                start_dt = datetime.strptime(start_time_override, "%Y-%m-%d %H:%M")

        except:

            start_dt = datetime.now()

    else:

        start_dt = datetime.now()

        

    end_dt = start_dt + timedelta(minutes=duration_mins)

    

    try:

        cursor = conn.cursor()

        sql = """

            INSERT INTO timeline_blocks 

            (activity, start_datetime, end_datetime, workout_id, project_id, task_id, interaction_id)

            VALUES (?, ?, ?, ?, ?, ?, ?)

        """

        cursor.execute(sql, (activity, start_dt.isoformat(), end_dt.isoformat(), 

                             workout_id, project_id, task_id, interaction_id))

        conn.commit()

        block_id = cursor.lastrowid

        print(f"Success: Timeline Block '{activity}' ({duration_mins} min) created.")

        

        # --- ENHANCED VECTOR INDEXING ---

        context_str = ""

        try:

            if project_id:

                cursor.execute("SELECT title FROM projects WHERE id = ?", (project_id,))

                row = cursor.fetchone()

                if row: context_str += f" | Project: {row['title']}"

            if task_id:

                cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))

                row = cursor.fetchone()

                if row: context_str += f" | Task: {row['title']}"

            if workout_id:

                cursor.execute("SELECT type FROM workouts WHERE id = ?", (workout_id,))

                row = cursor.fetchone()

                if row: context_str += f" | Workout: {row['type']}"

        except: pass



        # Sync Vector Brain

        try:

            full_text = f"Timeline: {activity}{context_str}"

            update_vector_index(block_id, 'timeline', full_text)

        except Exception as v_err:

            print(f"   [Vector Warning] Timeline sync failed: {v_err}")



        return block_id

    except Exception as e:

        print(f"Error creating timeline block: {e}")

        return None

    finally:

        conn.close()
