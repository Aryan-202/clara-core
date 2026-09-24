"""WebSocket API Router for Clara Real-time Chat and Skill Execution.

This module defines FastAPI WebSocket routing endpoints, message parsing
routines, and automated intent routing to available skills (e.g. Email
Assistant).
"""

from typing import Any, Dict, Optional, Tuple
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from clara.api.ws.connection_manager import manager
from clara.api.ws.event_streamer import EventStreamer
from clara.skills.email_assistant import handle_email_prompt

router: APIRouter = APIRouter()
"""FastAPI APIRouter instance for WebSocket endpoints."""

streamer: EventStreamer = EventStreamer(manager=manager)
"""EventStreamer instance bound to the active WebSocket connection manager."""


def _extract_chat_params(
    data: Any,
) -> Tuple[str, Optional[str], Optional[str], Dict[str, Any]]:
    """Extracts user prompt and execution metadata from raw incoming payloads.

    Args:
        data (Any): Raw deserialized JSON payload from the WebSocket client.

    Returns:
        Tuple[str, Optional[str], Optional[str], Dict[str, Any]]: A 4-tuple:
            - user_prompt (str): The extracted prompt text.
            - access_token (Optional[str]): OAuth or user bearer token.
            - skill (Optional[str]): Targeted skill identifier if specified.
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
        context = data.get("context", {})
        return user_prompt, access_token, skill, context
    return str(data), None, None, {}


def _process_chat_data(data: Any) -> Dict[str, Any]:
    """Processes incoming chat message and dispatches it to skill workflow.

    Args:
        data (Any): Parsed dictionary received from the client.

    Returns:
        Dict[str, Any]: Formatted response payload with reply and data.
    """
    user_prompt, access_token, skill, context = _extract_chat_params(data)
    prompt_lower = user_prompt.lower().strip()

    if prompt_lower == "hello":
        return {"reply": "Hello!"}

    email_keywords = [
        "email", "gmail", "inbox", "draft", "mail",
        "unread", "sent", "trash", "archive",
    ]
    has_email_keyword = any(k in prompt_lower for k in email_keywords)
    if skill == "email_assistant" or has_email_keyword:
        result = handle_email_prompt(
            user_prompt=user_prompt,
            access_token=access_token,
            context=context,
        )
        return {"reply": result.get("reply", "Done."), "data": result}

    result = handle_email_prompt(
        user_prompt=user_prompt,
        access_token=access_token,
        context=context,
    )
    return {"reply": result.get("reply", "Hello!"), "data": result}


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket) -> None:
    """FastAPI WebSocket endpoint for interactive streaming chat with Clara.

    Handles connection acceptance, incoming message loops, live event streaming,
    and graceful disconnection handling.

    Args:
        websocket (WebSocket): Incoming FastAPI WebSocket connection.

    Route:
        ``/ws/chat``
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
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
