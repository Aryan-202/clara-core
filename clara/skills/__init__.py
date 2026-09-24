"""Skills and cognitive workflow subsystem for Clara Core.

Skills contain specialized domain knowledge, intent parsing, prompt templates,
and orchestrations combining LLMs and external connections.
"""

from clara.skills.email_assistant import EmailAssistantWorkflow, handle_email_prompt

__all__ = [
    "EmailAssistantWorkflow",
    "handle_email_prompt",
]
