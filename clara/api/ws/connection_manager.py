"""WebSocket Connection Lifetime and Broadcast Manager.

This module provides the :class:`ConnectionManager` class to manage active
WebSocket client connections, connection handshakes, disconnections, and
concurrent message broadcasting with automatic stale connection pruning.
"""

from typing import Any, Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections and client communication.

    Provides mechanisms to accept new client connections, track active
    sockets, send targeted single-client messages, and broadcast events
    to all connected clients.

    Attributes:
        active_connections (List[WebSocket]): A list of currently open and
            active WebSocket client connections.

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket)
        >>> await manager.broadcast({"event": "status", "data": "ready"})
    """

    def __init__(self) -> None:
        """Initializes an empty connection manager with no active clients."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts a incoming WebSocket handshake and tracks the connection.

        Args:
            websocket (WebSocket): The raw FastAPI WebSocket instance.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes a WebSocket from the active connection pool.

        Args:
            websocket (WebSocket): The WebSocket connection instance.

        Raises:
            ValueError: If connection is not found in the active pool.
        """
        self.active_connections.remove(websocket)

    async def send_clara_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ) -> None:
        """Sends a JSON-serialized message to a single specific client.

        Args:
            message (Dict[str, Any]): Dictionary payload to transmit as JSON.
            websocket (WebSocket): Target client WebSocket connection.
        """
        await websocket.send_json(message)

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """Broadcasts a JSON-serializable message to all active clients.

        Automatically detects and prunes disconnected or broken client sockets
        during broadcast iteration.

        Args:
            data (Dict[str, Any]): JSON payload to send to all active clients.
        """
        dead_connections: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data=data)
            except Exception:
                dead_connections.append(connection)

        for conn in dead_connections:
            try:
                self.disconnect(conn)
            except ValueError:
                pass


manager: ConnectionManager = ConnectionManager()
"""Default global connection manager singleton."""
