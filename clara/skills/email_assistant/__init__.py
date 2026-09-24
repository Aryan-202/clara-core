"""Email Assistant Skill for Clara Core.

Provides cognitive workflows to parse natural language email commands, draft,
send, search, summarize threads, archive, and delete messages using Google Gmail.
"""

from clara.skills.email_assistant.workflows import (
    EmailAssistantWorkflow,
    handle_email_prompt,
)

__all__ = [
    "EmailAssistantWorkflow",
    "handle_email_prompt",
]
