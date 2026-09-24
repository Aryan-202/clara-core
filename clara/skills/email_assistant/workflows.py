"""
Email Assistant Workflow Module for Clara Core.

Implements the cognitive CRUD loop for email management:
1. Parse Intent (Create, Read, Update, Delete)
2. Extract Entities (Recipients, Subject, Body, Date, Folder, Attachments)
3. Confirm Ambiguity / Guardrails
4. Execute via Gmail Connection tools
5. Format structured markdown response
"""

import re
from typing import Any, Dict, List, Optional

from clara.connections.google.gmail import (
    create_draft,
    delete_email,
    get_email_content,
    move_email,
    search_emails,
    send_email,
    summarize_thread,
    update_draft,
    _get_gmail_service,
)


class EmailAssistantWorkflow:
    """
    Workflow coordinator for processing natural language email requests.
    """

    def __init__(
        self,
        service: Optional[Any] = None,
        access_token: Optional[str] = None,
    ):
        self.service = service
        self.access_token = access_token
        if not self.service and self.access_token:
            self.service = _get_gmail_service(access_token=self.access_token)

    def _ensure_service(self):
        if not self.service:
            self.service = _get_gmail_service(access_token=self.access_token)
        return self.service

    def execute(
        self,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for executing an email assistant request.

        Args:
            user_prompt: Natural language user instruction.
            context: Optional conversation context or previous action state.

        Returns:
            Dict containing status, action, reply (markdown text), and data.
        """
        ctx = context or {}
        prompt_clean = user_prompt.strip()

        # Handle pending confirmations / cancellations
        pending_action = ctx.get("pending_action")
        if pending_action:
            if self._is_confirmation(prompt_clean):
                return self._execute_confirmed_action(pending_action)
            if self._is_cancellation(prompt_clean):
                return {
                    "status": "cancelled",
                    "action": pending_action.get("name", "unknown"),
                    "reply": "**Action Cancelled.** The operation was discarded.",
                    "data": {},
                }

        intent = self._parse_intent(prompt_clean)
        return self._dispatch_intent(intent, prompt_clean, ctx)

    def _dispatch_intent(
        self, intent: str, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch parsed intent to corresponding handler."""
        handlers = {
            "SEND_EMAIL": self._handle_send_email,
            "CREATE_DRAFT": self._handle_create_draft,
            "UPDATE_DRAFT": self._handle_update_draft,
            "READ_EMAIL": self._handle_read_email,
            "SEARCH_EMAILS": self._handle_search_emails,
            "SUMMARIZE_THREAD": self._handle_summarize_thread,
            "MOVE_EMAIL": self._handle_move_email,
            "DELETE_EMAIL": self._handle_delete_email,
        }
        handler = handlers.get(intent, self._handle_fallback)
        try:
            return handler(prompt, ctx)
        except Exception as e:
            return {
                "status": "error",
                "action": intent.lower() if intent else "unknown",
                "reply": f"**Error:** Failed to process email request: {str(e)}",
                "data": {"error": str(e)},
            }

    def _parse_intent(self, prompt: str) -> str:
        """Identify the CRUD operation from the prompt."""
        p = prompt.lower()

        delete_kw = [
            "delete email", "trash email", "remove email", "permanently delete"
        ]
        if any(w in p for w in delete_kw):
            return "DELETE_EMAIL"

        move_kw = ["archive email", "move email", "move to", "label email"]
        if any(w in p for w in move_kw):
            return "MOVE_EMAIL"

        summary_kw = [
            "summarize thread", "thread summary", "summarize conversation"
        ]
        if any(w in p for w in summary_kw):
            return "SUMMARIZE_THREAD"

        update_kw = [
            "update draft", "edit draft", "modify draft", "change draft"
        ]
        if any(w in p for w in update_kw):
            return "UPDATE_DRAFT"

        draft_kw = [
            "create draft", "draft email", "save draft", "write a draft"
        ]
        if any(w in p for w in draft_kw):
            return "CREATE_DRAFT"

        send_kw = [
            "send email", "send an email", "send mail",
            "compose and send", "mail to"
        ]
        if any(w in p for w in send_kw):
            return "SEND_EMAIL"

        read_kw = [
            "read email", "open email", "view email",
            "get email", "show email content"
        ]
        if any(w in p for w in read_kw):
            return "READ_EMAIL"

        search_kw = [
            "search email", "find email", "check email",
            "check inbox", "unread emails", "list emails", "my emails"
        ]
        if any(w in p for w in search_kw):
            return "SEARCH_EMAILS"

        return self._parse_intent_fallback(p)

    def _parse_intent_fallback(self, p: str) -> str:
        """Secondary fallback check for single keyword intents."""
        if "delete" in p or "trash" in p:
            return "DELETE_EMAIL"
        if "draft" in p:
            return "CREATE_DRAFT"
        if "send" in p:
            return "SEND_EMAIL"
        if "read" in p or "content" in p:
            return "READ_EMAIL"
        if any(k in p for k in ["search", "find", "inbox", "emails"]):
            return "SEARCH_EMAILS"
        return "UNKNOWN"

    def _is_confirmation(self, text: str) -> bool:
        t = text.lower()
        affirmative = [
            "yes", "confirm", "proceed", "sure",
            "ok", "do it", "send it", "delete it", "yes, please"
        ]
        return t in affirmative

    def _is_cancellation(self, text: str) -> bool:
        t = text.lower()
        return t in ["no", "cancel", "stop", "abort", "don't", "do not"]

    def _extract_email_address(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        return re.findall(email_pattern, text)

    def _extract_quoted_or_pattern(
        self, text: str, label: str
    ) -> Optional[str]:
        """Extract content after label like 'subject: ...' or 'body: ...'."""
        pattern = rf"{label}\s*:\s*([^,\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip("\"'")
        return None

    def _extract_subject_body(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> tuple[str, str]:
        """Extract subject and body from prompt and context."""
        subject = (
            self._extract_quoted_or_pattern(prompt, "subject")
            or ctx.get("subject", "")
        )
        body = (
            self._extract_quoted_or_pattern(prompt, "body")
            or ctx.get("body", "")
        )

        quotes = re.findall(r'"([^"]*)"', prompt)
        if not subject and len(quotes) >= 1:
            subject = quotes[0]
        if not body and len(quotes) >= 2:
            body = quotes[1]
        elif not body and not quotes:
            body_match = re.search(
                r"(?:saying|that says|with text|body)\s+(.+)",
                prompt,
                re.IGNORECASE,
            )
            if body_match:
                body = body_match.group(1).strip()

        return subject, body

    def _handle_send_email(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle drafting and sending emails."""
        emails = self._extract_email_address(prompt)
        subject, body = self._extract_subject_body(prompt, ctx)

        if not emails and "to" in ctx:
            emails = [ctx["to"]] if isinstance(ctx["to"], str) else ctx["to"]

        if not emails:
            return {
                "status": "clarification_needed",
                "action": "send_email",
                "reply": "Who is the recipient? Please provide their email.",
                "data": {"missing_field": "to"},
            }

        if not body:
            recips = ", ".join(emails)
            return {
                "status": "clarification_needed",
                "action": "send_email",
                "reply": f"What would you like the body to {recips} to say?",
                "data": {
                    "missing_field": "body", "to": emails, "subject": subject
                },
            }

        if not subject:
            subject = "No Subject"

        if len(emails) > 5:
            recips = ", ".join(emails[:5])
            remaining = len(emails) - 5
            return {
                "status": "pending_confirmation",
                "action": "send_email",
                "reply": (
                    f"**Pending Confirmation:** Sending to {len(emails)} "
                    f"recipients.\n\n> **Subject:** {subject}\n"
                    f"> **Recipients:** {recips} and {remaining} others\n\n"
                    "Do you want to proceed? (Reply **Yes** or **Cancel**)"
                ),
                "data": {
                    "pending_action": {
                        "name": "send_email",
                        "to": emails,
                        "subject": subject,
                        "body": body,
                    }
                },
            }

        svc = self._ensure_service()
        result = send_email(to=emails, subject=subject, body=body, service=svc)
        reply = (
            f"**Success:** Email sent to {', '.join(emails)}.\n\n"
            f"> **Subject:** {subject}\n\n"
            f"{body}"
        )
        return {
            "status": "success",
            "action": "send_email",
            "reply": reply,
            "data": result,
        }

    def _handle_create_draft(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle creating drafts."""
        emails = self._extract_email_address(prompt)
        subject = self._extract_quoted_or_pattern(prompt, "subject") or "Draft"
        body = self._extract_quoted_or_pattern(prompt, "body") or ""

        if not body:
            quotes = re.findall(r'"([^"]*)"', prompt)
            if quotes:
                body = quotes[-1]
            else:
                body_match = re.search(
                    r"(?:draft|saying|about)\s+(.+)", prompt, re.IGNORECASE
                )
                body = (
                    body_match.group(1).strip()
                    if body_match
                    else "Draft content"
                )

        svc = self._ensure_service()
        result = create_draft(
            to=emails if emails else None,
            subject=subject,
            body=body,
            service=svc,
        )

        to_str = ", ".join(emails) if emails else "None"
        reply = (
            f"**Success:** Draft created (ID: `{result.get('draft_id')}`).\n\n"
            f"> **Subject:** {subject}\n"
            f"> **To:** {to_str}\n\n"
            f"{body}"
        )
        return {
            "status": "success",
            "action": "create_draft",
            "reply": reply,
            "data": result,
        }

    def _handle_update_draft(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle updating an existing draft."""
        draft_id_match = re.search(
            r"draft\s*(?:id)?\s*[:#]?\s*([a-zA-Z0-9_-]+)",
            prompt,
            re.IGNORECASE,
        )
        draft_id = (
            draft_id_match.group(1) if draft_id_match else ctx.get("draft_id")
        )

        if not draft_id:
            return {
                "status": "clarification_needed",
                "action": "update_draft",
                "reply": "Please specify the draft ID to update.",
                "data": {"missing_field": "draft_id"},
            }

        body = self._extract_quoted_or_pattern(prompt, "body") or ""
        subject = self._extract_quoted_or_pattern(prompt, "subject")
        emails = self._extract_email_address(prompt)

        if not body:
            quotes = re.findall(r'"([^"]*)"', prompt)
            body = quotes[-1] if quotes else prompt

        svc = self._ensure_service()
        result = update_draft(
            draft_id=draft_id,
            new_content=body,
            new_recipients=emails if emails else None,
            subject=subject,
            service=svc,
        )

        return {
            "status": "success",
            "action": "update_draft",
            "reply": f"**Success:** Draft `{draft_id}` has been updated.",
            "data": result,
        }

    def _handle_read_email(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle retrieving full email content."""
        id_match = re.search(
            r"(?:email|message|id)\s*[:#]?\s*([a-zA-Z0-9_-]{10,})",
            prompt,
            re.IGNORECASE,
        )
        message_id = id_match.group(1) if id_match else ctx.get("message_id")

        if not message_id:
            return {
                "status": "clarification_needed",
                "action": "get_email_content",
                "reply": "Which email ID would you like to view?",
                "data": {"missing_field": "message_id"},
            }

        svc = self._ensure_service()
        content = get_email_content(message_id, service=svc)

        reply = (
            f"**Subject:** {content.get('subject')}\n"
            f"**From:** {content.get('from')}\n"
            f"**Date:** {content.get('date')}\n\n"
            f"---\n\n"
            f"{content.get('body', content.get('snippet', ''))}"
        )
        return {
            "status": "success",
            "action": "get_email_content",
            "reply": reply,
            "data": content,
        }

    def _handle_search_emails(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle searching/listing emails."""
        p_lower = prompt.lower()
        folder = None
        for f in ["unread", "starred", "sent", "trash", "inbox"]:
            if f in p_lower:
                folder = f
                break

        clean_query = prompt
        remove_words = [
            "search email", "find email", "check email",
            "list email", "show email", "for", "about", "emails"
        ]
        for w in remove_words:
            clean_query = re.sub(
                rf"\b{w}\b", "", clean_query, flags=re.IGNORECASE
            )
        clean_query = clean_query.strip()

        svc = self._ensure_service()
        results = search_emails(
            query=clean_query, folder=folder, limit=10, service=svc
        )

        if not results:
            reply = "**No emails found** matching your query."
        else:
            lines = [f"**Found {len(results)} email(s):**\n"]
            for item in results:
                sender = item.get("from", "Unknown")
                subject = item.get("subject", "(No Subject)")
                snippet = item.get("snippet", "")
                msg_id = item.get("id", "")
                lines.append(
                    f"- **{subject}** (From: `{sender}` | ID: `{msg_id}`)\n"
                    f"  _{snippet}_"
                )
            reply = "\n".join(lines)

        return {
            "status": "success",
            "action": "search_emails",
            "reply": reply,
            "data": {"count": len(results), "results": results},
        }

    def _handle_summarize_thread(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle thread summarization."""
        id_match = re.search(
            r"(?:thread|message|id)\s*[:#]?\s*([a-zA-Z0-9_-]{10,})",
            prompt,
            re.IGNORECASE,
        )
        thread_id = id_match.group(1) if id_match else ctx.get("thread_id")

        if not thread_id:
            return {
                "status": "clarification_needed",
                "action": "summarize_thread",
                "reply": "Please specify the thread/message ID to summarize.",
                "data": {"missing_field": "thread_id"},
            }

        svc = self._ensure_service()
        thread_info = summarize_thread(thread_id, service=svc)

        participants = ", ".join(thread_info.get("participants", []))
        reply = (
            f"**Thread Summary:** {thread_info.get('subject')}\n"
            f"- **Messages:** {thread_info.get('message_count')}\n"
            f"- **Participants:** {participants}\n\n"
            f"**History:**\n{thread_info.get('formatted_thread')}"
        )
        return {
            "status": "success",
            "action": "summarize_thread",
            "reply": reply,
            "data": thread_info,
        }

    def _handle_move_email(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle archiving or moving email."""
        id_match = re.search(
            r"(?:email|message|id)\s*[:#]?\s*([a-zA-Z0-9_-]{10,})",
            prompt,
            re.IGNORECASE,
        )
        message_id = id_match.group(1) if id_match else ctx.get("message_id")

        p_lower = prompt.lower()
        target = "archive"
        for t in ["spam", "inbox", "trash", "starred"]:
            if t in p_lower:
                target = t
                break

        if not message_id:
            return {
                "status": "clarification_needed",
                "action": "move_email",
                "reply": f"Which email ID would you like to move to {target}?",
                "data": {
                    "missing_field": "message_id", "target_folder": target
                },
            }

        svc = self._ensure_service()
        result = move_email(message_id, target_folder=target, service=svc)

        return {
            "status": "success",
            "action": "move_email",
            "reply": f"**Success:** Moved email `{message_id}` to **{target}**.",
            "data": result,
        }

    def _handle_delete_email(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle deleting or trashing an email with safety guardrails."""
        id_match = re.search(
            r"(?:email|message|id)\s*[:#]?\s*([a-zA-Z0-9_-]{10,})",
            prompt,
            re.IGNORECASE,
        )
        message_id = id_match.group(1) if id_match else ctx.get("message_id")
        permanent = "permanent" in prompt.lower()

        if not message_id:
            return {
                "status": "clarification_needed",
                "action": "delete_email",
                "reply": "Please specify the email ID you want to delete.",
                "data": {"missing_field": "message_id"},
            }

        if permanent:
            return {
                "status": "pending_confirmation",
                "action": "delete_email",
                "reply": (
                    f"**Pending Confirmation:** Are you sure you want to "
                    f"**permanently delete** email `{message_id}`?\n"
                    "This action cannot be undone. (Reply **Yes** or **Cancel**)"
                ),
                "data": {
                    "pending_action": {
                        "name": "delete_email",
                        "message_id": message_id,
                        "permanent": True,
                    }
                },
            }

        svc = self._ensure_service()
        result = delete_email(message_id, permanent=False, service=svc)
        return {
            "status": "success",
            "action": "delete_email",
            "reply": f"**Success:** Moved email `{message_id}` to Trash.",
            "data": result,
        }

    def _execute_confirmed_action(
        self, pending_action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a previously held action after user confirmation."""
        action_name = pending_action.get("name")
        svc = self._ensure_service()

        if action_name == "send_email":
            result = send_email(
                to=pending_action["to"],
                subject=pending_action.get("subject", ""),
                body=pending_action.get("body", ""),
                service=svc,
            )
            recips = ", ".join(pending_action["to"])
            return {
                "status": "success",
                "action": "send_email",
                "reply": f"**Success:** Email sent to {recips}.",
                "data": result,
            }
        if action_name == "delete_email":
            mid = pending_action["message_id"]
            result = delete_email(
                message_id=mid,
                permanent=pending_action.get("permanent", True),
                service=svc,
            )
            return {
                "status": "success",
                "action": "delete_email",
                "reply": f"**Success:** Email `{mid}` permanently deleted.",
                "data": result,
            }

        return {
            "status": "error",
            "action": action_name or "unknown",
            "reply": "**Error:** Unknown confirmed action.",
            "data": {},
        }

    def _handle_fallback(
        self, prompt: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback handler when intent is ambiguous."""
        return {
            "status": "clarification_needed",
            "action": "unknown",
            "reply": (
                "I am Clara's Email Assistant. You can ask me to:\n"
                "- **Send or draft** emails (`send email to user@example.com "
                "with subject Hi and body Hello`)\n"
                "- **Search or check** your inbox (`check unread emails`)\n"
                "- **Read** an email by ID (`read email <id>`)\n"
                "- **Summarize** a thread (`summarize thread <id>`)\n"
                "- **Archive or delete** emails (`delete email <id>`)"
            ),
            "data": {},
        }


def handle_email_prompt(
    user_prompt: str,
    access_token: Optional[str] = None,
    service: Optional[Any] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to run the Email Assistant workflow on a prompt.
    """
    workflow = EmailAssistantWorkflow(
        service=service, access_token=access_token
    )
    return workflow.execute(user_prompt=user_prompt, context=context)
