"""
This module contains all the required settings regarding google client configurations
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OAuth Client IDs
GOOGLE_CLIENT_ID_WEB = os.getenv("GOOGLE_CLIENT_ID_WEB", "")
GOOGLE_CLIENT_SECRET_WEB = os.getenv("GOOGLE_CLIENT_SECRET_WEB", "")
GOOGLE_CLIENT_ID_DESKTOP = os.getenv("GOOGLE_CLIENT_ID_DESKTOP", "")
GOOGLE_CLIENT_ID_ANDROID = os.getenv("GOOGLE_CLIENT_ID_ANDROID", "")
GOOGLE_CLIENT_ID_IOS = os.getenv("GOOGLE_CLIENT_ID_IOS", "")

# Google Auth URIs
AUTH_URI = os.getenv("AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
TOKEN_URI = os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token")

# Google Workspace Scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
]

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES + DRIVE_SCOPES
