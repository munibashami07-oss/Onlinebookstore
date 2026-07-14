"""WebSocket JWT authentication dependency.

Mirrors `get_current_user` / `get_current_active_user` in
`app.security.oauth2`, but adapted for the WebSocket handshake:

- Browsers cannot attach a custom `Authorization` header during the WS
  handshake, so the access token is instead passed as a `token` query
  parameter on the connection URL (e.g. `wss://host/api/v1/ws/chat?token=...`).
- FastAPI HTTP dependencies raise `HTTPException` on failure; WebSocket
  dependencies must raise `WebSocketException` instead, since by the time
  dependency resolution runs the handshake has already been through the
  ASGI accept negotiation. Closing with a policy-violation code lets the
  client reliably detect "auth failed" vs. a generic connection drop and
  decide whether to redirect to login or simply reconnect.

Uses the exact same `verify_token` + `UserRepository` stack as the REST
API, so a token is valid (or invalid) identically across HTTP and WS.
"""

from typing import Optional

from fastapi import Depends, WebSocket, WebSocketException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.jwt import verify_token


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate a WebSocket connection via a JWT access token.

    Args:
        websocket: The incoming WebSocket connection (unused directly here,
            but required by FastAPI to resolve this as a WS dependency).
        token: JWT access token, read from the `?token=` query parameter.
        db: Async DB session.

    Returns:
        Authenticated, active User instance.

    Raises:
        WebSocketException: with code 1008 (policy violation) if the token
            is missing, invalid, expired, belongs to no user, or the user
            account is inactive. The caller (route handler) should let this
            propagate -- FastAPI closes the socket with this code/reason
            before `accept()` is ever called.
    """
    if not token:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token"
        )

    payload = verify_token(token, token_type="access")
    if not payload:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token"
        )

    user_id_str = payload.get("sub")
    if not user_id_str or not user_id_str.isdigit():
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token subject"
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id_str))
    if not user:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
        )
    if not user.is_active:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Inactive user account"
        )

    return user
