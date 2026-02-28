import sys
import os
import zipfile
import time
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Path Fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.auth_google import authenticate_google

BACKUP_FOLDER_NAME = "Second Brain Backups"
FILES_TO_BACKUP = ["brain.db", "brain_pulse.log"]
FOLDERS_TO_BACKUP = ["second_brain_web/media"]

def get_drive_service():
    creds = authenticate_google()
    return build('drive', 'v3', credentials=creds)

def find_or_create_folder(service, folder_name):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

def backup_db_to_drive():
    """
    Zips the database, logs, and media files, then uploads to Google Drive.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_filename = f"brain_backup_{timestamp}.zip"
    
    try:
        # 1. Create Zip
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            # Add standalone files
            for file in FILES_TO_BACKUP:
                if os.path.exists(file):
                    print(f"   + Zipping {file}...")
                    zipf.write(file)
            
            # Add folders recursively
            for folder in FOLDERS_TO_BACKUP:
                if os.path.exists(folder):
                    print(f"   + Zipping folder {folder}...")
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Store in zip using relative path to avoid full absolute paths
                            zipf.write(file_path, os.path.relpath(file_path, os.path.join(folder, '..')))
        
        # 2. Upload
        service = get_drive_service()
        folder_id = find_or_create_folder(service, BACKUP_FOLDER_NAME)
        
        print(f"Uploading {zip_filename}...")
        file_metadata = {'name': zip_filename, 'parents': [folder_id]}
        media = MediaFileUpload(zip_filename, mimetype='application/zip')
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        # 3. Cleanup (With Safety Delay)
        # Give the OS a moment to release the file handle used by MediaFileUpload
        time.sleep(2)
        
        try:
            os.remove(zip_filename)
        except Exception as cleanup_err:
            print(f"   ! Warning: Could not delete local backup file: {cleanup_err}")
        
        return f"Success: Backup uploaded (ID: {file.get('id')})"

    except Exception as e:
        return f"Backup Failed: {e}"

if __name__ == "__main__":
    print(backup_db_to_drive())
