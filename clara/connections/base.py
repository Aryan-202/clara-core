"""
Base connection class for Clara service integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseConnection(ABC):
    """
    Abstract base class for all third-party service connections in Clara.

    Subclasses should implement authentication, session management,
    and service discovery.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._is_connected = False
        self._service = None

    @abstractmethod
    def connect(self, credentials: Optional[Any] = None) -> Any:
        """
        Authenticate and initialize the underlying service client.

        Args:
            credentials: Optional credentials or access token.

        Returns:
            The authenticated service client instance.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect and release any held resources or sessions."""
        pass

    @property
    def is_connected(self) -> bool:
        """Return True if connection is established and active."""
        return self._is_connected

    @property
    def service(self) -> Any:
        """Return the active service client instance."""
        return self._service
