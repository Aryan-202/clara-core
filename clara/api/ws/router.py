from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
from .event_streamer import EventStreamer


router = APIRouter()

streamer = EventStreamer(manager=manager)


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received message: {data}")

            await websocket.send_json({"status": "received", "echo": data})
            await streamer.broadcast_event("chat_response", {"reply": "Hello!"})

    except WebSocketDisconnect:
        try:
            manager.disconnect(websocket=websocket)
        except ValueError:
            pass
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            manager.disconnect(websocket=websocket)
        except ValueError:
            pass
