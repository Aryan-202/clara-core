"""
Gmail Connection Module for Clara Core.

This module handles all Gmail CRUD operations performed by Clara AI assistant on
behalf of the user. User consent and authorization tokens are received via the
Clara mobile app (Android/iOS) or web/desktop OAuth flows.
"""

import base64
import mimetypes
import os
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from clara.conf.google_client_conf import GMAIL_SCOPES
from clara.connections.base import BaseConnection
from clara.connections.registry import registry


def _get_gmail_service(
    credentials: Optional[Credentials] = None,
    access_token: Optional[str] = None,
    token_path: str = "token.json",
    client_secrets_file: str = "credentials.json",
) -> Resource:
    """
    Internal helper to initialize and authenticate the Gmail service.

    Supports direct Credentials object, OAuth access token string,
    or local token/credentials files.
    """
    if credentials is not None:
        return build("gmail", "v1", credentials=credentials)

    if access_token:
        creds = Credentials(token=access_token, scopes=GMAIL_SCOPES)
        return build("gmail", "v1", credentials=creds)

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(
            token_path, scopes=GMAIL_SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(request=Request())
        elif os.path.exists(client_secrets_file):
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        else:
            # Create unauthenticated build for offline/mock environments
            return build("gmail", "v1", developerKey="")

    return build("gmail", "v1", credentials=creds)


def _normalize_recipients(
    recipients: Optional[Union[str, List[str]]]
) -> str:
    """Normalize recipient input to comma-separated string."""
    if not recipients:
        return ""
    if isinstance(recipients, list):
        return ", ".join(recipients)
    return str(recipients)


def _attach_file_or_data(
    message: MIMEMultipart,
    attachment: Union[str, Dict[str, Any]],
) -> None:
    """Helper to attach a single file path or dictionary payload."""
    if isinstance(attachment, str) and os.path.exists(attachment):
        content_type, encoding = mimetypes.guess_type(attachment)
        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)
        with open(attachment, "rb") as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(attachment)
        part.add_header(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
        message.attach(part)
    elif isinstance(attachment, dict) and "data" in attachment:
        filename = attachment.get("filename", "attachment")
        mime_type = attachment.get("mime_type", "application/octet-stream")
        main_type, sub_type = (
            mime_type.split("/", 1)
            if "/" in mime_type
            else ("application", "octet-stream")
        )
        raw_data = attachment["data"]
        if isinstance(raw_data, str):
            raw_data = base64.b64decode(raw_data)
        part = MIMEBase(main_type, sub_type)
        part.set_payload(raw_data)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
        message.attach(part)


def _build_mime_message(
    to: Optional[Union[str, List[str]]] = None,
    cc: Optional[Union[str, List[str]]] = None,
    bcc: Optional[Union[str, List[str]]] = None,
    subject: str = "",
    body: str = "",
    attachments: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None,
    is_html: bool = False,
) -> MIMEMultipart:
    """Helper to construct a MIME message with optional attachments."""
    message = MIMEMultipart()
    message["Subject"] = subject

    if to:
        message["To"] = _normalize_recipients(to)
    if cc:
        message["Cc"] = _normalize_recipients(cc)
    if bcc:
        message["Bcc"] = _normalize_recipients(bcc)

    mime_subtype = "html" if is_html else "plain"
    message.attach(MIMEText(body, mime_subtype, "utf-8"))

    if attachments:
        items = (
            [attachments]
            if isinstance(attachments, (str, dict))
            else attachments
        )
        for att in items:
            _attach_file_or_data(message, att)

    return message


def _extract_body_from_payload(payload: Dict[str, Any]) -> tuple[str, str]:
    """Extract plain text and html bodies recursively from Gmail payload."""
    plain_text = ""
    html_text = ""

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data:
        try:
            decoded = base64.urlsafe_b64decode(body_data).decode(
                "utf-8", errors="replace"
            )
            if "text/plain" in mime_type:
                plain_text += decoded
            elif "text/html" in mime_type:
                html_text += decoded
        except Exception:
            pass

    parts = payload.get("parts", [])
    for part in parts:
        p_text, h_text = _extract_body_from_payload(part)
        if p_text:
            plain_text = (
                (plain_text + "\n" + p_text).strip()
                if plain_text
                else p_text
            )
        if h_text:
            html_text = (
                (html_text + "\n" + h_text).strip() if html_text else h_text
            )

    return plain_text, html_text


def send_email(
    to: Union[str, List[str]],
    cc: Optional[Union[str, List[str]]] = None,
    bcc: Optional[Union[str, List[str]]] = None,
    subject: str = "",
    body: str = "",
    attachments: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None,
    is_html: bool = False,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Send an email message via Gmail.

    Args:
        to: Recipient email address or list of email addresses.
        cc: Optional CC email address or list.
        bcc: Optional BCC email address or list.
        subject: Email subject line.
        body: Email body text (plain text or HTML).
        attachments: Optional file path or list of file paths/attachment dicts.
        is_html: Set to True if body is HTML formatted.
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        Dict containing send status, message ID, thread ID, and recipient.
    """
    svc = service or _get_gmail_service()
    message = _build_mime_message(
        to=to,
        cc=cc,
        bcc=bcc,
        subject=subject,
        body=body,
        attachments=attachments,
        is_html=is_html,
    )
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    sent = (
        svc.users()
        .messages()
        .send(userId="me", body={"raw": raw_message})
        .execute()
    )
    return {
        "status": "sent",
        "id": sent.get("id"),
        "threadId": sent.get("threadId"),
        "to": to,
        "subject": subject,
    }


def create_draft(
    to: Optional[Union[str, List[str]]] = None,
    cc: Optional[Union[str, List[str]]] = None,
    bcc: Optional[Union[str, List[str]]] = None,
    subject: str = "",
    body: str = "",
    attachments: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None,
    is_html: bool = False,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Create a new email draft in Gmail.

    Args:
        to: Optional recipient email address or list.
        cc: Optional CC email address or list.
        bcc: Optional BCC email address or list.
        subject: Email subject line.
        body: Email body text.
        attachments: Optional attachment paths or dictionaries.
        is_html: True if body is HTML formatted.
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        Dict containing draft creation status, draft ID, and message ID.
    """
    svc = service or _get_gmail_service()
    message = _build_mime_message(
        to=to,
        cc=cc,
        bcc=bcc,
        subject=subject,
        body=body,
        attachments=attachments,
        is_html=is_html,
    )
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft = (
        svc.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw_message}})
        .execute()
    )
    return {
        "status": "draft_created",
        "draft_id": draft.get("id"),
        "message_id": draft.get("message", {}).get("id"),
        "subject": subject,
    }


def update_draft(
    draft_id: str,
    new_content: str,
    new_recipients: Optional[Union[str, List[str]]] = None,
    subject: Optional[str] = None,
    cc: Optional[Union[str, List[str]]] = None,
    bcc: Optional[Union[str, List[str]]] = None,
    attachments: Optional[Union[str, List[Any]]] = None,
    is_html: bool = False,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Update an existing email draft in Gmail.

    Args:
        draft_id: The ID of the draft to update.
        new_content: The new body content for the draft.
        new_recipients: Optional updated recipient(s).
        subject: Optional updated subject line.
        cc: Optional updated CC recipient(s).
        bcc: Optional updated BCC recipient(s).
        attachments: Optional updated attachment(s).
        is_html: True if new_content is HTML formatted.
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        Dict containing draft update status and draft ID.
    """
    svc = service or _get_gmail_service()

    current_subject = subject
    current_to = new_recipients
    if current_subject is None or current_to is None:
        try:
            existing = (
                svc.users()
                .drafts()
                .get(userId="me", id=draft_id, format="metadata")
                .execute()
            )
            headers = (
                existing.get("message", {})
                .get("payload", {})
                .get("headers", [])
            )
            header_map = {h["name"].lower(): h["value"] for h in headers}
            if current_subject is None:
                current_subject = header_map.get("subject", "")
            if current_to is None:
                current_to = header_map.get("to", "")
        except Exception:
            if current_subject is None:
                current_subject = ""

    message = _build_mime_message(
        to=current_to,
        cc=cc,
        bcc=bcc,
        subject=current_subject or "",
        body=new_content,
        attachments=attachments,
        is_html=is_html,
    )
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    updated = (
        svc.users()
        .drafts()
        .update(
            userId="me",
            id=draft_id,
            body={"message": {"raw": raw_message}},
        )
        .execute()
    )
    return {
        "status": "draft_updated",
        "draft_id": updated.get("id"),
        "message_id": updated.get("message", {}).get("id"),
        "subject": current_subject,
    }


def _resolve_folder_query(folder: str) -> str:
    """Map folder/label name to Gmail search syntax."""
    f_lower = folder.lower().strip()
    if f_lower in ["unread", "starred", "read", "important"]:
        return f"is:{f_lower}"
    if f_lower in ["inbox", "sent", "trash", "spam", "drafts"]:
        return f"in:{f_lower}"
    return f"label:{folder}"


def _resolve_date_query(date_range: Union[datetime, str, tuple, list]) -> str:
    """Map date range parameter to Gmail search syntax."""
    if isinstance(date_range, datetime):
        return f"after:{date_range.strftime('%Y/%m/%d')}"
    if isinstance(date_range, (tuple, list)) and len(date_range) >= 2:
        start, end = date_range[0], date_range[1]
        s_str = start.strftime("%Y/%m/%d") if isinstance(start, datetime) else start
        e_str = end.strftime("%Y/%m/%d") if isinstance(end, datetime) else end
        return f"after:{s_str} before:{e_str}"
    d_str = str(date_range)
    if "after:" not in d_str and "before:" not in d_str:
        return f"after:{d_str}"
    return d_str


def _build_search_query(
    query: str = "",
    folder: Optional[str] = None,
    date_range: Optional[Union[datetime, str, tuple, list]] = None,
) -> str:
    """Construct Gmail search query string from parameters."""
    query_parts = []
    if folder:
        query_parts.append(_resolve_folder_query(folder))
    if date_range:
        query_parts.append(_resolve_date_query(date_range))
    if query:
        query_parts.append(query)
    return " ".join(query_parts).strip()


def search_emails(
    query: str = "",
    folder: Optional[str] = None,
    date_range: Optional[Union[datetime, str, tuple]] = None,
    limit: int = 10,
    service: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Search for emails in Gmail matching query parameters.

    Args:
        query: Search keywords or query string.
        folder: Optional folder/label (e.g., 'inbox', 'sent', 'unread').
        date_range: Optional date filter.
        limit: Maximum number of results to return (default: 10).
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        List of matching email summaries.
    """
    svc = service or _get_gmail_service()
    final_q = _build_search_query(query, folder, date_range)

    response = (
        svc.users()
        .messages()
        .list(userId="me", q=final_q, maxResults=limit)
        .execute()
    )
    messages = response.get("messages", [])

    results = []
    for msg in messages:
        msg_id = msg["id"]
        try:
            detail = (
                svc.users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
                    format="metadata",
                    metadataHeaders=["Subject", "From", "To", "Date"],
                )
                .execute()
            )
            raw_headers = detail.get("payload", {}).get("headers", [])
            headers = {h["name"].lower(): h["value"] for h in raw_headers}
            results.append({
                "id": msg_id,
                "threadId": detail.get("threadId"),
                "subject": headers.get("subject", "(No Subject)"),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "date": headers.get("date", ""),
                "snippet": detail.get("snippet", ""),
                "labels": detail.get("labelIds", []),
            })
        except Exception:
            results.append({
                "id": msg_id,
                "threadId": msg.get("threadId"),
                "subject": "(Unable to retrieve details)",
                "snippet": "",
            })

    return results


def _collect_attachment_metadata(
    part: Dict[str, Any], attachments: List[Dict[str, Any]]
) -> None:
    """Helper to collect attachment metadata recursively."""
    filename = part.get("filename")
    body = part.get("body", {})
    attachment_id = body.get("attachmentId")
    if filename and (attachment_id or body.get("size", 0) > 0):
        attachments.append({
            "filename": filename,
            "mimeType": part.get("mimeType", ""),
            "size": body.get("size", 0),
            "attachmentId": attachment_id,
        })
    for sub_part in part.get("parts", []):
        _collect_attachment_metadata(sub_part, attachments)


def get_email_content(
    message_id: str,
    format: str = "full",
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Retrieve full content and metadata for a specific email message.

    Args:
        message_id: The unique Gmail message ID.
        format: Format of returned message ('full', 'raw', 'metadata').
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        Dict containing parsed subject, sender, recipients, date, and body.
    """
    svc = service or _get_gmail_service()
    detail = (
        svc.users()
        .messages()
        .get(userId="me", id=message_id, format=format)
        .execute()
    )

    payload = detail.get("payload", {})
    headers = {
        h["name"].lower(): h["value"] for h in payload.get("headers", [])
    }

    plain_text, html_text = _extract_body_from_payload(payload)

    attachments_info: List[Dict[str, Any]] = []
    _collect_attachment_metadata(payload, attachments_info)

    return {
        "id": message_id,
        "threadId": detail.get("threadId"),
        "subject": headers.get("subject", "(No Subject)"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "bcc": headers.get("bcc", ""),
        "date": headers.get("date", ""),
        "body": plain_text or detail.get("snippet", ""),
        "html_body": html_text,
        "snippet": detail.get("snippet", ""),
        "labels": detail.get("labelIds", []),
        "attachments": attachments_info,
    }


def _fetch_thread_messages(
    svc: Any, message_ids: Union[str, List[str]]
) -> List[Dict[str, Any]]:
    """Retrieve list of message dictionaries for a thread or ID list."""
    messages_data = []
    if isinstance(message_ids, str):
        try:
            thread_detail = (
                svc.users()
                .threads()
                .get(userId="me", id=message_ids, format="full")
                .execute()
            )
            for msg in thread_detail.get("messages", []):
                payload = msg.get("payload", {})
                raw_h = payload.get("headers", [])
                headers = {h["name"].lower(): h["value"] for h in raw_h}
                plain_body, _ = _extract_body_from_payload(payload)
                messages_data.append({
                    "id": msg.get("id"),
                    "from": headers.get("from", ""),
                    "to": headers.get("to", ""),
                    "date": headers.get("date", ""),
                    "subject": headers.get("subject", ""),
                    "body": plain_body or msg.get("snippet", ""),
                })
        except Exception:
            single = get_email_content(message_ids, service=svc)
            messages_data.append(single)
    elif isinstance(message_ids, list):
        for mid in message_ids:
            try:
                msg_content = get_email_content(mid, service=svc)
                messages_data.append(msg_content)
            except Exception:
                continue
    return messages_data


def summarize_thread(
    message_ids: Union[str, List[str]],
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Retrieve and format all messages in a thread for summarization.

    Args:
        message_ids: A thread ID string or a list of message ID strings.
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        Dict containing thread subject, participant list, and history.
    """
    svc = service or _get_gmail_service()
    messages_data = _fetch_thread_messages(svc, message_ids)

    participants = set()
    formatted_lines = []
    main_subject = "(No Subject)"

    for idx, msg in enumerate(messages_data, start=1):
        sender = msg.get("from", "Unknown Sender")
        recipient = msg.get("to", "")
        date = msg.get("date", "")
        subject = msg.get("subject", "")
        if subject and main_subject == "(No Subject)":
            main_subject = subject

        if sender:
            participants.add(sender)
        if recipient:
            participants.add(recipient)

        body_snippet = msg.get("body", "").strip()
        formatted_lines.append(
            f"--- Message {idx} ---\n"
            f"From: {sender}\n"
            f"Date: {date}\n\n"
            f"{body_snippet}\n"
        )

    thread_id_val = None
    if isinstance(message_ids, str):
        thread_id_val = message_ids
    elif messages_data:
        thread_id_val = messages_data[0].get("threadId")

    return {
        "thread_id": thread_id_val,
        "subject": main_subject,
        "message_count": len(messages_data),
        "participants": sorted(list(participants)),
        "messages": messages_data,
        "formatted_thread": "\n".join(formatted_lines),
    }


def move_email(
    message_id: str,
    target_folder: str,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Move an email to a specific folder or label.

    Args:
        message_id: The unique Gmail message ID.
        target_folder: The target folder or label name.
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        Dict containing operation status, message ID, and target folder.
    """
    svc = service or _get_gmail_service()
    folder_normalized = target_folder.lower().strip()

    if folder_normalized == "trash":
        svc.users().messages().trash(userId="me", id=message_id).execute()
        return {
            "status": "moved_to_trash",
            "message_id": message_id,
            "target_folder": "trash",
        }

    add_labels = []
    remove_labels = []

    if folder_normalized == "archive":
        remove_labels.append("INBOX")
    elif folder_normalized == "inbox":
        add_labels.append("INBOX")
        remove_labels.extend(["SPAM", "TRASH"])
    elif folder_normalized == "spam":
        add_labels.append("SPAM")
        remove_labels.append("INBOX")
    elif folder_normalized == "starred":
        add_labels.append("STARRED")
    elif folder_normalized == "important":
        add_labels.append("IMPORTANT")
    else:
        add_labels.append(target_folder)

    modified = (
        svc.users()
        .messages()
        .modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": add_labels, "removeLabelIds": remove_labels},
        )
        .execute()
    )

    return {
        "status": "moved",
        "message_id": message_id,
        "target_folder": target_folder,
        "labels": modified.get("labelIds", []),
    }


def delete_email(
    message_id: str,
    parmanent: bool = False,
    permanent: Optional[bool] = None,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Delete an email from Gmail. Supports moving to Trash and permanent deletion.

    Args:
        message_id: The unique Gmail message ID.
        parmanent: Backward compatibility flag for permanent deletion.
        permanent: True for permanent deletion, False to move to Trash.
        service: Optional pre-authenticated Gmail service instance.

    Returns:
        Dict containing operation status and message ID.
    """
    is_permanent = permanent if permanent is not None else parmanent
    svc = service or _get_gmail_service()

    if is_permanent:
        svc.users().messages().delete(userId="me", id=message_id).execute()
        return {"status": "permanently_deleted", "message_id": message_id}
    else:
        svc.users().messages().trash(userId="me", id=message_id).execute()
        return {"status": "trashed", "message_id": message_id}


class GmailConnection(BaseConnection):
    """Clara connection adapter implementation for Google Gmail service.

    Enables agents and workflows to search, read, draft, send, archive,
    and delete emails via the Gmail v1 REST API.

    Attributes:
        name (str): Unique connection identifier ('gmail').
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initializes a new Gmail connection instance.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(name="gmail", config=config)

    def connect(
        self,
        credentials: Optional[Credentials] = None,
        access_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Resource:
        """Authenticates and initializes the Gmail API client service.

        Args:
            credentials: Optional Google OAuth2 Credentials object.
            access_token: Optional OAuth2 access token.
            **kwargs: Extra parameters passed to the service builder.

        Returns:
            Resource: Authenticated Gmail API client resource.
        """
        token = access_token or self.config.get("access_token")
        self._service = _get_gmail_service(
            credentials=credentials,
            access_token=token,
            **kwargs,
        )
        self._is_connected = True
        return self._service

    def disconnect(self) -> None:
        """Disconnects and releases the active Gmail service client."""
        self._service = None
        self._is_connected = False

    def send_email(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Sends an email using the active Gmail service connection."""
        return send_email(*args, service=self.service, **kwargs)

    def create_draft(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Creates a draft using the active Gmail service connection."""
        return create_draft(*args, service=self.service, **kwargs)

    def update_draft(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Updates a draft using the active Gmail service connection."""
        return update_draft(*args, service=self.service, **kwargs)

    def search_emails(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Searches messages using the active Gmail service connection."""
        return search_emails(*args, service=self.service, **kwargs)

    def get_email_content(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Retrieves email content using the active Gmail service connection."""
        return get_email_content(*args, service=self.service, **kwargs)

    def summarize_thread(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Summarizes a message thread using the active Gmail service connection."""
        return summarize_thread(*args, service=self.service, **kwargs)

    def move_email(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Moves an email using the active Gmail service connection."""
        return move_email(*args, service=self.service, **kwargs)

    def delete_email(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Trashes or permanently deletes an email using the active connection."""
        return delete_email(*args, service=self.service, **kwargs)


# Register connection in the global registry
registry.register("gmail", GmailConnection)
