"""
Unit tests for Email Assistant skill and workflows.
"""

from unittest.mock import MagicMock, patch
import pytest

from clara.skills.email_assistant.workflows import (
    EmailAssistantWorkflow,
    handle_email_prompt,
)


class TestEmailAssistantWorkflow:
    def test_send_email_missing_recipient(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("send email with subject Meeting and body Hello")

        assert result["status"] == "clarification_needed"
        assert result["action"] == "send_email"
        assert "recipient" in result["reply"].lower()

    def test_send_email_missing_body(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("send email to test@example.com with subject Hi")

        assert result["status"] == "clarification_needed"
        assert result["action"] == "send_email"
        assert "body" in result["reply"].lower()

    @patch("clara.skills.email_assistant.workflows.send_email")
    def test_send_email_success(self, mock_send):
        mock_send.return_value = {"status": "sent", "id": "123", "to": ["test@example.com"], "subject": "Hi"}
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute('send email to test@example.com with subject "Project Update" saying "Everything looks good"')

        assert result["status"] == "success"
        assert result["action"] == "send_email"
        assert "Email sent to test@example.com" in result["reply"]

    def test_send_email_bulk_guardrail(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        prompt = (
            "send email to u1@a.com, u2@a.com, u3@a.com, u4@a.com, u5@a.com, u6@a.com "
            "with subject Bulk and body Hello all"
        )
        result = workflow.execute(prompt)

        assert result["status"] == "pending_confirmation"
        assert "Pending Confirmation" in result["reply"]
        assert "pending_action" in result["data"]

    @patch("clara.skills.email_assistant.workflows.create_draft")
    def test_create_draft(self, mock_draft):
        mock_draft.return_value = {"status": "draft_created", "draft_id": "d123", "subject": "Meeting"}
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute('draft email to boss@company.com with subject "Meeting" saying "Can we talk today?"')

        assert result["status"] == "success"
        assert result["action"] == "create_draft"
        assert "d123" in result["reply"]

    @patch("clara.skills.email_assistant.workflows.search_emails")
    def test_search_emails(self, mock_search):
        mock_search.return_value = [
            {
                "id": "m1234567890",
                "subject": "Invoice",
                "from": "billing@stripe.com",
                "snippet": "Your receipt for March",
                "date": "2026-09-24",
            }
        ]
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("search emails from billing@stripe.com")

        assert result["status"] == "success"
        assert result["action"] == "search_emails"
        assert "Invoice" in result["reply"]
        assert "billing@stripe.com" in result["reply"]

    @patch("clara.skills.email_assistant.workflows.get_email_content")
    def test_read_email(self, mock_get):
        mock_get.return_value = {
            "id": "m1234567890",
            "subject": "Important Announcement",
            "from": "hr@company.com",
            "date": "2026-09-24",
            "body": "Welcome to Clara!",
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("read email id m1234567890")

        assert result["status"] == "success"
        assert result["action"] == "get_email_content"
        assert "Important Announcement" in result["reply"]
        assert "Welcome to Clara!" in result["reply"]

    @patch("clara.skills.email_assistant.workflows.delete_email")
    def test_delete_email_trash(self, mock_delete):
        mock_delete.return_value = {"status": "trashed", "message_id": "m1234567890"}
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("delete email message m1234567890")

        assert result["status"] == "success"
        assert result["action"] == "delete_email"
        assert "Trash" in result["reply"]

    def test_delete_email_permanent_confirmation_guardrail(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("permanently delete email message m1234567890")

        assert result["status"] == "pending_confirmation"
        assert "permanently delete" in result["reply"].lower()

    @patch("clara.skills.email_assistant.workflows.delete_email")
    def test_confirm_pending_delete(self, mock_delete):
        mock_delete.return_value = {"status": "permanently_deleted", "message_id": "m1234567890"}
        workflow = EmailAssistantWorkflow(service=MagicMock())
        context = {
            "pending_action": {
                "name": "delete_email",
                "message_id": "m1234567890",
                "permanent": True,
            }
        }
        result = workflow.execute("yes", context=context)

        assert result["status"] == "success"
        assert "permanently deleted" in result["reply"]

    def test_cancel_pending_action(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        context = {
            "pending_action": {
                "name": "delete_email",
                "message_id": "m1234567890",
            }
        }
        result = workflow.execute("cancel", context=context)

        assert result["status"] == "cancelled"
        assert "Cancelled" in result["reply"]
