"""WebSocket routes for the customer<->admin live chat feature.

Step 1 scope: authenticated connection lifecycle only -- accept, register
in the ConnectionManager, keep alive via client-driven ping/pong, and clean
up on disconnect. Message persistence, one-to-one routing rules,
read/unread state, and typing indicators are added in Step 2 once
`ChatMessage` (model + repository + service) exists, so the route body
below stays deliberately thin per the project's existing convention.
"""

import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.models.user import User
from app.websocket.auth import get_current_user_ws
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket Chat"])


@router.websocket("/chat")
async def chat_websocket(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
) -> None:
    """Authenticated WebSocket endpoint for live chat.

    Connect with: `wss://<host>/api/v1/ws/chat?token=<jwt-access-token>`

    If `get_current_user_ws` raises (missing/invalid/expired token, or
    inactive user), FastAPI closes the socket with that reason before this
    function body ever runs -- `websocket.accept()` below only happens for
    an authenticated, active user.
    """
    await websocket.accept()
    await manager.connect(current_user.id, websocket)

    try:
        while True:
            # Placeholder receive loop for Step 1: proves the connection
            # survives idle periods via client-sent heartbeats, and that
            # reconnect + multiple tabs both register correctly in the
            # ConnectionManager. Real message envelopes (chat messages,
            # typing indicators, read receipts) are handled here in Step 2.
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.info("Chat WS disconnected: user_id=%s", current_user.id)
    finally:
        manager.disconnect(current_user.id, websocket)
