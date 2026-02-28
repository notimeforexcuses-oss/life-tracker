import sys
import os
import json
from typing import List
from googleapiclient.discovery import build

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.auth_google import authenticate_google

def get_sheets_service():
    creds = authenticate_google()
    return build('sheets', 'v4', credentials=creds)

def create_sheet(title: str):
    try:
        service = get_sheets_service()
        spreadsheet = service.spreadsheets().create(body={'properties': {'title': title}}).execute()
        return f"Success: Created ID {spreadsheet.get('spreadsheetId')}"
    except Exception as e: return f"Error: {e}"

def append_row(spreadsheet_id: str, values: List[str]):
    """
    Appends a row of data.
    values: A list of strings to add as a row.
    """
    try:
        # Fix: Type Hardening. If AI sends a string "['a','b']" or "a,b", fix it.
        if isinstance(values, str):
            try:
                # Try parsing as JSON list
                values = json.loads(values)
            except:
                # If not JSON, treat as comma-separated or single value
                values = [values]
        
        service = get_sheets_service()
        body = {'values': [values]}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, 
            range='Sheet1!A1', 
            valueInputOption='USER_ENTERED', 
            body=body
        ).execute()
        return "Success: Row appended."
    except Exception as e: return f"Error: {e}"

def read_sheet(spreadsheet_id: str, range_name: str = 'Sheet1!A1:E10'):
    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return str(result.get('values', []))
    except Exception as e: return f"Error: {e}"

def update_cell(spreadsheet_id: str, cell_range: str, value: str):
    try:
        service = get_sheets_service()
        body = {'values': [[value]]}
        service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=cell_range, valueInputOption='USER_ENTERED', body=body).execute()
        return f"Success: Updated {cell_range}."
    except Exception as e: return f"Error: {e}"