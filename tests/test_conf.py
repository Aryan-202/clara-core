"""Unit tests for configuration constants and Google OAuth scopes."""

from clara.conf.google_client_conf import (
    AUTH_URI,
    CALENDAR_SCOPES,
    DRIVE_SCOPES,
    GMAIL_SCOPES,
    SCOPES,
    TOKEN_URI,
)


def test_scopes_defined():
    assert len(GMAIL_SCOPES) > 0
    assert len(CALENDAR_SCOPES) > 0
    assert len(DRIVE_SCOPES) > 0
    assert len(SCOPES) == len(GMAIL_SCOPES) + len(CALENDAR_SCOPES) + len(
        DRIVE_SCOPES
    )


def test_auth_uris_defined():
    assert AUTH_URI.startswith("https://")
    assert TOKEN_URI.startswith("https://")
