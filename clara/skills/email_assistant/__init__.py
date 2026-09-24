"""
Email Assistant Skill for Clara Core.
"""

from clara.skills.email_assistant.workflows import (
    EmailAssistantWorkflow,
    handle_email_prompt,
)

__all__ = [
    "EmailAssistantWorkflow",
    "handle_email_prompt",
]
