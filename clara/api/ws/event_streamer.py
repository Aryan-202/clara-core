from typing import Any
from .connection_manager import ConnectionManager


class EventStreamer:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def broadcast_event(self, event_type: str, payload: Any):
        """Send an event to all connected clients."""
        event = {
            "type": event_type,
            "payload": payload,
        }
        await self.manager.broadcast(event)

    async def send_to_user(self, user_id: str, event_type: str, payload: Any):
        # TODO: Implement user tracking
        await self.broadcast_event(event_type, payload)
