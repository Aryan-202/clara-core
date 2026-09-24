"""Real-time Event Streaming Module for Clara WebSocket Clients.

This module provides the :class:`EventStreamer` class to format, wrap, and
stream real-time agent progress events, execution updates, and response
payloads to connected frontends.
"""

from typing import Any, Dict
from clara.api.ws.connection_manager import ConnectionManager


class EventStreamer:
    """Streams structured real-time events over active WebSocket connections.

    Wraps raw application messages into consistent typed envelopes and
    broadcasts them to clients via a
    :class:`~clara.api.ws.connection_manager.ConnectionManager`.

    Attributes:
        manager (ConnectionManager): The WebSocket connection manager used for
            transmission.

    Example:
        >>> streamer = EventStreamer(manager=manager)
        >>> await streamer.broadcast_event("agent_thinking", {"step": 1})
    """

    def __init__(self, manager: ConnectionManager) -> None:
        """Initializes the event streamer with a connection manager.

        Args:
            manager (ConnectionManager): Connection manager instance to route
                events through.
        """
        self.manager: ConnectionManager = manager

    async def broadcast_event(self, event_type: str, payload: Any) -> None:
        """Publishes a typed event payload to all connected clients.

        Args:
            event_type (str): Type tag identifying the event (e.g.,
                'chat_response', 'agent_status').
            payload (Any): JSON-serializable data payload associated with
                the event.
        """
        event: Dict[str, Any] = {
            "type": event_type,
            "payload": payload,
        }
        await self.manager.broadcast(event)

    async def send_to_user(
        self, user_id: str, event_type: str, payload: Any
    ) -> None:
        """Publishes an event targeted to a specific user.

        Args:
            user_id (str): Unique user identifier.
            event_type (str): Type tag identifying the event.
            payload (Any): Data payload associated with the event.
        """
        # User tracking implementation hook; broadcasts by default
        await self.broadcast_event(event_type, payload)
