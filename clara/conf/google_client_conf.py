"""Google Workspace Client Configuration and Scope Definitions.

This module loads environment variables and defines OAuth 2.0 endpoints,
client application identifiers, and API scope groupings for Google Workspace
services (Gmail, Calendar, Drive).
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# OAuth Client IDs for various client platforms
GOOGLE_CLIENT_ID_WEB: str = os.getenv("GOOGLE_CLIENT_ID_WEB", "")
"""Google OAuth 2.0 Client ID for Web applications."""

GOOGLE_CLIENT_SECRET_WEB: str = os.getenv("GOOGLE_CLIENT_SECRET_WEB", "")
"""Google OAuth 2.0 Client Secret for Web applications."""

GOOGLE_CLIENT_ID_DESKTOP: str = os.getenv("GOOGLE_CLIENT_ID_DESKTOP", "")
"""Google OAuth 2.0 Client ID for Desktop/CLI applications."""

GOOGLE_CLIENT_ID_ANDROID: str = os.getenv("GOOGLE_CLIENT_ID_ANDROID", "")
"""Google OAuth 2.0 Client ID for Android client applications."""

GOOGLE_CLIENT_ID_IOS: str = os.getenv("GOOGLE_CLIENT_ID_IOS", "")
"""Google OAuth 2.0 Client ID for iOS client applications."""

# Google Auth URIs
AUTH_URI: str = os.getenv(
    "AUTH_URI", "https://accounts.google.com/o/oauth2/auth"
)
"""OAuth 2.0 Authorization server endpoint URL."""

TOKEN_URI: str = os.getenv(
    "TOKEN_URI", "https://oauth2.googleapis.com/token"
)
"""OAuth 2.0 Token exchange endpoint URL."""

# Google Workspace API Scopes
GMAIL_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
]
"""Required OAuth scopes for reading, composing, modifying, and sending
emails via Gmail."""

CALENDAR_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]
"""Required OAuth scopes for accessing and managing Google Calendar events."""

DRIVE_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]
"""Required OAuth scopes for accessing Google Drive files and documents."""

SCOPES: List[str] = GMAIL_SCOPES + CALENDAR_SCOPES + DRIVE_SCOPES
"""Combined list of all required Google Workspace OAuth scopes."""
