"""Unit tests for CalendarConnection and calendar operations in clara.connections.google."""

from unittest.mock import MagicMock, patch
from clara.connections.registry import registry
from clara.connections.google.calendar import (
    CalendarConnection,
    create_event,
    delete_event,
    list_events,
)


class TestCalendarConnection:
    """Test CalendarConnection lifecycle and registry integration."""

    def test_calendar_registration(self):
        conn_cls = registry.get("calendar")
        assert conn_cls == CalendarConnection
        instance = registry.get_instance("calendar")
        assert isinstance(instance, CalendarConnection)

    @patch("clara.connections.google.calendar._get_calendar_service")
    def test_calendar_connect_and_disconnect(self, mock_get_service):
        mock_svc = MagicMock()
        mock_get_service.return_value = mock_svc

        conn = CalendarConnection()
        assert not conn.is_connected
        assert conn.service is None

        svc = conn.connect(access_token="fake_cal_token")
        assert conn.is_connected
        assert conn.service == mock_svc
        assert svc == mock_svc

        conn.disconnect()
        assert not conn.is_connected
        assert conn.service is None


class TestCalendarCRUDOperations:
    """Test Calendar API operation functions."""

    def test_list_events(self):
        mock_svc = MagicMock()
        mock_events = mock_svc.events.return_value
        mock_events.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "ev1",
                    "summary": "Meeting with Bob",
                    "description": "Quarterly planning",
                    "start": {"dateTime": "2026-09-25T10:00:00Z"},
                    "end": {"dateTime": "2026-09-25T11:00:00Z"},
                    "location": "Room 101",
                    "attendees": [{"email": "bob@example.com"}],
                    "htmlLink": "https://calendar.google.com/event?id=ev1",
                }
            ]
        }

        results = list_events(max_results=5, service=mock_svc)
        assert len(results) == 1
        assert results[0]["id"] == "ev1"
        assert results[0]["summary"] == "Meeting with Bob"
        assert results[0]["start"] == "2026-09-25T10:00:00Z"
        assert results[0]["attendees"] == ["bob@example.com"]
        mock_events.list.assert_called_once()

    def test_create_event(self):
        mock_svc = MagicMock()
        mock_events = mock_svc.events.return_value
        mock_events.insert.return_value.execute.return_value = {
            "id": "ev_created",
            "summary": "Team Sync",
            "status": "confirmed",
            "htmlLink": "https://calendar.google.com/event?id=ev_created",
            "start": {"dateTime": "2026-09-25T14:00:00Z"},
            "end": {"dateTime": "2026-09-25T15:00:00Z"},
        }

        result = create_event(
            summary="Team Sync",
            start_time="2026-09-25T14:00:00Z",
            end_time="2026-09-25T15:00:00Z",
            description="Weekly sync",
            location="Online",
            attendees=["colleague@example.com"],
            service=mock_svc,
        )

        assert result["id"] == "ev_created"
        assert result["summary"] == "Team Sync"
        assert result["status"] == "confirmed"
        mock_events.insert.assert_called_once()

    def test_delete_event(self):
        mock_svc = MagicMock()
        mock_events = mock_svc.events.return_value
        mock_events.delete.return_value.execute.return_value = {}

        result = delete_event(event_id="ev_to_delete", service=mock_svc)
        assert result["status"] == "deleted"
        assert result["event_id"] == "ev_to_delete"
        mock_events.delete.assert_called_once_with(
            calendarId="primary", eventId="ev_to_delete"
        )

    def test_calendar_connection_delegates_to_crud(self):
        conn = CalendarConnection()
        mock_svc = MagicMock()
        conn._service = mock_svc
        conn._is_connected = True

        with patch("clara.connections.google.calendar.list_events") as mock_list, \
             patch("clara.connections.google.calendar.create_event") as mock_create, \
             patch("clara.connections.google.calendar.delete_event") as mock_del:

            mock_list.return_value = [{"id": "ev1"}]
            mock_create.return_value = {"id": "ev2"}
            mock_del.return_value = {"status": "deleted"}

            assert conn.list_events(max_results=2) == [{"id": "ev1"}]
            assert conn.create_event(summary="Test", start_time="a", end_time="b") == {"id": "ev2"}
            assert conn.delete_event(event_id="ev1") == {"status": "deleted"}
