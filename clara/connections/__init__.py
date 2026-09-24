"""Service connection adapters and registry for Clara Core.

This package manages integrations with external services such as Google Workspace
(Gmail, Calendar, Drive) and other third-party API providers.
"""

from clara.connections.base import BaseConnection
from clara.connections.registry import ConnectionRegistry, registry

__all__ = [
    "BaseConnection",
    "ConnectionRegistry",
    "registry",
]
