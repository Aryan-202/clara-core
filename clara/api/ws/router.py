from typing import Any, Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
from .event_streamer import EventStreamer
from clara.skills.email_assistant import handle_email_prompt

router = APIRouter()
streamer = EventStreamer(manager=manager)


def _extract_chat_params(
    data: Any,
) -> tuple[str, Optional[str], Optional[str], Dict[str, Any]]:
    """Extract user prompt and metadata from websocket payload."""
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
    """Process incoming chat data and generate response payload."""
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
async def websocket_chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received message: {data}")

            await websocket.send_json({"status": "received", "echo": data})
            reply_payload = _process_chat_data(data)
            await streamer.broadcast_event("chat_response", reply_payload)

    except WebSocketDisconnect:
        try:
            manager.disconnect(websocket)
        except ValueError:
            pass
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            manager.disconnect(websocket)
        except ValueError:
            pass
