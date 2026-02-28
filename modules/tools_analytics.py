import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.database_utils import get_db_connection

def analyze_trend(metric_column: str, days: int = 30):
    conn = get_db_connection()
    try:
        query = f"""
            SELECT date, {metric_column} 
            FROM daily_metrics 
            WHERE date >= date('now', '-{days} days')
            ORDER BY date ASC
        """
        df = pd.read_sql_query(query, conn)
        
        if df.empty: return f"No data found for '{metric_column}'."
        df = df.dropna(subset=[metric_column])
        if len(df) < 3: return f"Insufficient data ({len(df)}) for trend."

        avg_val = df[metric_column].mean()
        min_val = df[metric_column].min()
        max_val = df[metric_column].max()
        
        # Slope Calculation
        if df['date'].nunique() <= 1:
            x_values = np.arange(len(df))
        else:
            x_values = pd.to_datetime(df['date']).map(datetime.toordinal)
            
        slope, _ = np.polyfit(x_values, df[metric_column], 1)
        
        trend = "Stable"
        if slope > 0.05: trend = "Trending UP ↗️"
        elif slope < -0.05: trend = "Trending DOWN ↘️"
        
        return (f"ANALYSIS ({days} Days): {metric_column.replace('_', ' ').title()}\n"
                f"- Trend: {trend} (Slope: {slope:.3f})\n"
                f"- Average: {avg_val:.1f}\n"
                f"- Range: {min_val} - {max_val}")

    except Exception as e: return f"Analytics Error: {e}"
    finally: conn.close()

def analyze_correlation(metric_a: str, metric_b: str, days: int = 60):
    conn = get_db_connection()
    try:
        query = f"SELECT {metric_a}, {metric_b} FROM daily_metrics WHERE date >= date('now', '-{days} days')"
        df = pd.read_sql_query(query, conn).dropna()
        
        if len(df) < 5: return "Insufficient data for correlation."
            
        corr = df[metric_a].corr(df[metric_b])
        strength = "No link"
        if abs(corr) > 0.7: strength = "Strong Link"
        elif abs(corr) > 0.3: strength = "Moderate Link"
        
        return f"CORRELATION ({metric_a} vs {metric_b}): {corr:.2f} ({strength})"
    except Exception as e: return f"Error: {e}"
    finally: conn.close()

def get_weekly_summary():
    """
    Comprehensive Weekly Report: Mental, Physical, Focus, and Financial.
    """
    conn = get_db_connection()
    try:
        # 1. Daily Metrics (Sleep, Mood, HRV)
        df_metrics = pd.read_sql_query("SELECT * FROM daily_metrics WHERE date >= date('now', '-7 days')", conn)
        
        # 2. Focus Logs (New)
        df_focus = pd.read_sql_query("SELECT focus_level, energy_level FROM focus_logs WHERE date >= date('now', '-7 days')", conn)
        
        # 3. Finance (New - Income vs Expense)
        df_finance = pd.read_sql_query("SELECT amount, type FROM transactions WHERE date >= date('now', '-7 days')", conn)

        # Calculations
        sleep_avg = df_metrics['sleep_hours'].mean() if not df_metrics.empty else 0
        hrv_avg = df_metrics['hrv'].mean() if 'hrv' in df_metrics and not df_metrics.empty else 0
        
        focus_avg = df_focus['focus_level'].mean() if not df_focus.empty else 0
        energy_avg = df_focus['energy_level'].mean() if not df_focus.empty else 0
        
        income = df_finance[df_finance['type'] == 'Income']['amount'].sum()
        expenses = df_finance[df_finance['type'] == 'Expense']['amount'].sum()
        savings_rate = ((income - expenses) / income * 100) if income > 0 else 0

        return (f"WEEKLY REPORT (Last 7 Days):\n"
                f"🧠 MIND: Focus {focus_avg:.1f}/10 | Energy {energy_avg:.1f}/10\n"
                f"💪 BODY: Sleep {sleep_avg:.1f} hrs | HRV {hrv_avg:.0f} ms\n"
                f"💰 MONEY: Earned ${income:.0f} | Spent ${expenses:.0f} | Savings Rate: {savings_rate:.1f}%")
    except Exception as e:
        return f"Summary Error: {e}"
    finally:
        conn.close()