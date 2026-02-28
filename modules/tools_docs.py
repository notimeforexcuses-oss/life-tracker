import sys
import os
from googleapiclient.discovery import build

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.auth_google import authenticate_google

def get_services():
    try:
        creds = authenticate_google()
        if not creds: return None, None
        
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        return docs_service, drive_service
    except Exception as e:
        print(f"Docs Auth Error: {e}")
        return None, None

def create_doc(title: str, initial_text: str = ""):
    docs_service, _ = get_services()
    if not docs_service: return "Error: Auth failed."

    try:
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')
        
        if initial_text:
            requests = [{'insertText': {'location': {'index': 1}, 'text': initial_text}}]
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            
        return f"Success: Created Doc '{title}' (ID: {doc_id})"
    except Exception as e:
        return f"Error creating doc: {e}"

def read_doc(doc_id: str):
    docs_service, _ = get_services()
    if not docs_service: return "Error: Auth failed."
    
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get('body').get('content')
        full_text = ""
        for item in content:
            if 'paragraph' in item:
                elements = item.get('paragraph').get('elements')
                for elem in elements:
                    full_text += elem.get('textRun', {}).get('content', "")
        return full_text
    except Exception as e:
        return f"Error reading doc: {e}"

def append_to_doc(doc_id: str, text: str):
    docs_service, _ = get_services()
    if not docs_service: return "Error: Auth failed."
    
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get('body').get('content')
        if not content: return "Error: Doc content is empty."
        
        end_index = content[-1].get('endIndex') - 1
        
        requests = [{'insertText': {'location': {'index': end_index}, 'text': "\n" + text}}]
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        return "Text appended."
    except Exception as e:
        return f"Error appending: {e}"

def replace_text_in_doc(doc_id: str, find_text: str, replace_text: str):
    docs_service, _ = get_services()
    if not docs_service: return "Error: Auth failed."
    
    try:
        requests = [{
            'replaceAllText': {
                'containsText': {'text': find_text, 'matchCase': True},
                'replaceText': replace_text
            }
        }]
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        return f"Replaced '{find_text}' with '{replace_text}'."
    except Exception as e:
        return f"Error replacing text: {e}"

def delete_drive_file(file_id: str):
    """Deletes a file from Google Drive (Moves to Trash)."""
    _, drive_service = get_services()
    if not drive_service: return "Error: Auth failed."
    
    try:
        drive_service.files().update(fileId=file_id, body={'trashed': True}).execute()
        return f"Success: File {file_id} moved to trash."
    except Exception as e:
        return f"Error deleting file: {e}"