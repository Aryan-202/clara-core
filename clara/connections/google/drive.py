"""Google Drive Connection Module for Clara Core.

This module provides the :class:`DriveConnection` class and helper functions
to interact with the Google Drive API for querying files, reading metadata,
managing folder hierarchies, and searching user documents.
"""

import os
from typing import Any, Dict, List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from clara.conf.google_client_conf import DRIVE_SCOPES
from clara.connections.base import BaseConnection
from clara.connections.registry import registry


def _get_drive_service(
    credentials: Optional[Credentials] = None,
    access_token: Optional[str] = None,
    token_path: str = "token.json",
    client_secrets_file: str = "credentials.json",
) -> Resource:
    """Internal helper to initialize and authenticate Google Drive service.

    Args:
        credentials: An existing Google OAuth2 Credentials object.
        access_token: An OAuth2 bearer token string.
        token_path: Path to stored credentials file.
        client_secrets_file: Path to client_secrets.json for interactive OAuth.

    Returns:
        Resource: Authenticated Google Drive v3 API client resource.
    """
    if credentials is not None:
        return build("drive", "v3", credentials=credentials)

    if access_token:
        creds = Credentials(token=access_token, scopes=DRIVE_SCOPES)
        return build("drive", "v3", credentials=creds)

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(
            token_path, scopes=DRIVE_SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(request=Request())
        elif os.path.exists(client_secrets_file):
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, DRIVE_SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        else:
            return build("drive", "v3", developerKey="")

    return build("drive", "v3", credentials=creds)


def list_files(
    query: Optional[str] = None,
    page_size: int = 10,
    order_by: str = "modifiedTime desc",
    service: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Lists or queries files in Google Drive.

    Args:
        query: Optional Google Drive search query string (e.g.
            "name contains 'Report'").
        page_size: Number of files to return (maximum 100). Defaults to 10.
        order_by: Sorting field and direction. Defaults to
            'modifiedTime desc'.
        service: Optional pre-authenticated Google Drive API client resource.

    Returns:
        List[Dict[str, Any]]: List of file records containing id, name,
        mimeType, modifiedTime, and webViewLink.

    Example:
        >>> files = list_files(query="mimeType = 'application/pdf'", page_size=5)
        >>> for f in files:
        ...     print(f['name'], f['id'])
    """
    svc = service or _get_drive_service()
    fields = (
        "nextPageToken, files(id, name, mimeType, "
        "modifiedTime, size, webViewLink, owners)"
    )
    response = (
        svc.files()
        .list(
            q=query,
            pageSize=page_size,
            fields=fields,
            orderBy=order_by,
        )
        .execute()
    )
    return response.get("files", [])


def get_file_metadata(
    file_id: str,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """Retrieves metadata and properties for a specific Google Drive file.

    Args:
        file_id: Unique Google Drive file identifier.
        service: Optional pre-authenticated Google Drive API client resource.

    Returns:
        Dict[str, Any]: Dictionary containing detailed file metadata.
    """
    svc = service or _get_drive_service()
    fields = (
        "id, name, mimeType, description, size, "
        "modifiedTime, createdTime, webViewLink, webContentLink, parents"
    )
    return svc.files().get(fileId=file_id, fields=fields).execute()


def delete_file(
    file_id: str,
    service: Optional[Any] = None,
) -> Dict[str, Any]:
    """Permanently deletes a file from Google Drive.

    Args:
        file_id: Unique Google Drive file identifier.
        service: Optional pre-authenticated Google Drive API client resource.

    Returns:
        Dict[str, Any]: Deletion confirmation dictionary.
    """
    svc = service or _get_drive_service()
    svc.files().delete(fileId=file_id).execute()
    return {"status": "deleted", "file_id": file_id}


class DriveConnection(BaseConnection):
    """Google Drive connection adapter for Clara.

    Enables agents and skills to search, inspect, upload, and organize
    documents stored in the user's Google Drive.

    Attributes:
        name (str): Connection name identifier ('drive').
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initializes a new Google Drive connection instance.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(name="drive", config=config)

    def connect(
        self,
        credentials: Optional[Credentials] = None,
        access_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Resource:
        """Initializes and authenticates the Google Drive API client.

        Args:
            credentials: Optional OAuth2 Credentials instance.
            access_token: Optional OAuth2 access token string.
            **kwargs: Extra parameters passed to the internal service builder.

        Returns:
            Resource: The active Google Drive Resource client instance.
        """
        token = access_token or self.config.get("access_token")
        self._service = _get_drive_service(
            credentials=credentials,
            access_token=token,
            **kwargs,
        )
        self._is_connected = True
        return self._service

    def disconnect(self) -> None:
        """Closes the connection session and cleans up resources."""
        self._service = None
        self._is_connected = False

    def list_files(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        """Queries files using the active connection."""
        return list_files(*args, service=self.service, **kwargs)

    def get_file_metadata(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Fetches file metadata using the active connection."""
        return get_file_metadata(*args, service=self.service, **kwargs)

    def delete_file(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Deletes a file using the active connection."""
        return delete_file(*args, service=self.service, **kwargs)


# Register drive connection in the global registry
registry.register("drive", DriveConnection)
