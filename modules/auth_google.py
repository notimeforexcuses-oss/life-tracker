import os.path
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# THE MASTER SCOPE LIST
# We ask for everything we might need so we never have to re-auth.
SCOPES = [
    'https://www.googleapis.com/auth/calendar',        # Read/Write Calendar
    'https://www.googleapis.com/auth/tasks',           # Read/Write Tasks
    'https://www.googleapis.com/auth/gmail.modify',    # Read/Send/Delete Email
    'https://www.googleapis.com/auth/drive.file',      # Create/Manage Backup Files
    'https://www.googleapis.com/auth/documents',       # Read/Write Google Docs
    'https://www.googleapis.com/auth/spreadsheets'     # Read/Write Google Sheets
]

# --- PATH FIX: Locate files in the Project Root, not the current folder ---
BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = str(BASE_DIR / 'credentials.json')
TOKEN_FILE = str(BASE_DIR / 'token.json')

def authenticate_google():
    """
    Handles the OAuth2 flow for the entire Google Workspace suite.
    Uses absolute paths to ensure credentials are found.
    """
    creds = None
    
    # 1. Check for existing token
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            print("Token invalid or scopes changed. Refreshing...")
            creds = None

    # 2. Login if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing access token...")
                creds.refresh(Request())
            except Exception:
                print("Refresh failed. Re-logging in.")
                creds = None
        
        if not creds:
            print(f"Initiating new login for ALL services using {CREDENTIALS_FILE}...")
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"Missing {CREDENTIALS_FILE}. Please download it from Google Cloud.")
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # 3. Save the master token
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"Login successful. Master Token saved to {TOKEN_FILE}.")

    return creds

if __name__ == "__main__":
    try:
        creds = authenticate_google()
        print("Authentication System: ONLINE (Docs/Sheets/Drive/Calendar/Tasks/Gmail)")
    except Exception as e:
        print(f"Authentication Failed: {e}")