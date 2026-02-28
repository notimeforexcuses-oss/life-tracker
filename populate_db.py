import sqlite3
import re
from datetime import datetime

DB_PATH = 'brain.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def clear_database():
    print("🗑️ Clearing existing data...")
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = [
        'areas', 'goals', 'projects', 'tasks', 'contacts', 'journal_entries', 'notes',
        'interactions', 'daily_metrics', 'workouts', 'exercises', 'nutrition_logs',
        'timeline_blocks', 'task_updates', 'budgets', 'transactions', 'resources',
        'chat_sessions', 'chat_messages', 'proposed_automations', 'flexible_tracker', 
        'memory_links', 'project_stakeholders', 'goal_participants', 'task_assignees'
    ]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()

def parse_and_populate():
    with open('data_outline.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. AREAS
    print("🌱 Populating Areas...")
    area_section_match = re.search(r'## 1. AREAS \(7\)\n+(.*?)\n---', content, re.S)
    if area_section_match:
        area_section = area_section_match.group(1)
        areas = re.findall(r'\d+\.\s+(.*)', area_section)
        for a in areas:
            cursor.execute("INSERT INTO areas (name, created_at) VALUES (?, ?)", (a.strip(), today_str))

    # 2. GOALS & PROJECTS & TASKS
    print("🌱 Populating Goals, Projects, and Tasks...")
    area_blocks = re.findall(r'### AREA \d+:\s+(.*?)\n(.*?)(?=\n### AREA|\n---)', content, re.S)
    area_id = 1
    for a_name, a_content in area_blocks:
        goal_blocks = re.findall(r'\*\s+\*\*Goal ([\d\.]+):\s+(.*?)\*\*\n\s+\*\s+\*Importance:\*\s+(.*?)\n(.*?)(?=\n\*\s+\*\*Goal|\Z)', a_content, re.S)
        for g_idx, g_title, g_imp, g_content in goal_blocks:
            cursor.execute("INSERT INTO goals (area_id, title, description, status, motivation, created_at) VALUES (?, ?, ?, 'ACTIVE', ?, ?)",
                           (area_id, g_title.strip(), g_imp.strip(), g_imp.strip(), today_str))
            goal_id = cursor.lastrowid
            
            project_blocks = re.findall(r'\s+\*\s+\*\*Project ([\d\.]+):\s+(.*?)\*\*\n\s+\*\s+\*Scope:\*\s+(.*?)\n\s+\*\s+\*Priority:\*\s+(.*?)\n(.*?)(?=\n\s+\*\s+\*\*Project|\Z)', g_content, re.S)
            for p_idx, p_title, p_scope, p_prio, p_content in project_blocks:
                cursor.execute("INSERT INTO projects (goal_id, title, description, status, priority, percent_complete, created_at) VALUES (?, ?, ?, 'ACTIVE', ?, 0, ?)",
                               (goal_id, p_title.strip(), p_scope.strip(), p_prio.strip(), today_str))
                project_id = cursor.lastrowid
                
                tasks = re.findall(r'Task ([\d\.]+):\s+(.*?)\s+\(Due:\s+(.*?),\s+(.*?)\)', p_content)
                for t_idx, t_title, t_due, t_prio in tasks:
                    cursor.execute("INSERT INTO tasks (linked_project_id, title, status, due_date, priority, created_at) VALUES (?, ?, 'PENDING', ?, ?, ?)",
                                   (project_id, t_title.strip(), t_due.strip(), t_prio.strip(), today_str))
        area_id += 1

    # 3. CONTACTS
    print("🌱 Populating Contacts...")
    contact_section_match = re.search(r'## 3. CONTACTS \(50\)\n+(.*?)\n---', content, re.S)
    if contact_section_match:
        contact_section = contact_section_match.group(1)
        contacts = re.findall(r'\d+\.\s+\*\*Name:\*\*\s+(.*?)\s+\|\s+\*\*Relationship:\*\*\s+(.*?)\s+\|\s+\*\*Tier:\*\*\s+(.*?)\s+\|\s+\*\*Org:\*\*\s+(.*?)\s+\|\s+\*\*Job:\*\*\s+(.*?)\s+\|\s+\*\*Phone:\*\*\s+(.*?)\s+\|\s+\*\*Email:\*\*\s+(.*?)\s+\|\s+\*\*Address:\*\*\s+(.*?)\s+\|\s+\*\*Notes:\*\*\s+(.*)', contact_section)
        for c in contacts:
            cursor.execute("""
                INSERT INTO contacts (name, relationship, tier, organization, job_title, phone, email, address, notes, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*[x.strip() for x in c], today_str))

    # 4. JOURNAL
    print("🌱 Populating Journal Entries...")
    journal_section_match = re.search(r'## 4. JOURNAL ENTRIES \(14\)\n+(.*?)\n---', content, re.S)
    if journal_section_match:
        journal_section = journal_section_match.group(1)
        entries = re.findall(r'\d+\.\s+\*\*Date:\*\*\s+(.*?)\s+\|\s+\*\*Time:\*\*\s+(.*?)\s+\|\s+\*\*Tags:\*\*\s+(.*?)\s+\|\s+\*\*Content:\*\*\s+(.*)', journal_section)
        for e in entries:
            cursor.execute("INSERT INTO journal_entries (date, time, tags, content) VALUES (?, ?, ?, ?)", [x.strip() for x in e])

    # 5. NOTES
    print("🌱 Populating Notes...")
    notes_section_match = re.search(r'## 5. NOTES \(14\)\n+(.*?)\n---', content, re.S)
    if notes_section_match:
        notes_section = notes_section_match.group(1)
        notes = re.findall(r'\d+\.\s+\*?\*?Title:\*?\*?\s+(.*?)\s+\|\s+\*?\*?Tags:\*?\*?\s+(.*?)\s+\|\s+\*?\*?Content:\*?\*?\s+(.*)', notes_section)
        for n in notes:
            cursor.execute("INSERT INTO notes (title, tags, content, created_at) VALUES (?, ?, ?, ?)", (*[x.strip() for x in n], today_str))

    # 6. WORKOUTS
    print("🌱 Populating Workouts...")
    workout_section_match = re.search(r'## 6. WORKOUTS \(12\).*?\n+(.*?)\n---', content, re.S)
    if workout_section_match:
        workout_section = workout_section_match.group(1)
        days = re.findall(r'\*\s+\*\*([\d\-]+)\s+\(.*?\) - (.*?)\*\*\n\s+\*\s+\*Notes:\*\s+(.*?)\n(.*?)(?=\n\*\s+\*\*|\Z)', workout_section, re.S)
        for d_date, d_type, d_notes, d_ex in days:
            cursor.execute("INSERT INTO workouts (start_datetime, type, notes) VALUES (?, ?, ?)", (d_date.strip() + " 06:00", d_type.strip(), d_notes.strip()))
            w_id = cursor.lastrowid
            exs = re.findall(r'\d+\.\s+(.*?):\s+(\d+)\s+sets\s+x\s+(\d+)\s+reps\s+@\s+(\d+)\s+lbs', d_ex)
            for name, s, r, w in exs:
                cursor.execute("INSERT INTO exercises (workout_id, name, sets, reps, weight) VALUES (?, ?, ?, ?, ?)", (w_id, name.strip(), s, r, w))

    # 7. NUTRITION
    print("🌱 Populating Nutrition Logs...")
    nut_section_match = re.search(r'## 7. NUTRITION LOGS \(90\).*?\n+(.*?)\n---', content, re.S)
    if nut_section_match:
        nut_section = nut_section_match.group(1)
        nut_days = re.findall(r'\*\*([\d\-]+)\*\*\n(.*?)(?=\n\*\*|\Z)', nut_section, re.S)
        for n_date, n_content in nut_days:
            meals = re.findall(r'\*\s+(.*?):\s+(.*?)\s+\((\d+)\s+cal,\s+(\d+)g\s+P,\s+(\d+)g\s+C,\s+(\d+)g\s+F\)', n_content)
            for m_type, m_item, cal, p, c, f in meals:
                cursor.execute("INSERT INTO nutrition_logs (date, meal_type, food_item, calories, protein_g, carbs_g, fat_g) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (n_date.strip(), m_type.strip(), m_item.strip(), cal, p, c, f))

    # 8. DAILY METRICS
    print("🌱 Populating Daily Metrics...")
    metrics_section_match = re.search(r'## 8. DAILY METRICS \(30 DAYS\)\n+.*?\n+(.*?)\n---', content, re.S)
    if metrics_section_match:
        metrics_section = metrics_section_match.group(1)
        metric_lines = re.findall(r'\d+\.\s+(.*?):\s+([\d\.]+)/(\d+)\s+\|\s+(\d+)/(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+"(.*?)"\s+\|\s+"(.*?)"\s+\|\s+(.*?)\s+\|\s+(\d+)\s+\|\s+(\d+)', metrics_section)
        for m in metric_lines:
            cursor.execute("""
                INSERT INTO daily_metrics (date, sleep_hours, sleep_quality, morning_mood, evening_mood, readiness_score, productivity_score, stress_level, diet_quality, win_of_the_day, primary_obstacle, hrv, resting_hr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[12], m[13]))

    # 9. INTERACTIONS
    print("🌱 Populating Interactions...")
    int_section_match = re.search(r'## 9. INTERACTIONS \(25 ENTRIES\)\n+(.*?)\n---', content, re.S)
    if int_section_match:
        int_section = int_section_match.group(1)
        ints = re.findall(r'\d+\.\s+\*\*([\d\-]+):\*\*\s+(.*?)\s+\|\s+Re:\s+(.*?)\s+\|\s+(.*?)\s+\|\s+(.*?)(?:\s+\|\s+(.*))?\n', int_section)
        for i in ints:
            c_name = i[1].split('(')[0].replace('Call with ', '').replace('Meeting with ', '').replace('Coffee with ', '').replace('Appointment with ', '').replace('Dinner with ', '').replace('Sync with ', '').replace('Lunch with ', '').replace('Quick chat with ', '').replace('Mentorship session with ', '').replace('Project Kickoff with ', '').replace('Check-in with ', '').replace('Networking call with ', '').replace('Zoom call with ', '').replace('Brief exchange with ', '').replace('Workshop with ', '').strip()
            cursor.execute("SELECT id FROM contacts WHERE name LIKE ?", (f"%{c_name}%",))
            row = cursor.fetchone()
            c_id = row[0] if row else None
            cursor.execute("INSERT INTO interactions (date, contact_id, notes, type) VALUES (?, ?, ?, ?)", (i[0].strip(), c_id, i[2].strip(), i[4].strip()))

    # 10. FINANCIALS
    print("🌱 Populating Financials...")
    fin_section_match = re.search(r'## 10. FINANCIALS.*?\n+### Budgets.*?\n(.*?)\n+### Transactions.*?\n(.*?)\n---', content, re.S)
    if fin_section_match:
        budgets = re.findall(r'\*\s+\*\*?(.*?):\*\*?\s+\$(.*)', fin_section_match.group(1))
        for b_cat, b_amt in budgets:
            cursor.execute("INSERT INTO budgets (category, amount, period) VALUES (?, ?, 'Monthly')", (b_cat.strip(), b_amt.replace(',', '').strip()))
        
        trans = re.findall(r'\d+\.\s+\*\*([\d\-]+):\*\*\s+([\+\-\$\d\.,]+)\s+\|\s+(.*?)\s+\|\s+(.*?)\s+\|\s+(.*?)(?:\s+\|\s+\*\*Link:\s+(.*?)\*\*)?\n', fin_section_match.group(2))
        for t in trans:
            amount_str = t[1].replace('$', '').replace(',', '').strip()
            cursor.execute("INSERT INTO transactions (date, amount, type, category, description) VALUES (?, ?, ?, ?, ?)",
                           (t[0].strip(), amount_str, t[2].strip(), t[3].strip(), t[4].strip()))

    # 11. RESOURCES
    print("🌱 Populating Resources...")
    res_section_match = re.search(r'## 16. RESOURCES \(REFERENCE LIBRARY\)\n+(.*)', content, re.S)
    if res_section_match:
        res_section = res_section_match.group(1)
        res = re.findall(r'\d+\.\s+\*\*Title:\*\*\s+(.*?)\s+\|\s+\*\*URL:\*\*\s+(.*?)\s+\|\s+Type:\s+(.*?)\s+\|\s+Tags:\s+(.*)', res_section)
        for r in res:
            cursor.execute("INSERT INTO resources (title, url, type, tags, created_at) VALUES (?, ?, ?, ?, ?)", (*[x.strip() for x in r], today_str))

    conn.commit()
    conn.close()
    print("✅ Database populated correctly from data_outline.txt.")

if __name__ == "__main__":
    clear_database()
    parse_and_populate()
