"""Base connection interfaces and abstractions for Clara service integrations.

This module defines :class:`BaseConnection`, the foundational abstract class
that all third-party service adapters (such as Google Workspace, GitHub, Slack,
Notion, etc.) must inherit from and implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseConnection(ABC):
    """Abstract base class for all third-party service connections in Clara.

    Subclasses must implement authentication lifecycle methods, session
    management, and service client discovery for external APIs.

    Attributes:
        name (str): Unique identifier for the service connection
            (e.g., 'gmail', 'calendar').
        config (Dict[str, Any]): Configuration dictionary containing service
            parameters, endpoints, scopes, or credentials.
    """

    def __init__(
        self, name: str, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initializes a new service connection instance.

        Args:
            name (str): Unique name identifier for the connection.
            config (Optional[Dict[str, Any]]): Optional dictionary containing
                setup configuration.
        """
        self.name: str = name
        self.config: Dict[str, Any] = config or {}
        self._is_connected: bool = False
        self._service: Optional[Any] = None

    @abstractmethod
    def connect(self, credentials: Optional[Any] = None, **kwargs: Any) -> Any:
        """Authenticates and initializes the underlying service client.

        Args:
            credentials (Optional[Any]): Optional credentials, OAuth tokens,
                or API keys.
            **kwargs (Any): Additional service-specific initialization options.

        Returns:
            Any: The authenticated service client instance (e.g. Google API
            Resource).

        Raises:
            ConnectionError: If authentication or connection initialization
                fails.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnects active session and releases held network resources."""
        pass

    @property
    def is_connected(self) -> bool:
        """Indicates whether the connection is currently established and active.

        Returns:
            bool: True if connected and ready for requests; otherwise False.
        """
        return self._is_connected

    @property
    def service(self) -> Optional[Any]:
        """Provides direct access to the underlying authenticated API client.

        Returns:
            Optional[Any]: The active service client instance, or None if not
            connected.
        """
        return self._service
