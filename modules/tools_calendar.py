import sys
import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

# Allow importing from the parent 'modules' directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.auth_google import authenticate_google

DEFAULT_TIMEZONE = 'America/Phoenix'

def get_calendar_service():
    """
    Retrieves the authenticated Calendar Service using the Master Token.
    """
    try:
        creds = authenticate_google()
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Calendar Auth Error: {e}")
        return None

def list_calendar_events(days: int = 3):
    service = get_calendar_service()
    if not service: return "Error: Calendar service not authenticated."

    now = datetime.utcnow().isoformat() + 'Z'
    end_time = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
    
    try:
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              timeMax=end_time, maxResults=20, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found."

        output = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            evt_id = event.get('id')
            # We include the ID so the Agent can use it for updates/deletions
            output.append(f"- [ID: {evt_id}] {start}: {summary}")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error listing events: {e}"

def find_available_slots(date: str, duration_min: int = 60):
    """
    Finds free time slots on a specific date.
    date format: 'YYYY-MM-DD'
    """
    service = get_calendar_service()
    if not service: return "Error: Calendar service not authenticated."

    try:
        tz = pytz.timezone(DEFAULT_TIMEZONE)
        
        # Define the search window (9 AM to 9 PM)
        day_start = datetime.strptime(date, "%Y-%m-%d").replace(hour=9, minute=0)
        day_end = datetime.strptime(date, "%Y-%m-%d").replace(hour=21, minute=0)
        
        # Convert to ISO for API
        iso_start = tz.localize(day_start).isoformat()
        iso_end = tz.localize(day_end).isoformat()
        
        body = {
            "timeMin": iso_start,
            "timeMax": iso_end,
            "timeZone": DEFAULT_TIMEZONE,
            "items": [{"id": "primary"}]
        }
        
        events_result = service.freebusy().query(body=body).execute()
        busy_periods = events_result['calendars']['primary']['busy']
        
        # Simple Logic: Check hour-by-hour availability
        available_slots = []
        current_time = day_start
        
        while current_time + timedelta(minutes=duration_min) <= day_end:
            slot_end = current_time + timedelta(minutes=duration_min)
            
            # Check if this slot overlaps with any busy period
            is_busy = False
            slot_start_iso = tz.localize(current_time).isoformat()
            slot_end_iso = tz.localize(slot_end).isoformat()
            
            for period in busy_periods:
                if period['start'] < slot_end_iso and period['end'] > slot_start_iso:
                    is_busy = True
                    break
            
            if not is_busy:
                available_slots.append(current_time.strftime("%I:%M %p"))
            
            # Move forward 30 mins
            current_time += timedelta(minutes=30)
            
        if not available_slots:
            return f"No available slots found on {date}."
            
        return f"Available slots on {date}: " + ", ".join(available_slots)

    except Exception as e:
        return f"Error finding slots: {e}"

def add_calendar_event(summary: str, start_time: str, duration_min: int = 60):
    """
    Creates a new event. 
    start_time format: 'YYYY-MM-DD HH:MM' or ISO
    """
    service = get_calendar_service()
    if not service: return "Error: Calendar service not authenticated."
    
    try:
        # Flexible parsing
        try:
            dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        except ValueError:
            dt_start = datetime.fromisoformat(start_time)

        dt_end = dt_start + timedelta(minutes=duration_min)
        
        event = {
            'summary': summary,
            'start': {'dateTime': dt_start.isoformat(), 'timeZone': DEFAULT_TIMEZONE},
            'end': {'dateTime': dt_end.isoformat(), 'timeZone': DEFAULT_TIMEZONE},
        }
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Success: Event created (ID: {event.get('id')})"
    except Exception as e:
        return f"Error creating event: {e}"

def update_calendar_event(event_id: str, new_summary: str = None, new_start_time: str = None):
    service = get_calendar_service()
    if not service: return "Error: Calendar service not authenticated."
    
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        if new_summary:
            event['summary'] = new_summary
            
        if new_start_time:
            try:
                dt_start = datetime.strptime(new_start_time, "%Y-%m-%d %H:%M")
            except ValueError:
                dt_start = datetime.fromisoformat(new_start_time)
            
            # Calculate original duration to preserve it
            orig_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', ''))
            orig_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', ''))
            duration = orig_end - orig_start
            
            dt_end = dt_start + duration
            
            event['start']['dateTime'] = dt_start.isoformat()
            event['end']['dateTime'] = dt_end.isoformat()
            
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return f"Success: Event updated."
    except Exception as e:
        return f"Error updating event: {e}"

def delete_calendar_event(event_id: str):
    service = get_calendar_service()
    if not service: return "Error: Calendar service not authenticated."
    
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return "Success: Event deleted."
    except Exception as e:
        return f"Error deleting event: {e}"

def reschedule_block(date: str, target_date: str):
    """
    Moves ALL events from one day to another (Bulk Reschedule).
    """
    service = get_calendar_service()
    if not service: return "Error: Calendar service not authenticated."
    
    tz = pytz.timezone(DEFAULT_TIMEZONE)
    
    # Define Source Range
    dt_source_start = datetime.strptime(date, "%Y-%m-%d")
    dt_source_end = dt_source_start + timedelta(days=1)
    
    # ISO Format
    iso_start = dt_source_start.isoformat() + 'Z' 
    iso_end = dt_source_end.isoformat() + 'Z'
    
    # 1. Find Events
    events_result = service.events().list(calendarId='primary', timeMin=iso_start,
                                          timeMax=iso_end, singleEvents=True).execute()
    events = events_result.get('items', [])
    
    if not events:
        return f"No events found on {date} to move."
    
    # 2. Calculate Delta
    dt_target_start = datetime.strptime(target_date, "%Y-%m-%d")
    days_delta = (dt_target_start - dt_source_start).days
    
    moved_count = 0
    try:
        batch = service.new_batch_http_request()
        
        for event in events:
            if 'dateTime' not in event['start']: continue 

            orig_start = datetime.fromisoformat(event['start'].get('dateTime')).replace(tzinfo=None)
            orig_end = datetime.fromisoformat(event['end'].get('dateTime')).replace(tzinfo=None)
            
            new_event_start = orig_start + timedelta(days=days_delta)
            new_event_end = orig_end + timedelta(days=days_delta)
            
            event['start'] = {'dateTime': tz.localize(new_event_start).isoformat(), 'timeZone': DEFAULT_TIMEZONE}
            event['end'] = {'dateTime': tz.localize(new_event_end).isoformat(), 'timeZone': DEFAULT_TIMEZONE}
            
            batch.add(service.events().update(calendarId='primary', eventId=event['id'], body=event))
            moved_count += 1
            
        batch.execute()
        return f"Success: Moved {moved_count} events from {date} to {target_date}."
        
    except Exception as e:
        return f"Error moving events: {e}"