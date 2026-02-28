import sqlite3
from pathlib import Path

def check_tables():
    DB_PATH = Path('brain.db')
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("Existing Tables:")
    for t in tables:
        print(f"- {t}")
    conn.close()

if __name__ == "__main__":
    check_tables()
