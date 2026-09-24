"""API routing and WebSocket interfaces for Clara Core.

This package exposes the HTTP endpoints and real-time WebSocket interfaces
used to communicate with Clara clients (web, mobile, CLI).
"""

from clara.api.ws.router import router as ws_router

__all__ = [
    "ws_router",
]
