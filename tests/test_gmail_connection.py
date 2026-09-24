"""
Unit tests for Gmail connection module and BaseConnection.
"""

import base64
from unittest.mock import MagicMock, patch

from clara.connections.registry import ConnectionRegistry
from clara.connections.google.gmail import (
    GmailConnection,
    create_draft,
    delete_email,
    get_email_content,
    move_email,
    search_emails,
    send_email,
    summarize_thread,
    update_draft,
    _build_mime_message,
)


class TestRegistry:
    def test_registry_registration(self):
        reg = ConnectionRegistry()
        reg.register("gmail", GmailConnection)
        assert reg.get("gmail") == GmailConnection
        assert reg.get("GMAIL") == GmailConnection
        assert "gmail" in reg.list_connections()


class TestGmailConnection:
    @patch("clara.connections.google.gmail._get_gmail_service")
    def test_gmail_connect_and_disconnect(self, mock_get_service):
        mock_svc = MagicMock()
        mock_get_service.return_value = mock_svc

        conn = GmailConnection()
        assert not conn.is_connected
        assert conn.service is None

        svc = conn.connect(access_token="fake_token")
        assert conn.is_connected
        assert conn.service == mock_svc
        assert svc == mock_svc

        conn.disconnect()
        assert not conn.is_connected
        assert conn.service is None

    def test_build_mime_message(self):
        msg = _build_mime_message(
            to="user@example.com",
            cc="cc@example.com",
            bcc="bcc@example.com",
            subject="Test Subject",
            body="Hello, World!",
            is_html=False,
        )
        assert msg["To"] == "user@example.com"
        assert msg["Cc"] == "cc@example.com"
        assert msg["Bcc"] == "bcc@example.com"
        assert msg["Subject"] == "Test Subject"


class TestGmailCRUDOperations:
    def test_send_email(self):
        mock_service = MagicMock()
        mock_messages = mock_service.users.return_value.messages.return_value
        mock_messages.send.return_value.execute.return_value = {
            "id": "msg123",
            "threadId": "th123",
        }

        result = send_email(
            to="alice@example.com",
            subject="Hello Alice",
            body="How are you?",
            service=mock_service,
        )

        assert result["status"] == "sent"
        assert result["id"] == "msg123"
        assert result["to"] == "alice@example.com"
        mock_messages.send.assert_called_once()

    def test_create_draft(self):
        mock_service = MagicMock()
        mock_drafts = mock_service.users.return_value.drafts.return_value
        mock_drafts.create.return_value.execute.return_value = {
            "id": "draft123",
            "message": {"id": "msg_draft_1"},
        }

        result = create_draft(
            to="bob@example.com",
            subject="Draft subject",
            body="Draft body",
            service=mock_service,
        )

        assert result["status"] == "draft_created"
        assert result["draft_id"] == "draft123"
        mock_drafts.create.assert_called_once()

    def test_update_draft(self):
        mock_service = MagicMock()
        mock_drafts = mock_service.users.return_value.drafts.return_value
        mock_drafts.update.return_value.execute.return_value = {
            "id": "draft123",
            "message": {"id": "msg_draft_2"},
        }

        result = update_draft(
            draft_id="draft123",
            new_content="Updated content",
            subject="Updated Subject",
            service=mock_service,
        )

        assert result["status"] == "draft_updated"
        assert result["draft_id"] == "draft123"
        mock_drafts.update.assert_called_once()

    def test_search_emails(self):
        mock_service = MagicMock()
        mock_messages = mock_service.users.return_value.messages.return_value
        mock_messages.list.return_value.execute.return_value = {
            "messages": [{"id": "msg1"}, {"id": "msg2"}]
        }
        mock_messages.get.return_value.execute.return_value = {
            "id": "msg1",
            "threadId": "th1",
            "snippet": "Test snippet",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Sub"},
                    {"name": "From", "value": "sender@test.com"},
                    {"name": "To", "value": "me@test.com"},
                    {
                        "name": "Date",
                        "value": "Thu, 24 Sep 2026 12:00:00 +0000",
                    },
                ]
            },
        }

        results = search_emails(
            query="meeting", folder="inbox", limit=5, service=mock_service
        )

        assert len(results) == 2
        assert results[0]["subject"] == "Test Sub"
        assert results[0]["from"] == "sender@test.com"

    def test_get_email_content(self):
        mock_service = MagicMock()
        mock_messages = mock_service.users.return_value.messages.return_value
        encoded_body = base64.urlsafe_b64encode(
            b"This is the email text body"
        ).decode("utf-8")
        mock_messages.get.return_value.execute.return_value = {
            "id": "msg123",
            "threadId": "th123",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Full Email"},
                    {"name": "From", "value": "sender@test.com"},
                    {"name": "To", "value": "receiver@test.com"},
                    {
                        "name": "Date",
                        "value": "Thu, 24 Sep 2026 12:00:00 +0000",
                    },
                ],
                "mimeType": "text/plain",
                "body": {"data": encoded_body},
            },
        }

        content = get_email_content("msg123", service=mock_service)
        assert content["id"] == "msg123"
        assert content["subject"] == "Full Email"
        assert "This is the email text body" in content["body"]

    def test_summarize_thread(self):
        mock_service = MagicMock()
        encoded_body = base64.urlsafe_b64encode(
            b"Thread message 1"
        ).decode("utf-8")
        mock_threads = mock_service.users.return_value.threads.return_value
        mock_threads.get.return_value.execute.return_value = {
            "id": "th123",
            "messages": [
                {
                    "id": "m1",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Project Sync"},
                            {"name": "From", "value": "boss@test.com"},
                            {
                                "name": "Date",
                                "value": "Thu, 24 Sep 2026 10:00:00 +0000",
                            },
                        ],
                        "mimeType": "text/plain",
                        "body": {"data": encoded_body},
                    },
                }
            ],
        }

        thread_info = summarize_thread("th123", service=mock_service)
        assert thread_info["subject"] == "Project Sync"
        assert thread_info["message_count"] == 1
        assert "boss@test.com" in thread_info["participants"]

    def test_move_email(self):
        mock_service = MagicMock()
        mock_messages = mock_service.users.return_value.messages.return_value
        mock_messages.modify.return_value.execute.return_value = {
            "id": "msg123",
            "labelIds": [],
        }

        result = move_email(
            "msg123", target_folder="archive", service=mock_service
        )
        assert result["status"] == "moved"
        assert result["target_folder"] == "archive"

    def test_delete_email_trash_and_permanent(self):
        mock_service = MagicMock()
        mock_messages = mock_service.users.return_value.messages.return_value

        # Trash
        res_trash = delete_email(
            "msg123", permanent=False, service=mock_service
        )
        assert res_trash["status"] == "trashed"
        mock_messages.trash.assert_called_once()

        # Permanent
        res_perm = delete_email(
            "msg123", permanent=True, service=mock_service
        )
        assert res_perm["status"] == "permanently_deleted"
        mock_messages.delete.assert_called_once()
