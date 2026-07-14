/**
 * useChatSocket
 * -----------------------------------------------------------------------
 * Connects to `wss://<host>/api/v1/ws/chat?token=<jwt>` and mirrors the
 * message protocol implemented in the backend's `chat.py`:
 *
 *   send  {"type": "ping"}                                   -> heartbeat
 *   send  {"type": "message", receiver_id, content}           -> send msg
 *   send  {"type": "read", sender_id}                         -> mark read
 *   recv  {"type": "pong"}
 *   recv  {"type": "message", id, sender_id, receiver_id,
 *          content, is_read, created_at}
 *   recv  {"type": "read", by_user_id}
 *   recv  {"type": "error", detail}
 *
 * Handles reconnect with backoff and a 25s ping so idle-timeout proxies
 * don't drop the connection.
 *
 * IMPORTANT: this only handles the *live* stream. It does not load
 * message history -- pair it with a REST call to your conversation
 * history endpoint (GET .../chat/conversation/{otherUserId}) on mount,
 * and seed `initialMessages` with the result, so the thread isn't empty
 * every time the component mounts.
 */
import { useState, useEffect, useRef, useCallback } from "react";

export function useChatSocket({
  token,
  wsUrl,
  currentUserId,
  otherUserId,
  initialMessages = [],
}) {
  const [messages, setMessages] = useState(initialMessages);
  const [status, setStatus] = useState("connecting"); // connecting | open | closed | error
  const wsRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!token || !otherUserId) return;
    setStatus("connecting");

    const ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setStatus("open");
      reconnectAttempts.current = 0;

      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 25000);

      // Clear unread badge for this thread as soon as it's opened.
      ws.send(JSON.stringify({ type: "read", sender_id: otherUserId }));
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }

      if (data.type === "pong") return;

      if (data.type === "message") {
        setMessages((prev) => [...prev, data]);
        // Auto-acknowledge messages that arrive while the thread is open.
        if (data.sender_id === otherUserId && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "read", sender_id: otherUserId }));
        }
        return;
      }

      if (data.type === "read") {
        // The other party read what we sent them -> flip our sent messages.
        setMessages((prev) =>
          prev.map((m) => (m.sender_id === currentUserId ? { ...m, is_read: true } : m))
        );
        return;
      }

      if (data.type === "error") {
        console.error("Chat error:", data.detail);
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus("closed");
      clearInterval(pingIntervalRef.current);
      const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 15000);
      reconnectAttempts.current += 1;
      reconnectTimeoutRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus("error");
    };
  }, [token, wsUrl, currentUserId, otherUserId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearInterval(pingIntervalRef.current);
      clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (content) => {
      const ws = wsRef.current;
      const trimmed = content.trim();
      if (!ws || ws.readyState !== WebSocket.OPEN || !trimmed) return false;
      ws.send(JSON.stringify({ type: "message", receiver_id: otherUserId, content: trimmed }));
      return true;
    },
    [otherUserId]
  );

  return { messages, sendMessage, status };
}
