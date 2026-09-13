"""
WebSocket connection manager for FastAPI applications.

This module provides a simple connection manager to handle active WebSocket
connections, accept new connections, disconnect clients, and broadcast messages
to all connected clients while automatically cleaning up broken connections.
"""

from fastapi import WebSocket
from typing import List, Dict, Any


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Attributes:
        active_connections (List[WebSocket]): A list of currently active
            WebSocket connections.
    """

    def __init__(self):
        """Initialize an empty list of active connections."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept a new WebSocket connection and add it to the active list.

        Args:
            websocket (WebSocket): The WebSocket instance to accept.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the active list.

        Args:
            websocket (WebSocket): The WebSocket instance to remove.

        Raises:
            ValueError: If the connection is not found in the active list.
        """
        self.active_connections.remove(websocket)

    async def send_clara_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a single client."""
        await websocket.send_json(message)

    async def broadcast(self, data: dict):
        """
        Send a JSON message to all active clients.

        If sending to a client fails (e.g., due to a closed connection), the
        client is marked for removal and will be disconnected after the loop.

        Args:
            data (dict): The JSON-serializable data to send to all clients.
        """
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data=data)
            except Exception:
                dead_connections.append(connection)

        for conn in dead_connections:
            self.disconnect(conn)


manager = ConnectionManager()
