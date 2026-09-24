"""
Connection registry for managing all external service connections in Clara.
"""

from typing import Dict, Type, Optional
from clara.connections.base import BaseConnection


class ConnectionRegistry:
    """
    Registry for managing available service connections.
    """

    def __init__(self):
        self._connections: Dict[str, Type[BaseConnection]] = {}
        self._active_instances: Dict[str, BaseConnection] = {}

    def register(self, name: str, connection_cls: Type[BaseConnection]) -> None:
        """Register a connection class with a given name."""
        self._connections[name.lower()] = connection_cls

    def get(self, name: str) -> Optional[Type[BaseConnection]]:
        """Retrieve a registered connection class by name."""
        return self._connections.get(name.lower())

    def get_instance(self, name: str, **kwargs) -> Optional[BaseConnection]:
        """Get or create an active instance of a connection."""
        name_key = name.lower()
        if name_key not in self._active_instances:
            conn_cls = self.get(name_key)
            if conn_cls is None:
                return None
            self._active_instances[name_key] = conn_cls(**kwargs)
        return self._active_instances[name_key]

    def list_connections(self) -> Dict[str, Type[BaseConnection]]:
        """Return all registered connection classes."""
        return dict(self._connections)


registry = ConnectionRegistry()
