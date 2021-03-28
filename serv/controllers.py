from .dependencies import get_token_header

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from fastapi.responses import HTMLResponse

from .managers import manager

html = open('serv/index.html', 'r').read()

router = APIRouter()


@router.get("/")
async def get():
    return HTMLResponse(html)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.request_processing(client_id, data)
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
        # await manager.broadcast(f"Client #{client_id} left the chat")
