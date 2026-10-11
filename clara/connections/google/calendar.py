"""Google Calendar Connection Module for Clara Core.

This module provides the :class:`CalendarConnection` class and helper functions
to interact with the Google Calendar API for event retrieval, scheduling,
updates, and deletion on behalf of the user.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from clara.conf.google_client_conf import (
    CALENDAR_SCOPES,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    TOKEN_URI,
)
from clara.connections.base import BaseConnection
from clara.connections.registry import registry


def _can_refresh(creds: Credentials) -> bool:
    """Check if credentials have all fields required for refresh."""
    return bool(
        creds.refresh_token
        and creds.token_uri
        and creds.client_id
        and creds.client_secret
    )


def _build_credentials(
    token: Optional[str],
    refresh_token: Optional[str],
    token_uri: str,
    client_id: str,
    client_secret: str,
    scopes: List[str],
) -> Credentials:
    """Build and refresh credentials if needed."""
    creds = Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id or None,
        client_secret=client_secret or None,
        scopes=scopes,
    )
    if not creds.valid and _can_refresh(creds):
        try:
            creds.refresh(Request())
        except Exception:
            pass
    return creds


def _load_stored_credentials(
    token_path: str,
    client_secrets_file: str,
    scopes: List[str],
    client_id: str,
    client_secret: str,
    token_uri: str,
) -> Optional[Credentials]:
    """Load credentials from disk or run local auth flow."""
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes=scopes)
        if creds:
            if not getattr(creds, "client_id", None) and client_id:
                creds._client_id = client_id
            if not getattr(creds, "client_secret", None) and client_secret:
                creds._client_secret = client_secret
            if not getattr(creds, "token_uri", None) and token_uri:
                creds._token_uri = token_uri

    if not creds or not creds.valid:
        if creds and creds.expired and _can_refresh(creds):
            creds.refresh(Request())
        elif os.path.exists(client_secrets_file):
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes
            )
            creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as tf:
                tf.write(creds.to_json())
    return creds


def _get_calendar_service(
    credentials: Optional[Credentials] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    token_uri: Optional[str] = None,
    token_path: str = "token.json",
    client_secrets_file: str = "credentials.json",
) -> Resource:
    """Internal helper to initialize and authenticate Google Calendar service.

    Args:
        credentials: An existing Google OAuth2 Credentials object.
        access_token: An OAuth2 bearer token string.
        refresh_token: An OAuth2 refresh token string.
        client_id: Optional OAuth client ID override.
        client_secret: Optional OAuth client secret override.
        token_uri: Optional OAuth token endpoint URI.
        token_path: Path to stored credentials file.
        client_secrets_file: Path to client_secrets.json for interactive OAuth.

    Returns:
        Resource: Authenticated Google Calendar v3 API client.
    """
    c_id = client_id or GOOGLE_CLIENT_ID
    c_sec = client_secret or GOOGLE_CLIENT_SECRET
    t_uri = token_uri or TOKEN_URI

    if credentials is not None:
        if credentials.expired and _can_refresh(credentials):
            try:
                credentials.refresh(Request())
            except Exception:
                pass
        return build("calendar", "v3", credentials=credentials)

    if access_token or refresh_token:
        creds = _build_credentials(
            access_token, refresh_token, t_uri, c_id, c_sec, CALENDAR_SCOPES
        )
        return build("calendar", "v3", credentials=creds)

    creds = _load_stored_credentials(
        token_path, client_secrets_file, CALENDAR_SCOPES, c_id, c_sec, t_uri
    )
    if not creds or not creds.valid:
        return build("calendar", "v3", developerKey="")

    return build("calendar", "v3", credentials=creds)


def list_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    service: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Lists upcoming events from the specified Google Calendar.

    Args:
        calendar_id: Unique calendar identifier (default is 'primary').
        time_min: Lower bound for an event's end time (ISO-8601 string).
            Defaults to current UTC time if omitted.
        time_max: Upper bound for an event's start time (ISO-8601 string).
        max_results: Maximum number of events to return. Defaults to 10.
        service: Optional pre-authenticated Google Calendar API client.

    Returns:
        List[Dict[str, Any]]: List of calendar event dictionaries containing
        summary, start/end times, location, and event ID.

    Example:
        >>> events = list_events(max_results=5)
        >>> for ev in events:
        ...     print(ev['summary'], ev['start'])
    """
    svc = service or _get_calendar_service()
    if time_min is None:
        time_min = datetime.now(timezone.utc).isoformat()

    events_result = (
        svc.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    items = events_result.get("items", [])
    results: List[Dict[str, Any]] = []
    for item in items:
        start_obj = item.get("start", {})
        end_obj = item.get("end", {})
        start_val = start_obj.get("dateTime") or start_obj.get("date")
        end_val = end_obj.get("dateTime") or end_obj.get("date")
        attendees = [
            a.get("email") for a in item.get("attendees", []) if "email" in a
        ]
        results.append({
            "id": item.get("id"),
            "summary": item.get("summary", "(No title)"),
            "description": item.get("description", ""),
            "start": start_val,
            "end": end_val,
            "location": item.get("location", ""),
            "attendees": attendees,
            "htmlLink": item.get("htmlLink", ""),
        })
    return results


def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    description: str = "",
    location: str = "",
    attendees: Optional[List[str]] = None,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """Creates a new calendar event on Google Calendar.

    Args:
        summary: Title/name of the calendar event.
        start_time: Start date-time formatted in ISO 8601 string.
        end_time: End date-time formatted in ISO 8601 string.
        calendar_id: Target calendar ID. Defaults to 'primary'.
        description: Detailed event description or meeting agenda.
        location: Event location, conference room, or video link.
        attendees: List of email addresses to invite.
        service: Optional pre-authenticated Google Calendar API client.

    Returns:
        Dict[str, Any]: Details of the created event including ID and link.

    Example:
        >>> event = create_event(
        ...     summary="Team Sync",
        ...     start_time="2026-09-25T14:00:00Z",
        ...     end_time="2026-09-25T15:00:00Z",
        ...     attendees=["colleague@example.com"]
        ... )
    """
    svc = service or _get_calendar_service()
    event_body: Dict[str, Any] = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    if attendees:
        event_body["attendees"] = [{"email": email} for email in attendees]

    created = (
        svc.events()
        .insert(calendarId=calendar_id, body=event_body)
        .execute()
    )
    return {
        "id": created.get("id"),
        "summary": created.get("summary"),
        "status": created.get("status"),
        "htmlLink": created.get("htmlLink"),
        "start": created.get("start"),
        "end": created.get("end"),
    }


def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """Deletes an existing event from Google Calendar.

    Args:
        event_id: Unique event identifier to remove.
        calendar_id: Calendar identifier. Defaults to 'primary'.
        service: Optional pre-authenticated Google Calendar API client.

    Returns:
        Dict[str, Any]: Status dictionary indicating successful deletion.
    """
    svc = service or _get_calendar_service()
    svc.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return {
        "status": "deleted",
        "event_id": event_id,
        "calendar_id": calendar_id,
    }


class CalendarConnection(BaseConnection):
    """Google Calendar connection adapter for Clara.

    Enables agents and skills to query calendar schedules, create bookings,
    reschedule events, and coordinate meetings.

    Attributes:
        name (str): Connection name identifier ('calendar').
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initializes a new Google Calendar connection instance.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(name="calendar", config=config)

    def connect(
        self,
        credentials: Optional[Credentials] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Resource:
        """Initializes and authenticates the Google Calendar API client.

        Args:
            credentials: Optional OAuth2 Credentials instance.
            access_token: Optional OAuth2 access token.
            refresh_token: Optional OAuth2 refresh token.
            **kwargs: Extra parameters passed to the internal service builder.

        Returns:
            Resource: The active Google Calendar Resource instance.
        """
        token = access_token or self.config.get("access_token")
        r_token = refresh_token or self.config.get("refresh_token")
        c_id = kwargs.pop("client_id", self.config.get("client_id"))
        c_sec = kwargs.pop("client_secret", self.config.get("client_secret"))
        t_uri = kwargs.pop("token_uri", self.config.get("token_uri"))
        self._service = _get_calendar_service(
            credentials=credentials,
            access_token=token,
            refresh_token=r_token,
            client_id=c_id,
            client_secret=c_sec,
            token_uri=t_uri,
            **kwargs,
        )
        self._is_connected = True
        return self._service

    def disconnect(self) -> None:
        """Closes the connection session and cleans up resources."""
        self._service = None
        self._is_connected = False

    def list_events(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Queries upcoming events using the active connection."""
        return list_events(*args, service=self.service, **kwargs)

    def create_event(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Creates a calendar event using the active connection."""
        return create_event(*args, service=self.service, **kwargs)

    def delete_event(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Deletes a calendar event using the active connection."""
        return delete_event(*args, service=self.service, **kwargs)


# Register calendar connection in the global registry
registry.register("calendar", CalendarConnection)
