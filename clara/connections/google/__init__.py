"""Google Workspace connection adapters for Clara Core.

This package provides service adapters for Google Workspace APIs including:
- :class:`~clara.connections.google.gmail.GmailConnection`
- :class:`~clara.connections.google.calendar.CalendarConnection`
- :class:`~clara.connections.google.drive.DriveConnection`
"""

from clara.connections.google.calendar import CalendarConnection
from clara.connections.google.drive import DriveConnection
from clara.connections.google.gmail import GmailConnection

__all__ = [
    "CalendarConnection",
    "DriveConnection",
    "GmailConnection",
]
