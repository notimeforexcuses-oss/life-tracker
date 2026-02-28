import json
from datetime import datetime
from modules.database_utils import get_db_connection

from modules.vector_utils import update_vector_index

# ==========================================
# 1. WORKOUTS
# ==========================================

def log_workout(type: str = "Weights", duration_min: int = 0, notes: str = ""):
    """
    Logs a workout session.
    Returns the workout_id to link exercises to.
    """
    conn = get_db_connection()
    now = datetime.now().isoformat()
    
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO workouts (start_datetime, type, duration_min, notes) 
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(sql, (now, type, duration_min, notes))
        conn.commit()
        workout_id = cursor.lastrowid
        print(f"Success: Started '{type}' Workout (ID: {workout_id}).")
        
        # Sync Vector Brain
        try:
            update_vector_index(workout_id, 'workout', f"Workout: {type}\nNotes: {notes}")
        except: pass

        return workout_id
    except Exception as e:
        print(f"Error logging workout: {e}")
        return None
    finally:
        conn.close()

def add_exercise(workout_id: int, name: str, sets: int = 0, reps: str = "0", weight: str = "0"):
    """
    Logs a specific exercise to a workout.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO exercises (workout_id, name, sets, reps, weight)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (workout_id, name, sets, reps, weight))
        conn.commit()
        exercise_id = cursor.lastrowid
        print(f"   + Added: {name} ({sets} x {reps} @ {weight})")

        # Sync Vector Brain
        try:
            update_vector_index(exercise_id, 'exercise', f"Exercise: {name}")
        except: pass

    except Exception as e:
        print(f"Error adding exercise: {e}")
    finally:
        conn.close()

# ==========================================

# 2. NUTRITION

# ==========================================



def log_nutrition(food_item: str, calories: int = 0, protein_g: int = 0, carbs_g: int = 0, fat_g: int = 0, 

                  fiber_g: int = 0, sugar_g: int = 0, sodium_mg: int = 0, cholesterol_mg: int = 0, meal_type: str = "Snack"):

    """

    Logs a single food entry including micro-nutrients.

    """

    conn = get_db_connection()

    today = datetime.now().strftime("%Y-%m-%d")

    

    try:

        cursor = conn.cursor()

        sql = """

            INSERT INTO nutrition_logs (date, food_item, calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg, cholesterol_mg, meal_type)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """

        cursor.execute(sql, (today, food_item, calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg, cholesterol_mg, meal_type))

        conn.commit()

        row_id = cursor.lastrowid

        print(f"Success: Logged '{food_item}' ({calories} kcal).")

        

        # Sync Vector Brain

        try:

            update_vector_index(row_id, 'nutrition', f"Nutrition: {food_item} ({calories} kcal)\nType: {meal_type}")

        except: pass



        return row_id

        

    except Exception as e:

        print(f"Error logging nutrition: {e}")

        return None

    finally:

        conn.close()



def save_meal_to_library(name: str, calories: int, protein: int = 0, carbs: int = 0, fat: int = 0, 

                         fiber: int = 0, sugar: int = 0, sodium: int = 0, cholesterol: int = 0, ingredients_list: list[str] = None):

    """

    Saves a recipe to the Meal Library for quick reuse.

    ingredients_list must be a list of strings.

    """

    if ingredients_list is None: ingredients_list = []

    ingredients_json = json.dumps(ingredients_list)

    

    conn = get_db_connection()

    try:

        cursor = conn.cursor()

        sql = """

            INSERT INTO meal_library (name, default_calories, default_protein, default_carbs, default_fat, 

                                      default_fiber, default_sugar, default_sodium, default_cholesterol, ingredients)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """

        cursor.execute(sql, (name, calories, protein, carbs, fat, fiber, sugar, sodium, cholesterol, ingredients_json))

        conn.commit()

        print(f"Success: Saved meal '{name}' to library.")

        return cursor.lastrowid

    except Exception as e:

        print(f"Error saving meal: {e}")

        return None

    finally:

        conn.close()



def search_meal_library(query: str):

    """

    Searches the Meal Library for saved recipes matching the query.

    Returns a list of matches with full nutritional data.

    """

    conn = get_db_connection()

    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    

    try:

        cursor = conn.cursor()

        sql = """

            SELECT * FROM meal_library 

            WHERE name LIKE ? OR ingredients LIKE ?

            ORDER BY name LIMIT 5

        """

        search_term = f"%{query}%"

        cursor.execute(sql, (search_term, search_term))

        results = cursor.fetchall()

        

        if not results:

            return "No meals found matching that query."

            

        return json.dumps(results, indent=2)

    except Exception as e:

        return f"Error searching meals: {e}"

    finally:

        conn.close()

def get_nutrition_logs(days: int = 60):
    """
    Retrieves nutrition logs for the last 'days' days.
    Returns a list of records including micro-nutrients.
    """
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    try:
        cursor = conn.cursor()
        sql = """
            SELECT * FROM nutrition_logs
            WHERE date >= date('now', '-' || ? || ' days')
            ORDER BY date DESC
        """
        cursor.execute(sql, (days,))
        results = cursor.fetchall()
        if not results:
            return f"No nutrition logs found for the last {days} days."
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error retrieving nutrition logs: {e}"
    finally:
        conn.close()

