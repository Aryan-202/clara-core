"""Email Assistant Skill for Clara Core.

Provides cognitive workflows to parse natural language email commands, draft,
send, search, summarize threads, archive, and delete messages using Google Gmail.
"""

from clara.skills.email_assistant.workflows import (
    EmailAssistantWorkflow,
    handle_email_prompt,
)

GmailAssistantWorkflow = EmailAssistantWorkflow
handle_gmail_prompt = handle_email_prompt

__all__ = [
    "EmailAssistantWorkflow",
    "GmailAssistantWorkflow",
    "handle_email_prompt",
    "handle_gmail_prompt",
]
