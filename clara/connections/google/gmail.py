"""
This module will handle all the crud operations done by ai agent according to user need.

All required consent will be taken via Clara mobile app, user needs to agree all terms
and condition before using this feature of Clara.
"""
import os
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from conf.google_client_conf import SCOPES


def _get_gmail_service():
    """Internal helper to initialize and authenticate the Gmail service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes=SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(request=Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


"""crud ops"""


def send_email(
    to: str, cc: str, bcc: str, subject: str, body: str, attachments: str
) -> None:
    pass


def search_emails(query: str, folder: str, date_range: datetime, limit: int) -> None:
    pass


def get_email_content(message_id: str):
    pass


def summarize_thread(message_ids: str) -> str:
    pass


def update_draft(draft_id: str, new_content: str, new_recipients: str):
    pass


def move_email(message_id: str, target_folder: str):
    pass


def delete_email(message_id: str, parmanent: bool = False):
    pass
