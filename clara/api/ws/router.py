"""WebSocket and HTTP API Router for Clara Real-time Chat and Skill Execution.

This module defines FastAPI WebSocket routing endpoints, HTTP fallback routes,
message parsing routines, and automated intent routing to available skills (e.g.
Email/Gmail Assistant) and OpenRouter LLM completions.
"""

import os
from typing import Any, Dict, Optional, Tuple
from fastapi import APIRouter, Body, WebSocket, WebSocketDisconnect
from clara.agent.open_router import OpenRouterClient
from clara.api.ws.connection_manager import manager
from clara.api.ws.event_streamer import EventStreamer
from clara.skills.email_assistant import handle_email_prompt

router: APIRouter = APIRouter()
"""FastAPI APIRouter instance for WebSocket and Chat API endpoints."""

streamer: EventStreamer = EventStreamer(manager=manager)
"""EventStreamer instance bound to the active WebSocket connection manager."""


def _extract_chat_params(
    data: Any,
) -> Tuple[
    str,
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Dict[str, Any],
]:
    """Extracts user prompt and execution metadata from raw incoming payloads.

    Args:
        data (Any): Raw deserialized JSON payload from the client.

    Returns:
        Tuple: A 6-tuple:
            - user_prompt (str): The extracted prompt text.
            - access_token (Optional[str]): OAuth or user bearer token.
            - skill (Optional[str]): Targeted skill identifier if specified.
            - openrouter_key (Optional[str]): Optional OpenRouter API key override.
            - model (Optional[str]): Optional LLM model identifier override.
            - context (Dict[str, Any]): Additional session execution context.
    """
    if isinstance(data, dict):
        user_prompt = (
            data.get("message")
            or data.get("prompt")
            or data.get("text")
            or data.get("content")
            or ""
        )
        access_token = data.get("access_token") or data.get("token")
        skill = data.get("skill")
        openrouter_key = data.get("openrouter_key") or data.get("api_key")
        model = data.get("model")
        context = data.get("context", {})
        return (
            user_prompt,
            access_token,
            skill,
            openrouter_key,
            model,
            context if isinstance(context, dict) else {},
        )
    return str(data), None, None, None, None, {}


def _process_chat_data(data: Any) -> Dict[str, Any]:
    """Processes incoming chat message and dispatches it to skill workflow or LLM.

    Args:
        data (Any): Parsed dictionary received from the client.

    Returns:
        Dict[str, Any]: Formatted response payload with reply and data.
    """
    (
        user_prompt,
        access_token,
        skill,
        openrouter_key,
        model,
        context,
    ) = _extract_chat_params(data)
    prompt_lower = user_prompt.lower().strip()

    if prompt_lower == "hello":
        return {"reply": "Hello!"}

    refresh_token = (
        data.get("refresh_token") if isinstance(data, dict) else None
    )

    email_keywords = [
        "email", "gmail", "inbox", "draft", "mail",
        "unread", "sent", "trash", "archive",
    ]
    has_email_keyword = any(k in prompt_lower for k in email_keywords)
    if (
        skill in ["email_assistant", "gmail_assistant", "gmail"]
        or has_email_keyword
    ):
        result = handle_email_prompt(
            user_prompt=user_prompt,
            access_token=access_token,
            refresh_token=refresh_token,
            context=context,
        )
        return {"reply": result.get("reply", "Done."), "data": result}

    or_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
    if or_key:
        try:
            client = OpenRouterClient(
                api_key=or_key,
                default_model=model,
            )
            response = client.generate_completion(
                messages=[{"role": "user", "content": user_prompt}],
                model=model,
            )
            return {
                "reply": response.content,
                "data": response.raw_response,
            }
        except Exception as e:
            return {
                "reply": f"**Error:** LLM generation failed: {str(e)}",
                "data": {"error": str(e)},
            }

    result = handle_email_prompt(
        user_prompt=user_prompt,
        access_token=access_token,
        refresh_token=refresh_token,
        context=context,
    )
    return {"reply": result.get("reply", "Hello!"), "data": result}


def _extract_handshake_params(
    websocket: WebSocket,
) -> Dict[str, Optional[str]]:
    """Extract auth and config parameters from WebSocket handshake."""
    token = (
        websocket.query_params.get("access_token")
        or websocket.query_params.get("token")
    )
    auth_header = websocket.headers.get("authorization")
    if (
        not token
        and auth_header
        and auth_header.lower().startswith("bearer ")
    ):
        token = auth_header[7:].strip()

    or_key = (
        websocket.query_params.get("openrouter_key")
        or websocket.query_params.get("api_key")
    )
    return {
        "access_token": token,
        "refresh_token": websocket.query_params.get("refresh_token"),
        "openrouter_key": or_key,
        "model": websocket.query_params.get("model"),
    }


def _enrich_incoming_data(
    data: Any, handshake_params: Dict[str, Optional[str]]
) -> Any:
    """Enrich incoming payload with WebSocket handshake parameters."""
    if not isinstance(data, dict):
        return data

    token = handshake_params.get("access_token")
    if token and not data.get("access_token") and not data.get("token"):
        data["access_token"] = token

    r_token = handshake_params.get("refresh_token")
    if r_token and not data.get("refresh_token"):
        data["refresh_token"] = r_token

    or_key = handshake_params.get("openrouter_key")
    if or_key and not data.get("openrouter_key") and not data.get("api_key"):
        data["openrouter_key"] = or_key

    model = handshake_params.get("model")
    if model and not data.get("model"):
        data["model"] = model

    return data


@router.websocket("/ws")
@router.websocket("/ws/")
@router.websocket("/ws/chat")
@router.websocket("/ws/chat/")
async def websocket_chat_endpoint(websocket: WebSocket) -> None:
    """FastAPI WebSocket endpoint for interactive streaming chat with Clara.

    Accepts connections on `/ws` and `/ws/chat`, handling query parameters
    and headers for handshake authentication and client identification.

    Args:
        websocket (WebSocket): Incoming FastAPI WebSocket connection.
    """
    await manager.connect(websocket)
    handshake = _extract_handshake_params(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            data = _enrich_incoming_data(data, handshake)
            await websocket.send_json({"status": "received", "echo": data})
            reply_payload = _process_chat_data(data)
            await streamer.broadcast_event("chat_response", reply_payload)

    except WebSocketDisconnect:
        try:
            manager.disconnect(websocket)
        except ValueError:
            pass
    except Exception:
        try:
            manager.disconnect(websocket)
        except ValueError:
            pass


@router.post("/api/chat")
@router.post("/chat")
async def chat_http_endpoint(
    payload: Dict[str, Any] = Body(...),
) -> Dict[str, Any]:
    """HTTP fallback endpoint for processing chat prompts.

    Args:
        payload (Dict[str, Any]): JSON payload containing user prompt and options.

    Returns:
        Dict[str, Any]: Formatted execution result payload.
    """
    return _process_chat_data(payload)
