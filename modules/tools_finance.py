import sqlite3
from datetime import datetime
from typing import Optional
from modules.database_utils import get_db_connection
from modules.vector_utils import update_vector_index

# --- TRANSACTIONS ---

def add_transaction(amount: float, type: str, category: str, description: str, 
                    linked_project_id: Optional[int] = None, linked_timeline_id: Optional[int] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO transactions (date, amount, type, category, description, linked_project_id, linked_timeline_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date_str, amount, type, category, description, linked_project_id, linked_timeline_id))
    
    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Vectorize for semantic search
    text = f"Transaction: {type} ${amount} - {description} (Category: {category})"
    update_vector_index(transaction_id, 'transaction', text)
    
    return f"Transaction logged: {type} ${amount} ({category})"

def log_income(amount: float, source: str, description: str = ""):
    """
    Logs income (e.g., Salary, Freelance). Wrapper for add_transaction.
    """
    return add_transaction(amount, "Income", source, description)

# --- BUDGETING ---

def set_budget(category: str, amount: float, period: str = "Monthly"):
    conn = get_db_connection()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT id FROM budgets WHERE category = ? AND period = ?", (category, period))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE budgets SET amount = ?, last_updated = ? WHERE id = ?", (amount, date_str, existing['id']))
        msg = f"Updated {period} budget for '{category}' to ${amount}."
    else:
        cursor.execute("INSERT INTO budgets (category, amount, period, last_updated) VALUES (?, ?, ?, ?)",
                       (category, amount, period, date_str))
        msg = f"Set new {period} budget for '{category}' to ${amount}."
    
    conn.commit()
    conn.close()
    return msg

def transfer_budget(from_category: str, to_category: str, amount: float):
    """
    Moves budget allocation from one category to another.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check From
    cursor.execute("SELECT id, amount FROM budgets WHERE category = ?", (from_category,))
    src = cursor.fetchone()
    if not src: return f"Error: Source category '{from_category}' not found."
    if src['amount'] < amount: return f"Error: Insufficient funds in '{from_category}' (Has ${src['amount']})."
    
    # Check To
    cursor.execute("SELECT id, amount FROM budgets WHERE category = ?", (to_category,))
    dest = cursor.fetchone()
    if not dest: return f"Error: Destination category '{to_category}' not found. Create it first."
    
    # Execute Transfer
    new_src_amt = src['amount'] - amount
    new_dest_amt = dest['amount'] + amount
    
    cursor.execute("UPDATE budgets SET amount = ? WHERE id = ?", (new_src_amt, src['id']))
    cursor.execute("UPDATE budgets SET amount = ? WHERE id = ?", (new_dest_amt, dest['id']))
    
    conn.commit()
    conn.close()
    return f"Success: Moved ${amount} from '{from_category}' to '{to_category}'."

def check_budget_status(category: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT amount FROM budgets WHERE category = ?", (category,))
    budget_row = cursor.fetchone()
    if not budget_row: 
        conn.close()
        return f"No budget set for category '{category}'."
    
    budget_limit = budget_row['amount']
    
    current_month = datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT SUM(amount) as total FROM transactions 
        WHERE category = ? AND type = 'Expense' AND date LIKE ?
    """, (category, f"{current_month}%"))
    
    spent_row = cursor.fetchone()
    spent = spent_row['total'] if spent_row['total'] else 0.0
    
    conn.close()
    
    remaining = budget_limit - spent
    percent = (spent / budget_limit) * 100
    
    status = "🟢 Good"
    if percent > 80: status = "🟡 Warning"
    if percent > 100: status = "🔴 Over Budget"
    
    return (f"BUDGET STATUS: {category}\n"
            f"Spent: ${spent:.2f} / ${budget_limit:.2f} ({percent:.1f}%)\n"
            f"Remaining: ${remaining:.2f}\n"
            f"Status: {status}")