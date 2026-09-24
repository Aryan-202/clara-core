"""
Google connections module for Clara.
"""

from clara.connections.google.gmail import (
    GmailConnection,
    create_draft,
    delete_email,
    get_email_content,
    move_email,
    search_emails,
    send_email,
    summarize_thread,
    update_draft,
)

__all__ = [
    "GmailConnection",
    "send_email",
    "create_draft",
    "update_draft",
    "search_emails",
    "get_email_content",
    "summarize_thread",
    "move_email",
    "delete_email",
]
