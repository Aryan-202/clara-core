"""Connection Registry for Clara Service Integrations.

This module provides the :class:`ConnectionRegistry` singleton and class
to register, instantiate, and look up external service adapters dynamically
at runtime.
"""

from typing import Any, Dict, Optional, Type
from clara.connections.base import BaseConnection


class ConnectionRegistry:
    """Manages active third-party API service integrations and adapters.

    Maintains a catalog of registered connection classes and singleton active
    instances for reuse across Clara skills and agent workflows.

    Attributes:
        _connections (Dict[str, Type[BaseConnection]]): Mapping of lowercased
            connection identifiers to their connection classes.
        _active_instances (Dict[str, BaseConnection]): Mapping of identifiers
            to live, instantiated connection objects.

    Example:
        >>> registry = ConnectionRegistry()
        >>> registry.register("gmail", GmailConnection)
        >>> gmail_client = registry.get_instance("gmail")
    """

    def __init__(self) -> None:
        """Initializes an empty connection registry."""
        self._connections: Dict[str, Type[BaseConnection]] = {}
        self._active_instances: Dict[str, BaseConnection] = {}

    def register(
        self, name: str, connection_cls: Type[BaseConnection]
    ) -> None:
        """Registers a connection class under a unique identifier.

        Args:
            name (str): Identifier for the connection (e.g., 'gmail',
                'calendar', 'drive').
            connection_cls (Type[BaseConnection]): The class object
                inheriting from :class:`~clara.connections.base.BaseConnection`.

        Example:
            >>> registry.register("gmail", GmailConnection)
        """
        self._connections[name.lower()] = connection_cls

    def get(self, name: str) -> Optional[Type[BaseConnection]]:
        """Retrieves a registered connection class by its identifier.

        Args:
            name (str): Identifier for the connection.

        Returns:
            Optional[Type[BaseConnection]]: The connection class if
            registered; otherwise None.
        """
        return self._connections.get(name.lower())

    def get_instance(
        self, name: str, **kwargs: Any
    ) -> Optional[BaseConnection]:
        """Gets an existing instance or instantiates and caches a connection.

        Args:
            name (str): Identifier for the connection.
            **kwargs (Any): Keyword arguments passed to constructor.

        Returns:
            Optional[BaseConnection]: Active connection instance, or None
            if not registered.
        """
        name_key = name.lower()
        if name_key not in self._active_instances:
            conn_cls = self.get(name_key)
            if conn_cls is None:
                return None
            self._active_instances[name_key] = conn_cls(**kwargs)
        return self._active_instances[name_key]

    def list_connections(self) -> Dict[str, Type[BaseConnection]]:
        """Returns a snapshot of all registered connection classes.

        Returns:
            Dict[str, Type[BaseConnection]]: Dictionary of names mapped
            to classes.
        """
        return dict(self._connections)


registry: ConnectionRegistry = ConnectionRegistry()
"""Global default connection registry instance."""
