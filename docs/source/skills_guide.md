# Skills Guide

Skills in Clara encapsulate cognitive domains and automated agent capabilities. Each skill packages intent recognition, prompt engineering templates, safety policies, and tool execution routines.

---

## Skill Directory Structure

Every Clara skill is organized within its own subpackage under `clara/skills/`:

```text
clara/skills/email_assistant/
├── __init__.py         # Public exports (Workflows and helpers)
├── skill.yaml          # Declarative metadata, trigger keywords, and tool schemas
├── prompt.md           # System prompt templates, persona, and cognitive rules
└── workflows.py        # Python workflow coordinator and intent dispatcher
```

---

## 1. Skill Manifest (`skill.yaml`)

The `skill.yaml` file declaratively defines how Clara discovers, activates, and provisions tools for a skill:

```yaml
name: email_assistant
version: "0.1.0"
display_name: "Email Assistant"
description: "AI-powered email management assistant for Gmail."
category: "Productivity"

# Keyword triggers used for fast intent routing
triggers:
  - "email"
  - "gmail"
  - "inbox"
  - "send email"
  - "draft email"

# External connections required by this skill
connections:
  - service: google
    name: gmail
    required_scopes:
      - "https://www.googleapis.com/auth/gmail.readonly"
      - "https://www.googleapis.com/auth/gmail.send"
      - "https://www.googleapis.com/auth/gmail.modify"

# Callable tools exposed by the skill to LLM function calling
tools:
  - name: send_email
    description: "Send an email to one or more recipients."
    parameters:
      to:
        type: string
        required: true
      subject:
        type: string
        required: true
      body:
        type: string
        required: true
```

---

## 2. Prompt Template (`prompt.md`)

`prompt.md` provides domain-specific instructions to guide LLM reasoning:
* **Persona:** Defines Clara's role and tone (e.g. executive assistant).
* **The Cognitive CRUD Loop:** Directs the model to parse intents, extract parameters, check ambiguity, execute tools, and format output.
* **Safety Guardrails:** Enforces rules like mandatory confirmation for destructive operations or batch actions.

---

## 3. Workflow Implementation (`workflows.py`)

Workflows coordinate between incoming prompts and connection tools.

```python
from typing import Dict, Any, Optional
from clara.connections.registry import registry

class CustomSkillWorkflow:
    """Example custom workflow implementation."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token

    def execute(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Parse intent and arguments
        # 2. Check safety guardrails
        # 3. Invoke connection tools
        # 4. Return structured response
        return {
            "status": "success",
            "action": "custom_action",
            "reply": f"Completed task: {user_prompt}",
            "data": {}
        }
```

---

## Creating a New Skill: Step-by-Step

1. Create a directory `clara/skills/my_skill/`.
2. Define `skill.yaml` with your skill's triggers and tools.
3. Write `prompt.md` containing prompt definitions.
4. Implement `workflows.py` inheriting your business logic.
5. Export your workflow in `clara/skills/__init__.py`.
