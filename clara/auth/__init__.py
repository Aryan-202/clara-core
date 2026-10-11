"""Authentication and Authorization Module for Clara Core.

Provides OAuth 2.0 exchange routines and session management helpers.
"""

from clara.auth.google import (
    TokenExchangeRequest,
    exchange_server_auth_code,
    router as auth_router,
)

__all__ = [
    "TokenExchangeRequest",
    "exchange_server_auth_code",
    "auth_router",
]
