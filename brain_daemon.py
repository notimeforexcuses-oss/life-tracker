import time
import schedule
import logging
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sqlite3

# --- PATH SETUP ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain_agent import function_map, get_system_prompt, retry_with_backoff
from modules.database_utils import get_db_connection
from modules.tools_system import AUTONOMY_POLICY

# --- CONFIGURATION ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3-pro-preview"
LOG_FILE = "brain_pulse.log"

# --- LOGGING ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_pulse(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    logging.info(message)

# --- NEW TOOL: SYSTEM NOTIFICATIONS ---
def add_system_notification(content: str, type: str = "Insight", severity: str = "Info"):
    """
    Writes a proactive notification or alert to the system dashboard.
    type: 'Insight', 'Alert', 'Action Required'
    severity: 'Info', 'Warning', 'Critical'
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
            INSERT INTO system_notifications (type, content, severity, created_at)
            VALUES (?, ?, ?, ?)
        """, (type, content, severity, created_at))
        conn.commit()
        log_pulse(f"Proactive Notification Added: [{type}] {content[:50]}...")
        return "Notification sent to dashboard."
    except Exception as e:
        return f"Error adding notification: {e}"
    finally:
        conn.close()

# --- GOVERNANCE WRAPPER ---
def make_safe_tool(name, func):
    """
    Wraps a tool function to enforce the Tiered Autonomy Policy.
    Tier 1: Executes normally.
    Tier 2: Intercepts and creates a Proposal instead.
    """
    def safe_wrapper(**kwargs):
        tier = AUTONOMY_POLICY.get(name, 2)
        if tier == 1:
            log_pulse(f"   [Auto-Execute Tier 1: {name}]")
            return func(**kwargs)
        else:
            log_pulse(f"   [Restricted Tier 2 Intercepted: {name}]")
            # Create the proposal
            proposal_desc = f"Action: {name} | Parameters: {kwargs}"
            try:
                # We call the raw functions here to avoid recursion
                res_prop = function_map['propose_automation'](
                    trigger_condition="Autonomous Background Logic",
                    proposed_action=proposal_desc
                )
                add_system_notification(
                    content=f"The Brain proposed a restricted action: {name}. Please review the proposal.",
                    type="Action Required",
                    severity="Warning"
                )
                return f"INTERCEPTED: This action requires human approval. {res_prop}"
            except Exception as e:
                return f"Governance Error: {e}"
    
    # CRITICAL: Preserve the function name for the Gemini API tool definition
    safe_wrapper.__name__ = name
    return safe_wrapper

# Create the protected toolset for the daemon
daemon_function_map = {}
for name, func in function_map.items():
    daemon_function_map[name] = make_safe_tool(name, func)

# Also add the daemon-specific notification tool (it is Tier 1)
daemon_function_map['add_system_notification'] = add_system_notification
daemon_tool_list = list(daemon_function_map.values())

# --- THE LOGIC ENGINE (PROACTIVE AI) ---
def wake_agent(context_prompt):
    """
    Spins up a proactive AI session to handle background tasks.
    """
    if not API_KEY:
        log_pulse("Error: No API Key found.")
        return

    log_pulse(f"Waking Brain for: {context_prompt}")
    
    try:
        client = genai.Client(api_key=API_KEY)
        
        chat = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                tools=daemon_tool_list,
                system_instruction=get_system_prompt() + "\n\nPROACTIVE MODE: You are running in the background. Use 'add_system_notification' to alert the user of important findings."
            )
        )
        
        response = retry_with_backoff(chat.send_message, context_prompt)
        
        # Tool Execution Loop
        while True:
            if not response.candidates: break
            candidate = response.candidates[0]
            function_calls = []
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.function_call: function_calls.append(part.function_call)
            
            if not function_calls:
                # Daemon responses go to log, not user
                if response.text:
                    log_pulse(f"Brain Thought: {response.text}")
                break
            
            tool_outputs = []
            for fc in function_calls:
                func_name = fc.name
                args_dict = dict(fc.args) if fc.args else {}
                log_pulse(f"   [Daemon Activity: {func_name}]")
                
                if func_name in daemon_function_map:
                    try:
                        # Governance is now handled inside the wrapped function
                        result = daemon_function_map[func_name](**args_dict)
                    except Exception as tool_err:
                        result = f"Tool Error: {tool_err}"
                else:
                    result = f"Error: Function {func_name} not found."
                
                tool_outputs.append(types.Part.from_function_response(name=func_name, response={"result": result}))

            response = retry_with_backoff(chat.send_message, tool_outputs)

        log_pulse("Brain returned to standby.")

    except Exception as e:
        log_pulse(f"Daemon Execution Error: {e}")

# --- WATCHDOGS ---

def check_external_state():
    """Sensory integration check."""
    log_pulse("Polling sensory inputs (Email, Calendar, Tasks)...")
    wake_agent("SYSTEM: Perform a background state check. Fetch unread emails, check upcoming calendar events, and scan for overdue tasks. If anything is urgent, use add_system_notification.")

def nightly_maintenance():
    """Fixed-time maintenance."""
    log_pulse("Running Nightly Maintenance...")
    wake_agent("SYSTEM: It is 22:00. Perform a daily audit. Check if today's metrics were logged. Backfill any missing vectors. Suggest an evening reflection.")

def morning_briefing():
    """Morning proactive briefing."""
    log_pulse("Synthesizing Morning Briefing...")
    wake_agent("SYSTEM: It is 08:00. Synthesize today's battle plan. Check calendar, high-priority tasks, and budget status. Post a briefing to the dashboard.")

# --- SCHEDULER ---
# Real-world schedule
schedule.every(30).minutes.do(check_external_state)
schedule.every().day.at("08:00").do(morning_briefing)
schedule.every().day.at("22:00").do(nightly_maintenance)

# Initial run on startup
# check_external_state()

def start_daemon():
    log_pulse("--- SECOND BRAIN: THE PULSE IS ONLINE ---")
    log_pulse("Event-Driven Architecture: ACTIVE")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            log_pulse("Pulse stopped by user.")
            break
        except Exception as e:
            log_pulse(f"Fatal Pulse Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    start_daemon()