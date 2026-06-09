import os
import re
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_core.tools import tool

# =====================================================================
# Configuration and Initialization Helpers
# =====================================================================

# Scopes required to check, read, delete, and send emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Allows read/write/delete (trash) operations
    'https://www.googleapis.com/auth/gmail.send'    # Allows sending emails
]

def _get_gmail_service():
    """Initializes and returns an authorized Gmail API service instance."""
    creds = None
    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    
    # Resolve to absolute paths if they are relative
    token_path = os.path.abspath(token_path)
    credentials_path = os.path.abspath(credentials_path)
    
    # Load existing token if it exists
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            creds = None
            
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
                
        if not creds:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Gmail credentials file not found at '{credentials_path}'.\n"
                    "To enable Gmail integration, please do the following:\n"
                    "1. Go to Google Cloud Console (https://console.cloud.google.com/).\n"
                    "2. Create a project and enable the 'Gmail API'.\n"
                    "3. Go to 'APIs & Services' -> 'Credentials' and configure the OAuth Consent Screen.\n"
                    "4. Create an OAuth client ID for a 'Desktop application'.\n"
                    "5. Download the OAuth client secrets JSON file, rename it to 'credentials.json', "
                    "and place it in the workspace root directory: "
                    f"'{os.path.dirname(credentials_path)}'\n"
                    "Alternatively, specify the correct path using GMAIL_CREDENTIALS_PATH in your .env file."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # Starts a local web server to complete OAuth 2.0 flow
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

def get_email_body(payload) -> str:
    """Helper to extract the body text from a MIME payload."""
    if 'parts' in payload:
        # 1. Look for plain text parts first
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    try:
                        padded_data = data + '=' * (4 - len(data) % 4)
                        return base64.urlsafe_b64decode(padded_data.encode('ASCII')).decode('utf-8', errors='replace')
                    except Exception:
                        pass
            elif part['mimeType'] == 'multipart/alternative' or part['mimeType'].startswith('multipart/'):
                body = get_email_body(part)
                if body:
                    return body
                    
        # 2. If no plain text is found, look for html and strip it
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data')
                if data:
                    try:
                        padded_data = data + '=' * (4 - len(data) % 4)
                        html = base64.urlsafe_b64decode(padded_data.encode('ASCII')).decode('utf-8', errors='replace')
                        
                        # Strip css style blocks
                        html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html)
                        # Strip script blocks
                        html = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html)
                        # Strip all HTML tags
                        text = re.sub(r'<[^>]+?>', ' ', html)
                        # Normalize white space
                        text = re.sub(r'\s+', ' ', text).strip()
                        return text
                    except Exception:
                        pass
    else:
        # Single-part message
        data = payload.get('body', {}).get('data')
        if data:
            try:
                padded_data = data + '=' * (4 - len(data) % 4)
                return base64.urlsafe_b64decode(padded_data.encode('ASCII')).decode('utf-8', errors='replace')
            except Exception:
                pass
                
    return ""

# =====================================================================
# Tool Definitions
# =====================================================================

@tool
def gmail_check_unread(max_results: int = 10) -> str:
    """Check and list the most recent unread emails in the user's Gmail inbox.
    
    Args:
        max_results (int, optional): The maximum number of unread emails to retrieve. Defaults to 10.
        
    Returns:
        str: A formatted list of unread emails containing ID, Sender, Subject, Date, and Snippet, or an error.
    """
    try:
        service = _get_gmail_service()
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return "No unread emails found."
            
        lines = [f"Found {len(messages)} unread email(s):"]
        for msg in messages:
            msg_id = msg['id']
            # Get metadata headers
            full_msg = service.users().messages().get(
                userId='me', 
                id=msg_id, 
                format='metadata', 
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            payload = full_msg.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(No Sender)')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '(No Date)')
            snippet = full_msg.get('snippet', '')
            
            lines.append(f"\n- **ID**: `{msg_id}`")
            lines.append(f"  **From**: {sender}")
            lines.append(f"  **Subject**: {subject}")
            lines.append(f"  **Date**: {date}")
            lines.append(f"  **Snippet**: {snippet}")
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error checking unread emails: {str(e)}"

@tool
def gmail_search_emails(query: str, max_results: int = 10) -> str:
    """Search for emails matching a specific Gmail search query (e.g. 'from:Google', 'subject:Alert', 'is:starred').
    
    Args:
        query (str): The search query using standard Gmail search operators.
        max_results (int, optional): The maximum number of matching emails to retrieve. Defaults to 10.
        
    Returns:
        str: A formatted list of matching emails, or an error.
    """
    try:
        service = _get_gmail_service()
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return f"No emails found matching query: '{query}'"
            
        lines = [f"Found {len(messages)} email(s) matching '{query}':"]
        for msg in messages:
            msg_id = msg['id']
            full_msg = service.users().messages().get(
                userId='me', 
                id=msg_id, 
                format='metadata', 
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            payload = full_msg.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(No Sender)')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '(No Date)')
            snippet = full_msg.get('snippet', '')
            
            lines.append(f"\n- **ID**: `{msg_id}`")
            lines.append(f"  **From**: {sender}")
            lines.append(f"  **Subject**: {subject}")
            lines.append(f"  **Date**: {date}")
            lines.append(f"  **Snippet**: {snippet}")
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching emails with query '{query}': {str(e)}"

@tool
def gmail_read_email(email_id: str) -> str:
    """Retrieve and display the subject, sender, date, and full body content of a specific email.
    
    Args:
        email_id (str): The unique ID of the email to retrieve and read.
        
    Returns:
        str: The full details and text body of the email, or an error.
    """
    try:
        service = _get_gmail_service()
        msg = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(No Sender)')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '(No Date)')
        
        body = get_email_body(payload)
        if not body:
            body = msg.get('snippet', '(No body content could be decoded.)')
            
        lines = [
            f"Email ID: `{email_id}`",
            f"From: {sender}",
            f"Subject: {subject}",
            f"Date: {date}",
            "\n--- Body ---",
            body,
            "------------"
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading email with ID '{email_id}': {str(e)}"

@tool
def gmail_send_email(to: str, subject: str, body: str) -> str:
    """Send a new plain-text email message to a specified recipient.
    
    Args:
        to (str): The recipient's email address (e.g. 'someone@example.com').
        subject (str): The subject line of the email.
        body (str): The plain-text body content of the email.
        
    Returns:
        str: A confirmation message with the ID of the sent email, or an error.
    """
    try:
        from email.mime.text import MIMEText
        
        service = _get_gmail_service()
        
        # Build MIME Message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        # Encode message to base64url bytes and then to string
        raw_bytes = base64.urlsafe_b64encode(message.as_bytes())
        raw_string = raw_bytes.decode('utf-8')
        
        body_dict = {'raw': raw_string}
        
        sent_msg = service.users().messages().send(userId='me', body=body_dict).execute()
        return f"Successfully sent email to '{to}' (ID: `{sent_msg['id']}`)."
    except Exception as e:
        return f"Error sending email: {str(e)}"

@tool
def gmail_delete_email(email_id: str) -> str:
    """Move a specific email message to the Trash folder.
    
    Args:
        email_id (str): The unique ID of the email to move to trash.
        
    Returns:
        str: A success message confirming it was moved to Trash, or an error.
    """
    try:
        service = _get_gmail_service()
        service.users().messages().trash(userId='me', id=email_id).execute()
        return f"Successfully moved email with ID `{email_id}` to the Trash."
    except Exception as e:
        return f"Error deleting email with ID '{email_id}': {str(e)}"

# Export all defined Gmail tools as a list
gmail_toolset = [
    gmail_check_unread,
    gmail_search_emails,
    gmail_read_email,
    gmail_send_email,
    gmail_delete_email
]
