import sys
import os
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.auth_google import authenticate_google

def get_gmail_service():
    creds = authenticate_google()
    return build('gmail', 'v1', credentials=creds)

def fetch_unread_emails(limit: int = 5):
    """Reads top N unread emails."""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', q='is:unread in:inbox', maxResults=limit).execute()
        messages = results.get('messages', [])
        if not messages: return "No unread messages."

        report = []
        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
            headers = txt['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
            report.append(f"ID: {msg['id']} | From: {sender} | Subj: {subject}")
        return "\n".join(report)
    except Exception as e: return f"Error: {e}"

def send_email(to_email: str, subject: str, body: str):
    """Sends an email."""
    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        msg = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return f"Success: Sent (ID: {msg['id']})"
    except Exception as e: return f"Error: {e}"

def delete_email(message_id: str):
    """Moves a specific email to the Trash."""
    try:
        service = get_gmail_service()
        service.users().messages().trash(userId='me', id=message_id).execute()
        return f"Success: Email {message_id} moved to Trash."
    except Exception as e: return f"Error deleting: {e}"