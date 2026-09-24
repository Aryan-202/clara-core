# Connections & Integrations Guide

Connections provide low-level adapters to external APIs and services. They handle authentication, token refreshment, rate limits, and network requests.

---

## Connection Architecture

All service integrations inherit from `BaseConnection` and register themselves with the global `ConnectionRegistry`.

```text
               +----------------------------------+
               |          BaseConnection          |
               |  - connect(credentials, token)  |
               |  - disconnect()                  |
               |  - is_connected                  |
               |  - service                       |
               +----------------------------------+
                                ^
                                |  inherits
             +------------------+------------------+
             |                                     |
+--------------------------+             +--------------------------+
|     GmailConnection      |             |    CalendarConnection    |
+--------------------------+             +--------------------------+
```

---

## Using the Connection Registry

The `ConnectionRegistry` is a singleton repository for discovering and instantiating connections at runtime.

```python
from clara.connections.registry import registry
from clara.connections.google.gmail import GmailConnection

# 1. Register a connection class (automatically done in connection modules)
registry.register("gmail", GmailConnection)

# 2. Retrieve the active singleton instance
gmail = registry.get_instance("gmail")

# 3. Connect with user OAuth token
gmail.connect(access_token="ya29.a0...")

# 4. Perform service actions
messages = gmail.search_emails(folder="inbox", limit=5)
```

---

## Implementing a Custom Connection

To add an integration for a new service (e.g. GitHub, Slack, Notion):

### 1. Subclass `BaseConnection`

Create a new file `clara/connections/slack/client.py`:

```python
"""Slack Connection Adapter for Clara Core."""

from typing import Optional, Dict, Any
from clara.connections.base import BaseConnection
from clara.connections.registry import registry

class SlackConnection(BaseConnection):
    """Slack API client adapter."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(name="slack", config=config)

    def connect(self, credentials: Optional[str] = None, access_token: Optional[str] = None, **kwargs) -> Any:
        token = access_token or self.config.get("token")
        # Initialize your client SDK or HTTP session here
        self._service = f"SlackClient(token={token})"
        self._is_connected = True
        return self._service

    def disconnect(self) -> None:
        self._service = None
        self._is_connected = False

    def post_message(self, channel: str, text: str) -> Dict[str, Any]:
        """Post a chat message to a Slack channel."""
        # Execute API call using self._service
        return {"status": "ok", "channel": channel, "text": text}

# Register connection in the global registry
registry.register("slack", SlackConnection)
```

### 2. Export and Use

Import your connection in `clara/connections/__init__.py` so it is automatically registered when the module is imported.
