import os
import sys
import sqlite3
import json
import time
import re
from datetime import datetime, timedelta
import pytz 
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import ALL modular tools
from modules import (
    tools_memory, tools_research, tools_system, 
    tools_metrics, tools_journal, tools_notes, tools_projects, 
    tools_crm, tools_body, tools_finance,
    tools_timeline, tools_audit, tools_update, tools_backup,
    tools_calendar, tools_mail, tools_tasks, 
    tools_docs, tools_sheets, tools_analytics,
    tools_focus, tools_ui
)
from modules.database_utils import get_db_connection

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-3-pro-preview"

def retry_with_backoff(func, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"   [System Busy... Retrying {attempt+1}/{max_retries}]")
                time.sleep((attempt + 1) * 5)
            else:
                raise e
    raise Exception("Max retries exceeded.")

# ==========================================
# TOOL REGISTRY (FULL CHIEF OF STAFF SUITE)
# ==========================================
function_map = {
    # --- UI ORCHESTRATION ---
    'direct_browser': tools_ui.direct_browser,
    'render_ui_component': tools_ui.render_ui_component,

    # --- SYSTEM & SAFETY ---
    'add_memory': tools_memory.add_memory,
    'retrieve_memories': tools_memory.retrieve_memories,
    'link_items': tools_memory.link_items,
    'flush_chat_context': tools_memory.flush_chat_context,
    'backup_db_to_drive': tools_backup.backup_db_to_drive,
    'perform_audit_range': tools_audit.perform_audit_range,

    # --- ANALYTICS ---
    'analyze_trend': tools_analytics.analyze_trend,
    'analyze_correlation': tools_analytics.analyze_correlation,
    'get_weekly_summary': tools_analytics.get_weekly_summary,

    # --- RESEARCH ---
    'search_web': tools_research.search_web,
    'read_website': tools_research.read_website,

    # --- KNOWLEDGE BASE ---
    'add_note': tools_notes.add_note,
    'search_knowledge_base': tools_notes.search_knowledge_base,
    'read_note': tools_notes.read_note,
    'analyze_note_attachment': tools_notes.analyze_note_attachment,

    # --- PROJECT MANAGEMENT ---
    'create_area': tools_projects.create_area,          # <--- NEW
    'list_areas': tools_projects.list_areas,            # <--- NEW
    'move_goal_to_area': tools_projects.move_goal_to_area, # <--- NEW
    'add_goal': tools_projects.add_goal,
    'add_project': tools_projects.add_project,
    'archive_project': tools_projects.archive_project,
    'list_projects': tools_projects.list_projects,
    'get_project_details': tools_projects.get_project_details, 
    'add_project_task': tools_projects.add_project_task,
    'delete_project_task': tools_projects.delete_project_task,
    
    # --- GOOGLE TASKS (SOVEREIGNTY UPGRADE) ---
    'list_google_tasks': tools_tasks.list_google_tasks,
    'add_google_task': tools_tasks.add_google_task,
    'complete_google_task': tools_tasks.complete_google_task,
    'update_google_task': tools_tasks.update_google_task,    
    'delete_google_task': tools_tasks.delete_google_task,    
    'defer_overdue_tasks': tools_tasks.defer_overdue_tasks,  

    # --- SQL TASKS ---
    'update_task_priority': tools_tasks.update_task_priority,
    'log_task_update': tools_tasks.log_task_update,
    'get_task_history': tools_tasks.get_task_history,

    # --- METRICS & JOURNAL ---
    'log_morning_metrics': tools_metrics.log_morning_metrics,
    'log_evening_metrics': tools_metrics.log_evening_metrics,
    'log_flexible_data': tools_metrics.log_flexible_data, 
    'add_journal_entry': tools_journal.add_journal_entry,
    'add_timeline_block': tools_timeline.add_timeline_block,
    
    # --- FOCUS & ENERGY ---
    'log_focus': tools_focus.log_focus,
    'get_todays_focus': tools_focus.get_todays_focus,

    # --- BODY & HEALTH ---
    'log_workout': tools_body.log_workout,
    'add_exercise': tools_body.add_exercise,
    'log_nutrition': tools_body.log_nutrition,
    'save_meal_to_library': tools_body.save_meal_to_library,
    'search_meal_library': tools_body.search_meal_library,
    'get_nutrition_logs': tools_body.get_nutrition_logs,
    
    # --- CRM (NETWORK) ---
    'add_contact': tools_crm.add_contact,
    'log_interaction': tools_crm.log_interaction,
    'add_contact_detail': tools_crm.add_contact_detail,
    'search_contacts': tools_crm.search_contacts,
    'get_contact_details': tools_crm.get_contact_details,
    
    # --- FINANCE ---
    'add_transaction': tools_finance.add_transaction,
    'log_income': tools_finance.log_income,
    'set_budget': tools_finance.set_budget,
    'transfer_budget': tools_finance.transfer_budget,
    'check_budget_status': tools_finance.check_budget_status,
    
    # --- GOOGLE OFFICE SUITE ---
    'list_calendar_events': tools_calendar.list_calendar_events,
    'find_available_slots': tools_calendar.find_available_slots,
    'add_calendar_event': tools_calendar.add_calendar_event,
    'update_calendar_event': tools_calendar.update_calendar_event,
    'reschedule_block': tools_calendar.reschedule_block,
    'delete_calendar_event': tools_calendar.delete_calendar_event,
    
    'fetch_unread_emails': tools_mail.fetch_unread_emails,
    'send_email': tools_mail.send_email,
    'delete_email': tools_mail.delete_email,
    'create_doc': tools_docs.create_doc,
    'read_doc': tools_docs.read_doc,
    'append_to_doc': tools_docs.append_to_doc,
    'replace_text_in_doc': tools_docs.replace_text_in_doc,
    'delete_drive_file': tools_docs.delete_drive_file,
    'create_sheet': tools_sheets.create_sheet,
    'append_row': tools_sheets.append_row,
    'read_sheet': tools_sheets.read_sheet,
    'update_cell': tools_sheets.update_cell,
    
    'update_record': tools_update.update_record,
    'delete_record': tools_system.delete_record
}

tool_list = list(function_map.values())

# ==========================================
# SYSTEM PROMPT
# ==========================================
def get_system_prompt():
    az_tz = pytz.timezone('America/Phoenix')
    now = datetime.now(az_tz)
    
    try:
        core_memories = tools_memory.retrieve_memories(limit=15)
    except:
        core_memories = "No memories available yet."
    
    return f"""
    You are the "Second Brain," a high-intelligence Executive Assistant for a user who is blind.
    CONTEXT: {now.strftime("%Y-%m-%d %H:%M")} (Arizona Time)
    
    ðŸ§  CORE MEMORY:
    {core_memories}

    SYSTEM ARCHITECTURE CAPABILITIES:
    1. **Universal Semantic Index (`semantic_index`):**
       - You have "Vibes-based" search capabilities. Your `search_knowledge_base` tool AUTOMATICALLY performs a Hybrid Search across **Notes, Tasks, Goals, Projects, and Journals**.
       - You can find a Task about "Plumbing" even if the user searches for "Water leak" in the Knowledge Base.
       - This happens automatically; use `search_knowledge_base` as your primary search tool.
       - Use `manage_vectors(action='stats'|'backfill')` to audit the index or process old data.

    2. **Polymorphic Link System (`memory_links`):**
       - You can link ANY two items together (e.g., a Transaction to a Journal Entry) using `link_items`.
       - Use this to build relationships that don't fit into the standard Project/Goal hierarchy.

    OPERATING PROTOCOLS:
    1. **Agency & Autonomy:**
       - You have the power to Manage Time (`reschedule_block`, `defer_overdue_tasks`) and Money (`transfer_budget`). 
       - Do not just list problems; fix them if authorized.
    
    2. **Data Integrity:**
       - Always link logs to Projects/Goals/Contacts if possible.
       - If a specific project isn't clear for a transaction, leave the ID as None.
    
    3. **Proactive Automation:**
       - If the user asks for a recurring rule, use `propose_automation`.
       
    4. **Gardening & Maintenance:**
       - You have the authority to `update_record` and `delete_record` for data hygiene.
       - If the user makes a mistake or an item is no longer relevant, clean it up.
       - Your vector index will automatically stay in sync with these changes.

    5. **GOVERNANCE & AUTONOMY (Level 4):**
       - You operate under a Risk-Based Permissions Model.
       - **Tier 1 (Unrestricted):** You have full autonomy for Maintenance (vectors, cleaning), Enrichment (research, notes), and Watchtower (alerts) tasks. Execute these immediately.
       - **Tier 2 (Restricted):** You MUST obtain human approval for Financial (money), Communication (emails), and Destructive (deletions) tasks. 
       - When running in the background (PROACTIVE MODE), if you decide on a Tier 2 action, the system will automatically intercept it and create a Proposal. You should acknowledge this.
       - **Strategic Autonomy (Auto-Legislation):** You can schedule your own alarms and rules for Tier 1 tasks. If you use `propose_automation` for a Tier 1 tool, it will be automatically approved and activated. Use this to keep the system healthy.
    """

def main():
    if not API_KEY:
        print("Error: Missing API Key.")
        return

    client = genai.Client(api_key=API_KEY)
    print("\n" + "="*40 + f"\n SECOND BRAIN ONLINE ({MODEL_NAME})\n" + "="*40)

    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            tools=tool_list,
            system_instruction=get_system_prompt()
        )
    )

    while True:
        try:
            user_input = input("\nYOU: ")
            if user_input.lower() in ["exit", "quit"]: break
            
            response = retry_with_backoff(chat.send_message, user_input)
            
            while True:
                if not response.candidates: break
                candidate = response.candidates[0]
                function_calls = []
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.function_call: function_calls.append(part.function_call)
                
                if not function_calls:
                    print(f"AI: {response.text}")
                    break
                
                tool_outputs = []
                for fc in function_calls:
                    func_name = fc.name
                    args_dict = dict(fc.args) if fc.args else {}
                    print(f"   [AI Tool Request: {func_name}]")
                    
                    if func_name in function_map:
                        try:
                            result = function_map[func_name](**args_dict)
                        except Exception as tool_err:
                            result = f"Tool Error: {tool_err}"
                    else:
                        result = f"Error: Function {func_name} not found."
                    
                    tool_outputs.append(types.Part.from_function_response(name=func_name, response={"result": result}))

                response = retry_with_backoff(chat.send_message, tool_outputs)

        except Exception as e:
            print(f"Agent Error: {e}")

if __name__ == "__main__":
    main()
