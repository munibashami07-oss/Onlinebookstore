import React, { useState, useRef, useEffect } from 'react';
import { useChatSocket } from '../hooks/useChatSocket';

const STATUS_LABEL = {
  connecting: 'Connecting…',
  open: 'Live',
  closed: 'Reconnecting…',
  error: 'Connection error',
};

const STATUS_BADGE_CLASS = {
  connecting: 'bg-warning text-dark',
  open: 'bg-success',
  closed: 'bg-danger',
  error: 'bg-danger',
};

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Chat thread between the current user and one other party
 * (customer<->admin). Wire `token` to AuthContext's `token`, and
 * `currentUserId` to UserContext's `user.id`.
 *
 * Props:
 *   token          - JWT access token string
 *   currentUserId  - id of the logged-in user (for aligning bubbles)
 *   otherUserId    - id of the person on the other end of this thread
 *   otherUserName  - display name shown in the header
 *   wsUrl          - defaults to same-origin wss:// + /api/v1/ws/chat
 *   initialMessages- optional history preload from your REST endpoint
 */
export default function ChatWindow({
  token,
  currentUserId,
  otherUserId,
  otherUserName = 'Chat',
  wsUrl,
  initialMessages = [],
  maxWidth = '480px',
  height = '560px',
}) {
  const resolvedWsUrl =
    wsUrl ||
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/chat`;

  const { messages, sendMessage, status } = useChatSocket({
    token,
    wsUrl: resolvedWsUrl,
    currentUserId,
    otherUserId,
    initialMessages,
  });

  const [draft, setDraft] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  const handleSend = () => {
    if (sendMessage(draft)) setDraft('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="card border-0 shadow-lg rounded-4 overflow-hidden bg-white mx-auto"
      style={{ maxWidth, height, display: 'flex', flexDirection: 'column' }}
    >
      {/* Header */}
      <div
        className="d-flex justify-content-between align-items-center px-3 py-3 text-white flex-shrink-0"
        style={{ backgroundColor: 'var(--color-accent)' }}
      >
        <div className="d-flex align-items-center gap-2">
          <i className="bi bi-person-circle fs-4"></i>
          <div className="fw-bold" style={{ fontSize: '0.95rem' }}>
            {otherUserName}
          </div>
        </div>
        <span className={`badge ${STATUS_BADGE_CLASS[status]}`}>{STATUS_LABEL[status]}</span>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-grow-1 overflow-auto p-3"
        style={{ backgroundColor: '#f8fafc' }}
      >
        {messages.length === 0 && (
          <div className="h-100 d-flex align-items-center justify-content-center text-muted small">
            No messages yet — say hello.
          </div>
        )}
        {messages.map((m, i) => {
          const mine = m.sender_id === currentUserId;
          return (
            <div key={m.id ?? i} className={`d-flex mb-3 ${mine ? 'justify-content-end' : 'justify-content-start'}`}>
              <div
                className={`p-2 px-3 rounded-4 shadow-sm ${mine ? 'text-white' : 'bg-white text-dark border'}`}
                style={{ maxWidth: '75%', ...(mine ? { backgroundColor: 'var(--color-accent)' } : {}) }}
              >
                <div className="small" style={{ whiteSpace: 'pre-wrap' }}>
                  {m.content}
                </div>
                <div
                  className={`d-flex align-items-center gap-1 mt-1 ${mine ? 'justify-content-end text-white-50' : 'text-muted'}`}
                  style={{ fontSize: '0.7rem' }}
                >
                  {m.created_at && <span>{formatTime(m.created_at)}</span>}
                  {mine && <i className={`bi ${m.is_read ? 'bi-check2-all' : 'bi-check2'}`}></i>}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Composer */}
      <div className="p-2 border-top bg-white flex-shrink-0">
        <div className="d-flex gap-2">
          <input
            type="text"
            className="form-control form-control-sm rounded-pill px-3"
            placeholder="Type a message…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!draft.trim() || status !== 'open'}
            className="btn btn-sm rounded-circle flex-shrink-0 d-flex align-items-center justify-content-center text-white"
            style={{ width: '34px', height: '34px', backgroundColor: 'var(--color-accent)' }}
            aria-label="Send message"
          >
            <i className="bi bi-send-fill" style={{ fontSize: '0.8rem' }}></i>
          </button>
        </div>
      </div>
    </div>
  );
}