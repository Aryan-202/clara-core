# Quickstart Guide

Get up and running with Clara Core in under 5 minutes with these end-to-end practical examples.

---

## Example 1: Initializing the OpenRouter Client

Clara integrates with OpenRouter to provide access to hundreds of AI models (OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, Meta LLaMA 3, etc.) through a single client.

```python
import os
from clara.agent.open_router import OpenRouterClient, Message

# 1. Initialize the client (reads OPENROUTER_API_KEY from environment)
client = OpenRouterClient(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_model="openai/gpt-4o-mini"
)

# 2. Prepare conversation messages
messages = [
    Message(role="system", content="You are Clara, an executive AI assistant."),
    Message(role="user", content="Summarize my daily morning routine priorities.")
]

# 3. Generate completion
response = client.generate_completion(messages=messages, temperature=0.7)

print(f"Model used: {response.model}")
print(f"Response:\n{response.content}")
```

---

## Example 2: Connecting to Google Workspace (Gmail & Calendar)

Clara provides standard connection adapters managed via the `ConnectionRegistry`.

```python
from clara.connections.registry import registry
from clara.connections.google.gmail import GmailConnection
from clara.connections.google.calendar import CalendarConnection

# 1. Retrieve the connection instances from the registry
gmail: GmailConnection = registry.get_instance("gmail")
calendar: CalendarConnection = registry.get_instance("calendar")

# 2. Connect using an OAuth access token received from your user session
USER_TOKEN = "ya29.a0AfH6SM..."

gmail.connect(access_token=USER_TOKEN)
calendar.connect(access_token=USER_TOKEN)

# 3. Query unread emails and upcoming calendar events
emails = gmail.search_emails(folder="unread", limit=5)
print(f"Found {len(emails)} unread email(s):")
for email in emails:
    print(f" - [{email['id']}] {email['subject']} (From: {email['from']})")

events = calendar.list_events(max_results=3)
print(f"\nUpcoming calendar events:")
for ev in events:
    print(f" - {ev['summary']} at {ev['start']}")
```

---

## Example 3: Running the Email Assistant Skill

The `EmailAssistantWorkflow` executes natural language instructions against user email accounts with automated intent parsing, confirmation guardrails, and markdown formatting.

```python
from clara.skills.email_assistant import handle_email_prompt

# 1. User prompts the assistant in natural language
prompt = "Search for emails about Project Roadmap from last week"
access_token = "ya29.a0AfH6SM..."

# 2. Execute the skill workflow
result = handle_email_prompt(
    user_prompt=prompt,
    access_token=access_token
)

# 3. Inspect status and generated markdown response
print(f"Status: {result['status']}")
print(f"Action: {result['action']}")
print("\n--- Assistant Reply ---")
print(result["reply"])
```

### Handling Confirmations & Guardrails

For potentially sensitive operations (e.g. permanent deletion or mass emailing), Clara requires confirmation:

```python
# Step 1: Send a permanent deletion command
res1 = handle_email_prompt(
    user_prompt="Permanently delete email 18f1a2b3c4d5",
    access_token=access_token
)
print(res1["reply"])
# Output: **Pending Confirmation:** Are you sure you want to permanently delete email 18f1a2b3c4d5?

# Step 2: Confirm the pending action
res2 = handle_email_prompt(
    user_prompt="Yes, please proceed",
    access_token=access_token,
    context=res1["data"] # Pass pending action context
)
print(res2["reply"])
# Output: **Success:** Email 18f1a2b3c4d5 permanently deleted.
```

---

## Example 4: Real-time Event Streaming over WebSocket

Clara provides real-time streaming for frontends (React, Flutter, mobile, CLI) over WebSockets at `/ws/chat`.

### Client Implementation (Python / `websockets`)

```python
import asyncio
import json
import websockets

async def chat_with_clara():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        # Send prompt with user access token
        payload = {
            "message": "Check my unread emails and summarize them",
            "access_token": "ya29.a0AfH6SM...",
            "skill": "email_assistant"
        }
        await websocket.send(json.dumps(payload))

        # Listen for real-time streamed responses
        while True:
            response_raw = await websocket.recv()
            event = json.loads(response_raw)
            print(f"Event received [{event.get('type', 'ack')}]:", event)

            if event.get("type") == "chat_response":
                print("\nClara says:")
                print(event["payload"]["reply"])
                break

if __name__ == "__main__":
    asyncio.run(chat_with_clara())
```
