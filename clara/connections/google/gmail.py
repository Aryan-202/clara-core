"""
This module will handle all the crud operations done by ai agent according to user need.

All required consent will be taken via Clara mobile app, user needs to agree all terms
and condition before using this feature of Clara.
"""
import datetime


def send_email(
    to: str, cc: str, bcc: str, subject: str, body: str, attachments: str
) -> None:
    pass


def search_emails(query: str, folder: str, date_range: datetime, limit: int) -> None:
    pass


def get_email_content(message_id: str):
    pass


def summarize_thread(message_ids: str) -> str:
    pass


def update_draft(draft_id: str, new_content: str, new_recipients: str):
    pass


def move_email(message_id: str, target_folder: str):
    pass


def delete_email(message_id: str, parmanent: bool = False):
    pass
