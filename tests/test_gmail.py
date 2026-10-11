"""Unit tests for Gmail connection adapter and API functions.

Covers message construction, recipient normalization, query generation,
CRUD operations with mocks, and the GmailConnection class lifecycle.
"""

import base64
from datetime import datetime
from unittest.mock import MagicMock, patch


from clara.connections.google.gmail import (
    GmailConnection,
    _build_mime_message,
    _build_search_query,
    _collect_attachment_metadata,
    _extract_body_from_payload,
    _normalize_recipients,
    _resolve_date_query,
    _resolve_folder_query,
    create_draft,
    delete_email,
    get_email_content,
    move_email,
    search_emails,
    send_email,
    summarize_thread,
    update_draft,
)
from clara.connections.registry import registry


class TestGmailHelpers:
    """Tests for low-level formatting and query builder helpers."""

    def test_normalize_recipients_none(self):
        assert _normalize_recipients(None) == ""

    def test_normalize_recipients_str(self):
        assert _normalize_recipients("user@example.com") == "user@example.com"

    def test_normalize_recipients_list(self):
        recipients = ["a@example.com", "b@example.com"]
        assert _normalize_recipients(recipients) == "a@example.com, b@example.com"

    def test_resolve_folder_query(self):
        assert _resolve_folder_query("unread") == "is:unread"
        assert _resolve_folder_query("starred") == "is:starred"
        assert _resolve_folder_query("inbox") == "in:inbox"
        assert _resolve_folder_query("trash") == "in:trash"
        assert _resolve_folder_query("custom_label") == "label:custom_label"

    def test_resolve_date_query_datetime(self):
        dt = datetime(2026, 9, 25)
        assert _resolve_date_query(dt) == "after:2026/09/25"

    def test_resolve_date_query_range(self):
        start = datetime(2026, 9, 1)
        end = datetime(2026, 9, 30)
        res = _resolve_date_query((start, end))
        assert res == "after:2026/09/01 before:2026/09/30"

    def test_resolve_date_query_str(self):
        assert _resolve_date_query("2026/09/01") == "after:2026/09/01"
        assert _resolve_date_query("after:2026/01/01") == "after:2026/01/01"

    def test_build_search_query(self):
        q = _build_search_query(
            query="invoice",
            folder="inbox",
            date_range=datetime(2026, 9, 1),
        )
        assert "in:inbox" in q
        assert "after:2026/09/01" in q
        assert "invoice" in q

    def test_build_mime_message_plain(self):
        msg = _build_mime_message(
            to="alice@example.com",
            cc="bob@example.com",
            subject="Hello",
            body="How are you?",
        )
        assert msg["To"] == "alice@example.com"
        assert msg["Cc"] == "bob@example.com"
        assert msg["Subject"] == "Hello"

    def test_build_mime_message_html(self):
        msg = _build_mime_message(
            to="user@example.com",
            subject="HTML Test",
            body="<h1>Hello</h1>",
            is_html=True,
        )
        assert msg["Subject"] == "HTML Test"

    def test_attach_file_dict(self):
        msg = _build_mime_message(
            to="user@example.com",
            subject="Attachment Test",
            body="See attached",
            attachments=[{
                "filename": "note.txt",
                "mime_type": "text/plain",
                "data": base64.b64encode(b"Sample file data").decode("utf-8"),
            }],
        )
        payloads = msg.get_payload()
        assert len(payloads) == 2

    def test_extract_body_from_payload_plain(self):
        encoded = base64.urlsafe_b64encode(b"Hello world").decode("utf-8")
        payload = {
            "mimeType": "text/plain",
            "body": {"data": encoded},
        }
        plain, html = _extract_body_from_payload(payload)
        assert plain == "Hello world"
        assert html == ""

    def test_collect_attachment_metadata(self):
        attachments = []
        payload = {
            "parts": [
                {
                    "filename": "report.pdf",
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "att123", "size": 1024},
                }
            ]
        }
        _collect_attachment_metadata(payload, attachments)
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "report.pdf"
        assert attachments[0]["attachmentId"] == "att123"


class TestGmailOperations:
    """Tests for Gmail CRUD functions with mock API services."""

    def test_send_email_success(self):
        svc = MagicMock()
        mock_send = svc.users.return_value.messages.return_value.send
        mock_send.return_value.execute.return_value = {
            "id": "msg123",
            "threadId": "thr123",
        }

        res = send_email(
            to="bob@example.com",
            subject="Test Subject",
            body="Test Body",
            service=svc,
        )
        assert res["status"] == "sent"
        assert res["id"] == "msg123"
        assert res["to"] == "bob@example.com"

    def test_create_draft_success(self):
        svc = MagicMock()
        mock_draft = svc.users.return_value.drafts.return_value.create
        mock_draft.return_value.execute.return_value = {
            "id": "draft123",
            "message": {"id": "m123"},
        }

        res = create_draft(
            to="carol@example.com",
            subject="Meeting",
            body="Let's meet tomorrow.",
            service=svc,
        )
        assert res["status"] == "draft_created"
        assert res["draft_id"] == "draft123"

    def test_update_draft_success(self):
        svc = MagicMock()
        mock_update = svc.users.return_value.drafts.return_value.update
        mock_update.return_value.execute.return_value = {
            "id": "draft123",
            "message": {"id": "m123"},
        }

        res = update_draft(
            draft_id="draft123",
            new_content="Updated body content",
            subject="Updated Subject",
            service=svc,
        )
        assert res["status"] == "draft_updated"
        assert res["draft_id"] == "draft123"

    def test_search_emails_success(self):
        svc = MagicMock()
        mock_list = svc.users.return_value.messages.return_value.list
        mock_list.return_value.execute.return_value = {
            "messages": [{"id": "msg101", "threadId": "thr101"}]
        }

        mock_get = svc.users.return_value.messages.return_value.get
        mock_get.return_value.execute.return_value = {
            "id": "msg101",
            "threadId": "thr101",
            "snippet": "Hello preview",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Welcome"},
                    {"name": "From", "value": "team@clara.ai"},
                ]
            },
        }

        res = search_emails(query="Welcome", limit=5, service=svc)
        assert len(res) == 1
        assert res[0]["id"] == "msg101"
        assert res[0]["subject"] == "Welcome"
        assert res[0]["from"] == "team@clara.ai"

    def test_get_email_content_success(self):
        svc = MagicMock()
        encoded = base64.urlsafe_b64encode(b"Body content").decode("utf-8")
        mock_get = svc.users.return_value.messages.return_value.get
        mock_get.return_value.execute.return_value = {
            "id": "msg101",
            "threadId": "thr101",
            "snippet": "Snippet preview",
            "payload": {
                "mimeType": "text/plain",
                "body": {"data": encoded},
                "headers": [
                    {"name": "Subject", "value": "Project Status"},
                    {"name": "From", "value": "pm@clara.ai"},
                    {"name": "To", "value": "dev@clara.ai"},
                    {"name": "Date", "value": "2026-09-25"},
                ],
            },
        }

        res = get_email_content("msg101", service=svc)
        assert res["id"] == "msg101"
        assert res["subject"] == "Project Status"
        assert res["from"] == "pm@clara.ai"
        assert res["body"] == "Body content"

    def test_summarize_thread_success(self):
        svc = MagicMock()
        encoded = base64.urlsafe_b64encode(b"Discussion thread").decode("utf-8")
        mock_thread = svc.users.return_value.threads.return_value.get
        mock_thread.return_value.execute.return_value = {
            "messages": [
                {
                    "id": "msg1",
                    "snippet": "First message",
                    "payload": {
                        "mimeType": "text/plain",
                        "body": {"data": encoded},
                        "headers": [
                            {"name": "Subject", "value": "Sprint Sync"},
                            {"name": "From", "value": "lead@clara.ai"},
                        ],
                    },
                }
            ]
        }

        res = summarize_thread("thr101", service=svc)
        assert res["subject"] == "Sprint Sync"
        assert res["message_count"] == 1
        assert "lead@clara.ai" in res["participants"]

    def test_move_email_trash(self):
        svc = MagicMock()
        mock_trash = svc.users.return_value.messages.return_value.trash
        mock_trash.return_value.execute.return_value = {}

        res = move_email("msg101", target_folder="trash", service=svc)
        assert res["status"] == "moved_to_trash"
        assert res["message_id"] == "msg101"

    def test_move_email_archive(self):
        svc = MagicMock()
        mock_mod = svc.users.return_value.messages.return_value.modify
        mock_mod.return_value.execute.return_value = {"labelIds": []}

        res = move_email("msg101", target_folder="archive", service=svc)
        assert res["status"] == "moved"
        assert res["target_folder"] == "archive"

    def test_delete_email_trash(self):
        svc = MagicMock()
        mock_trash = svc.users.return_value.messages.return_value.trash
        mock_trash.return_value.execute.return_value = {}

        res = delete_email("msg101", permanent=False, service=svc)
        assert res["status"] == "trashed"

    def test_delete_email_permanent(self):
        svc = MagicMock()
        mock_del = svc.users.return_value.messages.return_value.delete
        mock_del.return_value.execute.return_value = {}

        res = delete_email("msg101", permanent=True, service=svc)
        assert res["status"] == "permanently_deleted"


class TestGmailConnectionClass:
    """Tests for GmailConnection adapter class lifecycle and delegation."""

    def test_init(self):
        conn = GmailConnection(config={"token": "test_token"})
        assert conn.name == "gmail"
        assert conn.config == {"token": "test_token"}
        assert conn.is_connected is False
        assert conn.service is None

    @patch("clara.connections.google.gmail._get_gmail_service")
    def test_connect_and_disconnect(self, mock_get_svc):
        fake_svc = MagicMock()
        mock_get_svc.return_value = fake_svc

        conn = GmailConnection()
        svc = conn.connect(access_token="mock_token")
        assert svc is fake_svc
        assert conn.is_connected is True
        assert conn.service is fake_svc

        conn.disconnect()
        assert conn.is_connected is False
        assert conn.service is None

    @patch("clara.connections.google.gmail.send_email")
    def test_delegated_send_email(self, mock_send):
        mock_send.return_value = {"status": "sent"}
        conn = GmailConnection()
        conn._service = MagicMock()

        res = conn.send_email(to="user@example.com", subject="Hi")
        assert res["status"] == "sent"
        mock_send.assert_called_once()

    def test_registry_registration(self):
        assert registry.get("gmail") is GmailConnection
        assert registry.get("gmail_assistant") is GmailConnection
        inst = registry.get_instance("gmail")
        assert isinstance(inst, GmailConnection)
