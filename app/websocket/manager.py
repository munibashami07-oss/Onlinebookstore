"""Central WebSocket connection registry.

Tracks all active WebSocket connections keyed by `user_id`, supporting:
- multiple simultaneous connections per user (multiple browser tabs)
- multiple admins online at once
- clean removal of dead sockets on send failure or disconnect

This is the single source of truth for "who is currently connected",
shared by both the chat feature (Feature 1) and the notifications
feature (Feature 2) so there is only one registry to keep consistent.
"""

import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """In-memory registry of active WebSocket connections per user.

    NOTE on horizontal scaling: this registry is process-local. If the app
    runs as multiple worker processes/replicas, each has its own registry,
    so a message meant for a user connected to a *different* worker won't
    be delivered by this class alone. `send_to_user` and `broadcast_to_users`
    are intentionally the only two "fan a message out" entry points used by
    calling code -- when Redis Pub/Sub is introduced later, only the bodies
    of these two methods need to change (publish to a channel instead of/in
    addition to iterating local sockets); no caller in chat.py or
    notifications.py will need to change.
    """

    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Register an already-accepted WebSocket under a user_id."""
        self._connections.setdefault(user_id, set()).add(websocket)
        logger.info(
            "WS connected: user_id=%s active_tabs=%s",
            user_id,
            len(self._connections[user_id]),
        )

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Remove a WebSocket from the registry, cleaning up empty entries.

        Safe to call multiple times / with an already-removed socket.
        """
        connections = self._connections.get(user_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            del self._connections[user_id]
        logger.info("WS disconnected: user_id=%s", user_id)

    def is_online(self, user_id: int) -> bool:
        """Return whether a user currently has at least one active connection."""
        return bool(self._connections.get(user_id))

    def online_user_ids(self) -> Set[int]:
        """Return the set of all currently connected user_ids."""
        return set(self._connections.keys())

    async def send_to_user(self, user_id: int, message: dict) -> bool:
        """Send a JSON message to every active connection (tab) for a user.

        Dead sockets encountered during send are removed from the registry
        automatically so they don't accumulate.

        Returns:
            True if the user had at least one live connection at send time,
            False if the user is offline (caller should fall back to
            "stored but undelivered" semantics -- e.g. relying on the
            unread flag / notification row already persisted in Postgres).
        """
        connections = list(self._connections.get(user_id, ()))
        if not connections:
            return False

        stale = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                logger.warning(
                    "Stale WS for user_id=%s, marking for cleanup", user_id, exc_info=True
                )
                stale.append(ws)

        for ws in stale:
            self.disconnect(user_id, ws)

        return True

    async def broadcast_to_users(self, user_ids: Set[int], message: dict) -> None:
        """Send the same JSON message to multiple users (e.g. all online admins)."""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)


# Process-wide singleton shared by the chat and notification features.
manager = ConnectionManager()
