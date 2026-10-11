"""Google OAuth 2.0 Authorization and Token Exchange Routines.

This module provides routines to exchange authorization codes (such as Android
serverAuthCode) for OAuth access and refresh tokens, and exposes FastAPI endpoints
for mobile and web client authentication flows.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, Field

from clara.conf.google_client_conf import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_ID_WEB,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_CLIENT_SECRET_WEB,
    TOKEN_URI,
)

router: APIRouter = APIRouter(tags=["auth"])
"""FastAPI router instance for Google OAuth token exchange endpoints."""


class TokenExchangeRequest(BaseModel):
    """Payload schema for exchanging an authorization code."""

    server_auth_code: Optional[str] = Field(
        default=None,
        alias="serverAuthCode",
        description="One-time authorization code received from Android/Web client.",
    )
    code: Optional[str] = Field(
        default=None,
        description="Alternative authorization code key name.",
    )
    client_id: Optional[str] = Field(
        default=None,
        alias="clientId",
        description="Optional OAuth client ID override.",
    )
    client_secret: Optional[str] = Field(
        default=None,
        alias="clientSecret",
        description="Optional OAuth client secret override.",
    )
    redirect_uri: Optional[str] = Field(
        default="",
        alias="redirectUri",
        description="Redirect URI used during initial authorization flow.",
    )

    class Config:
        populate_by_name = True


def exchange_server_auth_code(
    server_auth_code: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    redirect_uri: str = "",
) -> Dict[str, Any]:
    """Exchanges a Google server auth code for access and refresh tokens.

    Args:
        server_auth_code (str): The authorization code received from the client.
        client_id (Optional[str]): OAuth 2.0 Client ID. Defaults to web client ID.
        client_secret (Optional[str]): OAuth 2.0 Client Secret. Defaults to web secret.
        redirect_uri (str): Authorized redirect URI, or empty string for Android.

    Returns:
        Dict[str, Any]: Result dictionary containing access_token, refresh_token,
            expires_in, and token_type on success, or error details on failure.
    """
    if not server_auth_code or not server_auth_code.strip():
        return {
            "status": "error",
            "error": "invalid_request",
            "error_description": "server_auth_code is required.",
        }

    c_id = client_id or GOOGLE_CLIENT_ID_WEB or GOOGLE_CLIENT_ID
    c_secret = (
        client_secret or GOOGLE_CLIENT_SECRET_WEB or GOOGLE_CLIENT_SECRET
    )

    payload = {
        "code": server_auth_code.strip(),
        "client_id": c_id,
        "client_secret": c_secret,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    data_bytes = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URI,
        data=data_bytes,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body)
            return {
                "status": "success",
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "token_type": data.get("token_type", "Bearer"),
                "scope": data.get("scope"),
                "id_token": data.get("id_token"),
            }
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"error": "http_error", "error_description": err_body}
        return {
            "status": "error",
            "error": err_json.get("error", "oauth_exchange_failed"),
            "error_description": err_json.get(
                "error_description", str(err)
            ),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "request_failed",
            "error_description": str(e),
        }


@router.post("/api/auth/google/exchange")
@router.post("/api/auth/exchange")
async def exchange_google_auth_code_endpoint(
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """Endpoint for exchanging Google OAuth authorization code for tokens.

    Supports inputs with `server_auth_code`, `serverAuthCode`, or `code`.

    Args:
        payload (Dict[str, Any]): Incoming JSON request payload.

    Returns:
        Dict[str, Any]: Token dictionary or error response.

    Raises:
        HTTPException: If server_auth_code is missing or exchange fails.
    """
    code = (
        payload.get("server_auth_code")
        or payload.get("serverAuthCode")
        or payload.get("code")
    )
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: server_auth_code",
        )

    client_id = payload.get("client_id") or payload.get("clientId")
    client_secret = payload.get("client_secret") or payload.get("clientSecret")
    redirect_uri = (
        payload.get("redirect_uri") or payload.get("redirectUri") or ""
    )

    result = exchange_server_auth_code(
        server_auth_code=str(code),
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result,
        )

    return result
