"""WebSocket routes for the customer<->admin live chat feature.

Step 2 scope: adds message persistence and one-to-one routing on top of
the Step 1 connection lifecycle. Incoming `type: "message"` payloads are
saved via `ChatMessageRepository` and relayed to the receiver's live
connection(s) through the shared `ConnectionManager`; if the receiver is
offline, the message is still persisted so it shows up next time they
load the conversation (`ConnectionManager.send_to_user` returns False in
that case -- we log it but don't treat it as an error).
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db
from app.dependencies import get_current_active_user
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat import ChatMessageResponse, ConversationResponse
from app.schemas.user import UserPublic
from app.websocket.auth import get_current_user_ws
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket Chat"])
rest_router = APIRouter(prefix="/chat", tags=["Chat"])


@rest_router.get(
    "/support-contact",
    response_model=UserPublic,
    summary="Get the fixed support admin a customer should message",
)
async def get_support_contact(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the single fixed admin used as the customer support contact.

    Single-admin support model: every customer's "Contact support" widget
    messages this same admin account (the lowest-id active admin).
    """
    user_repo = UserRepository(db)
    admin = await user_repo.get_first_admin()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No support admin is currently configured.",
        )
    return admin


@rest_router.get(
    "/conversation/{other_user_id}",
    response_model=List[ChatMessageResponse],
    summary="Get message history with a specific user",
)
async def get_conversation_history(
    other_user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatMessage]:
    """Fetch past messages between the current user and `other_user_id`,
    oldest-first, to seed a chat thread before the WebSocket takes over
    for live messages."""
    repo = ChatMessageRepository(db)
    return await repo.get_conversation(current_user.id, other_user_id, skip=skip, limit=limit)


@rest_router.get(
    "/conversations",
    response_model=List[ConversationResponse],
    summary="List all conversation threads for the current user (inbox view)",
)
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Return every thread the current user is part of, newest activity
    first -- the admin-side inbox listing every customer who has messaged
    in, and equally usable on the customer side if they ever have more
    than one active thread."""
    repo = ChatMessageRepository(db)
    return await repo.get_conversations(current_user.id)


@router.websocket("/chat")
async def chat_websocket(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_ws),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Authenticated WebSocket endpoint for live chat.

    Connect with: `wss://<host>/api/v1/ws/chat?token=<jwt-access-token>`

    If `get_current_user_ws` raises (missing/invalid/expired token, or
    inactive user), FastAPI closes the socket with that reason before this
    function body ever runs -- `websocket.accept()` below only happens for
    an authenticated, active user.

    Supported inbound message types:
        {"type": "ping"}
            -> replies {"type": "pong"}. Client-driven heartbeat, keeps the
               connection alive through idle-timeout proxies.
        {"type": "message", "receiver_id": <int>, "content": <str>}
            -> persists a ChatMessage row and relays it to the receiver's
               live socket(s) if they're online; echoes the saved message
               back to the sender so their own UI can render it with a
               real id/timestamp instead of an optimistic placeholder.
        {"type": "read", "sender_id": <int>}
            -> marks all messages from `sender_id` to the current user as
               read. `sender_id` here is the *other* party in the
               conversation being marked read, not the current user.
    """
    await websocket.accept()
    await manager.connect(current_user.id, websocket)
    repo = ChatMessageRepository(db)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "message":
                await _handle_message(websocket, current_user, data, repo, db)

            elif msg_type == "read":
                await _handle_read(websocket, current_user, data, repo, db)

            else:
                await websocket.send_json(
                    {"type": "error", "detail": f"Unknown message type: {msg_type!r}"}
                )
    except WebSocketDisconnect:
        logger.info("Chat WS disconnected: user_id=%s", current_user.id)
    finally:
        manager.disconnect(current_user.id, websocket)


async def _handle_message(
    websocket: WebSocket,
    current_user: User,
    data: dict,
    repo: ChatMessageRepository,
    db: AsyncSession,
) -> None:
    """Persist an incoming chat message and relay it to the receiver."""
    receiver_id = data.get("receiver_id")
    content = data.get("content")

    if not isinstance(receiver_id, int) or not isinstance(content, str) or not content.strip():
        await websocket.send_json(
            {"type": "error", "detail": "message requires receiver_id (int) and content (str)"}
        )
        return

    if receiver_id == current_user.id:
        await websocket.send_json({"type": "error", "detail": "Cannot message yourself"})
        return

    message = ChatMessage(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
    )

    try:
        message = await repo.create_message(message)
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to persist chat message: sender_id=%s receiver_id=%s",
            current_user.id,
            receiver_id,
        )
        await websocket.send_json({"type": "error", "detail": "Failed to send message"})
        return

    payload = {
        "type": "message",
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "content": message.content,
        "is_read": message.is_read,
        "created_at": message.created_at.isoformat(),
    }

    delivered = await manager.send_to_user(receiver_id, payload)
    if not delivered:
        logger.info(
            "Receiver offline, message stored for later: receiver_id=%s message_id=%s",
            receiver_id,
            message.id,
        )

    # Echo back to the sender (across all their own tabs) so every open tab
    # gets the real persisted row, not just the one that sent it.
    await manager.send_to_user(current_user.id, payload)


async def _handle_read(
    websocket: WebSocket,
    current_user: User,
    data: dict,
    repo: ChatMessageRepository,
    db: AsyncSession,
) -> None:
    """Mark a conversation as read and let the original sender know."""
    sender_id = data.get("sender_id")

    if not isinstance(sender_id, int):
        await websocket.send_json({"type": "error", "detail": "read requires sender_id (int)"})
        return

    try:
        await repo.mark_conversation_read(user_id=current_user.id, from_user_id=sender_id)
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Failed to mark conversation read: user_id=%s from_user_id=%s",
            current_user.id,
            sender_id,
        )
        await websocket.send_json({"type": "error", "detail": "Failed to mark as read"})
        return

    # Let the original sender know their messages were seen, if they're online.
    await manager.send_to_user(
        sender_id,
        {"type": "read", "by_user_id": current_user.id},
    )