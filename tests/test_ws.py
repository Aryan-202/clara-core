import importlib
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from clara.main import clara
from clara.api.ws.connection_manager import ConnectionManager
from clara.api.ws.event_streamer import EventStreamer
from clara.api.ws.router import websocket_chat_endpoint


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(clara)


@pytest.fixture
def clean_connections():
    """Clear websocket connections before and after each endpoint test."""
    router_module = importlib.import_module("clara.api.ws.router")
    router_module.manager.active_connections.clear()
    yield
    router_module.manager.active_connections.clear()


class TestConnectionManager:
    """Test the websocket connection manager."""

    def test_initializes_without_connections(self):
        """Create a manager with an empty active connection list."""
        manager = ConnectionManager()

        assert manager.active_connections == []

    @pytest.mark.asyncio
    async def test_connect_accepts_and_tracks_connection(self):
        """Accept a websocket and add it to the active connections."""
        websocket = AsyncMock()
        manager = ConnectionManager()

        await manager.connect(websocket)

        websocket.accept.assert_awaited_once_with()
        assert manager.active_connections == [websocket]

    def test_disconnect_removes_connection(self):
        """Remove an existing websocket from the active connections."""
        websocket = object()
        manager = ConnectionManager()
        manager.active_connections.append(websocket)

        manager.disconnect(websocket)

        assert manager.active_connections == []

    def test_disconnect_raises_for_unknown_connection(self):
        """Raise ValueError when removing an unknown websocket."""
        manager = ConnectionManager()

        with pytest.raises(ValueError):
            manager.disconnect(object())

    @pytest.mark.asyncio
    async def test_send_clara_message_sends_json_to_one_connection(self):
        """Send the provided message to a single websocket."""
        websocket = AsyncMock()
        manager = ConnectionManager()
        message = {"type": "status", "payload": {"ready": True}}

        await manager.send_clara_message(message, websocket)

        websocket.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_sends_data_to_every_connection(self):
        """Send a broadcast payload to every active websocket."""
        connections = [AsyncMock(), AsyncMock()]
        manager = ConnectionManager()
        manager.active_connections.extend(connections)
        data = {"type": "update", "payload": 1}

        await manager.broadcast(data)

        for connection in connections:
            connection.send_json.assert_awaited_once_with(data=data)
        assert manager.active_connections == connections

    @pytest.mark.asyncio
    async def test_broadcast_removes_connections_that_fail(self):
        """Remove connections that raise while receiving a broadcast."""
        working_connection = AsyncMock()
        failed_connection = AsyncMock()
        failed_connection.send_json.side_effect = RuntimeError("closed")
        manager = ConnectionManager()
        manager.active_connections.extend([working_connection, failed_connection])

        await manager.broadcast({"type": "update"})

        working_connection.send_json.assert_awaited_once_with(data={"type": "update"})
        failed_connection.send_json.assert_awaited_once_with(data={"type": "update"})
        assert manager.active_connections == [working_connection]


class TestEventStreamer:
    """Test event broadcasting and user event delegation."""

    @pytest.mark.asyncio
    async def test_broadcast_event_builds_event_payload(self):
        """Broadcast an event containing its type and payload."""
        manager = AsyncMock()
        streamer = EventStreamer(manager)
        payload = {"message": "hello"}

        await streamer.broadcast_event("notification", payload)

        manager.broadcast.assert_awaited_once_with(
            {"type": "notification", "payload": payload}
        )

    @pytest.mark.asyncio
    async def test_send_to_user_delegates_to_broadcast_event(self, monkeypatch):
        """Delegate user events to the common event broadcasting method."""
        manager = ConnectionManager()
        streamer = EventStreamer(manager)
        broadcast_event = AsyncMock()
        monkeypatch.setattr(streamer, "broadcast_event", broadcast_event)
        payload = {"message": "hello"}

        await streamer.send_to_user("user-1", "notification", payload)

        broadcast_event.assert_awaited_once_with("notification", payload)


def test_websocket_chat_endpoint_is_registered():
    """Register the chat websocket endpoint on the websocket router."""
    router_module = importlib.import_module("clara.api.ws.router")
    paths = {route.path for route in router_module.router.routes}

    assert "/ws/chat" in paths


def test_websocket_chat_endpoint_echoes_and_broadcasts(client, clean_connections):
    """Echo a received message and broadcast the chat response."""
    with client.websocket_connect("/ws/chat") as websocket:
        message = {"message": "hello"}

        websocket.send_json(message)

        assert websocket.receive_json() == {
            "status": "received",
            "echo": message,
        }
        assert websocket.receive_json() == {
            "type": "chat_response",
            "payload": {"reply": "Hello!"},
        }


def test_websocket_chat_endpoint_disconnects_cleanly(client, clean_connections):
    """Remove a websocket connection after the client disconnects."""
    with client.websocket_connect("/ws/chat") as websocket:
        websocket.send_json({"message": "hello"})
        websocket.receive_json()
        websocket.receive_json()

    from clara.api.ws.router import manager

    assert manager.active_connections == []


@pytest.mark.asyncio
async def test_websocket_chat_endpoint_cleans_up_unexpected_errors(monkeypatch):
    """Remove a connection when an unexpected endpoint error occurs."""
    websocket = AsyncMock()
    websocket.receive_json.side_effect = RuntimeError("receive failed")
    manager = Mock()
    manager.connect = AsyncMock()
    router_module = importlib.import_module("clara.api.ws.router")
    monkeypatch.setattr(router_module, "manager", manager)

    await websocket_chat_endpoint(websocket)

    manager.connect.assert_awaited_once_with(websocket)
    manager.disconnect.assert_called_once_with(websocket)


def test_websocket_chat_endpoint_processes_email_assistant_request(client, clean_connections, monkeypatch):
    """Test receiving an email assistant prompt from an Android/mobile client over websocket."""
    from unittest.mock import MagicMock
    mock_workflow = MagicMock()
    mock_workflow.return_value = {
        "status": "success",
        "action": "send_email",
        "reply": "**Success:** Email sent to user@example.com.",
    }
    router_mod = importlib.import_module("clara.api.ws.router")
    monkeypatch.setattr(router_mod, "handle_email_prompt", mock_workflow)

    with client.websocket_connect("/ws/chat") as websocket:
        message = {
            "message": "send email to user@example.com with subject Hi and body Hello",
            "access_token": "mock_google_token",
            "skill": "email_assistant",
        }
        websocket.send_json(message)

        assert websocket.receive_json() == {
            "status": "received",
            "echo": message,
        }
        response = websocket.receive_json()
        assert response["type"] == "chat_response"
        assert "Success" in response["payload"]["reply"]

