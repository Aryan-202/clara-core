# Architecture Overview

Clara Core is architected as a modular, decoupled framework designed for cognitive agent workflows, external service integrations, and real-time client communication.

---

## High-Level System Architecture

```text
+-------------------------------------------------------------------------+
|                              Clara Client                               |
|               (Mobile Flutter App, Web Dashboard, CLI)                  |
+-------------------------------------------------------------------------+
                                    |
                                    |  JSON / WebSocket Protocol
                                    v
+-------------------------------------------------------------------------+
|                           clara.api (FastAPI)                           |
|  - ConnectionManager: Socket tracking & heartbeat                       |
|  - EventStreamer: Real-time broadcast & typing events                   |
|  - APIRouter (/ws/chat, /health): Request dispatching                   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                          clara.agent & Skills                           |
|  - OpenRouterClient: LLM model prompting & completion                   |
|  - Skill Registry & Router: Intent classification & entity extraction   |
|  - Cognitive CRUD Loop: Ambiguity check & safety guardrails             |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                       clara.connections (Adapters)                      |
|  - ConnectionRegistry: Dynamic service resolution                       |
|  - BaseConnection: Standardized authentication lifecycle                |
|  - Google Workspace Adapters: Gmail, Calendar, Drive                    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                          External APIs & Services                       |
|          (Google APIs, OpenRouter, Notion, Slack, GitHub)               |
+-------------------------------------------------------------------------+
```

---

## The Request Lifecycle

When a user interacts with Clara (e.g. typing *"Draft an email to Alex about the budget review"*), the request moves through five distinct lifecycle stages:

```text
[1. Ingestion]  -->  [2. Orchestration]  -->  [3. Skill Dispatch]  -->  [4. Execution]  -->  [5. Streaming]
   WebSocket             OpenRouter /             Email Assistant          Gmail Connection       EventStreamer
    Payload                Intents                  Cognitive Loop           API Calls             Broadcast
```

1. **Ingestion (`clara.api.ws`):**
   * The client initiates a persistent WebSocket connection to `/ws/chat`.
   * `ConnectionManager` accepts and registers the socket in the active pool.
   * Incoming messages are decoded and sanitized, separating prompt text, OAuth bearer tokens, and session context.

2. **Agent Orchestration (`clara.agent`):**
   * The prompt is evaluated against skill triggers or submitted to the `OpenRouterClient` for intent classification and tool selection.
   * The conversation history is maintained and formatted according to the model's chat schema.

3. **Skill Selection & Guardrails (`clara.skills`):**
   * The resolved skill workflow (e.g. `EmailAssistantWorkflow`) receives the prompt.
   * Entities such as recipients, subject, body, and dates are parsed.
   * **Safety Guardrails:** If the action has high blast radius (permanent deletion, emailing >5 recipients), execution pauses and emits a `pending_confirmation` status back to the user.

4. **Connection Execution (`clara.connections`):**
   * Once validated, the skill requests an active connection adapter from the `ConnectionRegistry`.
   * The connection adapter executes the concrete API calls (e.g., `send_email`, `create_event`, `list_files`) using the user's OAuth credentials.

5. **Streamed Response (`clara.api.ws.event_streamer`):**
   * The action result is formatted into human-readable markdown and a structured JSON payload.
   * `EventStreamer` publishes the `chat_response` event back over the WebSocket to the client frontend.

---

## Skills vs Connections: Key Architectural Distinction

A core design principle of Clara is the strict separation between **Skills** and **Connections**:

| Concept | Layer | Primary Responsibility | Example |
| :--- | :--- | :--- | :--- |
| **Connections** | `clara.connections` | Raw API protocol adapters, authentication token management, HTTP calls, payload serialization. | `GmailConnection.send_email()`, `CalendarConnection.list_events()` |
| **Skills** | `clara.skills` | Business logic, prompt engineering, intent parsing, safety guardrails, user confirmations, markdown formatting. | `EmailAssistantWorkflow.execute()`, `skill.yaml`, `prompt.md` |

### Why This Separation Matters
* **Swappable Providers:** Skills do not care about the underlying API implementation. An email skill could route to Gmail, Microsoft Graph, or Fastmail simply by targeting a different connection adapter.
* **Security & Testing:** Connection adapters can be mocked or unit-tested independently without running LLM inference.
* **Modularity:** Developers can write custom skills without modifying the core API server or low-level connection classes.
