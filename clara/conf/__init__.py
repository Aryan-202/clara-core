"""Configuration and environment settings package for Clara Core.

Provides configuration constants, OAuth scopes, and client IDs for external service
integrations.
"""

from clara.conf.google_client_conf import (
    AUTH_URI,
    CALENDAR_SCOPES,
    DRIVE_SCOPES,
    GMAIL_SCOPES,
    GOOGLE_CLIENT_ID_ANDROID,
    GOOGLE_CLIENT_ID_DESKTOP,
    GOOGLE_CLIENT_ID_IOS,
    GOOGLE_CLIENT_ID_WEB,
    GOOGLE_CLIENT_SECRET_WEB,
    SCOPES,
    TOKEN_URI,
)

__all__ = [
    "AUTH_URI",
    "CALENDAR_SCOPES",
    "DRIVE_SCOPES",
    "GMAIL_SCOPES",
    "GOOGLE_CLIENT_ID_ANDROID",
    "GOOGLE_CLIENT_ID_DESKTOP",
    "GOOGLE_CLIENT_ID_IOS",
    "GOOGLE_CLIENT_ID_WEB",
    "GOOGLE_CLIENT_SECRET_WEB",
    "SCOPES",
    "TOKEN_URI",
]
