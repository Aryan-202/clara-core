from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import ConnectionManager
from .event_streamer import EventStreamer


router = APIRouter()
manager = ConnectionManager()
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
        manager.disconnect(websocket)
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        manager.disconnect(websocket)
