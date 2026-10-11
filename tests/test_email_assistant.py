"""
Unit tests for Email Assistant skill and workflows.
"""

from unittest.mock import MagicMock, patch

from clara.skills.email_assistant.workflows import EmailAssistantWorkflow


class TestEmailAssistantWorkflow:
    def test_send_email_missing_recipient(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute(
            "send email with subject Meeting and body Hello"
        )

        assert result["status"] == "clarification_needed"
        assert result["action"] == "send_email"
        assert "recipient" in result["reply"].lower()

    def test_send_email_missing_body(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute(
            "send email to test@example.com with subject Hi"
        )

        assert result["status"] == "clarification_needed"
        assert result["action"] == "send_email"
        assert "body" in result["reply"].lower()

    @patch("clara.skills.email_assistant.workflows.send_email")
    def test_send_email_success(self, mock_send):
        mock_send.return_value = {
            "status": "sent",
            "id": "123",
            "to": ["test@example.com"],
            "subject": "Hi",
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        prompt = (
            'send email to test@example.com with subject "Project Update" '
            'saying "Everything looks good"'
        )
        result = workflow.execute(prompt)

        assert result["status"] == "success"
        assert result["action"] == "send_email"
        assert "Email sent to test@example.com" in result["reply"]

    def test_send_email_bulk_guardrail(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        prompt = (
            "send email to u1@a.com, u2@a.com, u3@a.com, u4@a.com, "
            "u5@a.com, u6@a.com with subject Bulk and body Hello all"
        )
        result = workflow.execute(prompt)

        assert result["status"] == "pending_confirmation"
        assert "Pending Confirmation" in result["reply"]
        assert "pending_action" in result["data"]

    @patch("clara.skills.email_assistant.workflows.create_draft")
    def test_create_draft(self, mock_draft):
        mock_draft.return_value = {
            "status": "draft_created",
            "draft_id": "d123",
            "subject": "Meeting",
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        prompt = (
            'draft email to boss@company.com with subject "Meeting" '
            'saying "Can we talk today?"'
        )
        result = workflow.execute(prompt)

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
        mock_delete.return_value = {
            "status": "trashed", "message_id": "m1234567890"
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("delete email message m1234567890")

        assert result["status"] == "success"
        assert result["action"] == "delete_email"
        assert "Trash" in result["reply"]

    def test_delete_email_permanent_confirmation_guardrail(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute(
            "permanently delete email message m1234567890"
        )

        assert result["status"] == "pending_confirmation"
        assert "permanently delete" in result["reply"].lower()

    @patch("clara.skills.email_assistant.workflows.delete_email")
    def test_confirm_pending_delete(self, mock_delete):
        mock_delete.return_value = {
            "status": "permanently_deleted", "message_id": "m1234567890"
        }
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

    @patch("clara.skills.email_assistant.workflows.update_draft")
    def test_update_draft_success(self, mock_update):
        mock_update.return_value = {
            "status": "draft_updated",
            "draft_id": "d123",
            "subject": "Updated Subject",
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        prompt = 'update draft id d123 with body "Updated meeting notes"'
        result = workflow.execute(prompt)

        assert result["status"] == "success"
        assert result["action"] == "update_draft"
        assert "d123" in result["reply"]

    def test_update_draft_missing_draft_id(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("update draft with body new text")

        assert result["status"] == "clarification_needed"
        assert result["action"] == "update_draft"
        assert "draft id" in result["reply"].lower()

    @patch("clara.skills.email_assistant.workflows.summarize_thread")
    def test_summarize_thread_success(self, mock_summarize):
        mock_summarize.return_value = {
            "thread_id": "t1234567890",
            "subject": "Q3 Planning",
            "message_count": 3,
            "participants": ["alice@corp.com", "bob@corp.com"],
            "formatted_thread": "Message 1\nMessage 2\nMessage 3",
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("summarize thread id t1234567890")

        assert result["status"] == "success"
        assert result["action"] == "summarize_thread"
        assert "Q3 Planning" in result["reply"]
        assert "alice@corp.com" in result["reply"]

    def test_summarize_thread_missing_id(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("summarize thread")

        assert result["status"] == "clarification_needed"
        assert result["action"] == "summarize_thread"
        assert "thread/message id" in result["reply"].lower()

    @patch("clara.skills.email_assistant.workflows.move_email")
    def test_move_email_archive(self, mock_move):
        mock_move.return_value = {
            "status": "moved",
            "message_id": "m1234567890",
            "target_folder": "archive",
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("archive email id m1234567890")

        assert result["status"] == "success"
        assert result["action"] == "move_email"
        assert "archive" in result["reply"].lower()

    def test_move_email_missing_id(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("archive email")

        assert result["status"] == "clarification_needed"
        assert result["action"] == "move_email"

    @patch("clara.skills.email_assistant.workflows.send_email")
    def test_confirm_pending_send(self, mock_send):
        mock_send.return_value = {
            "status": "sent",
            "id": "123",
            "to": ["user1@a.com", "user2@a.com"],
            "subject": "Important Announcement",
        }
        workflow = EmailAssistantWorkflow(service=MagicMock())
        context = {
            "pending_action": {
                "name": "send_email",
                "to": ["user1@a.com", "user2@a.com"],
                "subject": "Important Announcement",
                "body": "Hello team",
            }
        }
        result = workflow.execute("yes", context=context)

        assert result["status"] == "success"
        assert result["action"] == "send_email"
        assert "Email sent to user1@a.com, user2@a.com" in result["reply"]

    def test_fallback_intent(self):
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute("what is the weather today")

        assert result["status"] == "clarification_needed"
        assert "Email Assistant" in result["reply"]

    @patch("clara.skills.email_assistant.workflows.send_email")
    def test_error_handling(self, mock_send):
        mock_send.side_effect = RuntimeError("Gmail API rate limit exceeded")
        workflow = EmailAssistantWorkflow(service=MagicMock())
        result = workflow.execute(
            'send email to test@example.com with subject Hi body "Test"'
        )

        assert result["status"] == "error"
        assert "rate limit exceeded" in result["reply"]


class TestGmailAssistantAliases:
    """Test Gmail Assistant aliases and convenience helpers."""

    def test_aliases_export(self):
        from clara.skills import (
            EmailAssistantWorkflow as EAWorkflow,
            GmailAssistantWorkflow as GAWorkflow,
            handle_email_prompt,
            handle_gmail_prompt,
        )
        from clara.skills.gmail_assistant import (
            GmailAssistantWorkflow as DirectGAWorkflow,
            handle_gmail_prompt as direct_handle_gmail,
        )

        assert GAWorkflow is EAWorkflow
        assert DirectGAWorkflow is EAWorkflow
        assert handle_gmail_prompt is handle_email_prompt
        assert direct_handle_gmail is handle_email_prompt

    @patch("clara.skills.email_assistant.workflows.search_emails")
    def test_handle_email_prompt_convenience(self, mock_search):
        mock_search.return_value = []
        from clara.skills import handle_gmail_prompt

        res = handle_gmail_prompt(
            user_prompt="check unread emails",
            service=MagicMock(),
        )
        assert res["status"] == "success"
        assert res["action"] == "search_emails"
