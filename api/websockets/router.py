from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()
clients: List[WebSocket] = []

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

async def broadcast_json(data: dict):
    for client in clients.copy():
        try:
            await client.send_json(data)
        except Exception:
            if client in clients:
                clients.remove(client)
