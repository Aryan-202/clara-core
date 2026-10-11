"""Gmail Assistant module for Clara Core.

Provides direct access to Gmail Assistant workflows, aliases, and helpers
integrating with the Email Assistant cognitive workflow subsystem.
"""

from clara.skills.email_assistant.workflows import (
    EmailAssistantWorkflow,
    handle_email_prompt,
)

GmailAssistantWorkflow = EmailAssistantWorkflow
"""Alias for :class:`~clara.skills.email_assistant.workflows.EmailAssistantWorkflow`."""

handle_gmail_prompt = handle_email_prompt
"""Alias for :func:`~clara.skills.email_assistant.workflows.handle_email_prompt`."""

__all__ = [
    "EmailAssistantWorkflow",
    "GmailAssistantWorkflow",
    "handle_email_prompt",
    "handle_gmail_prompt",
]
