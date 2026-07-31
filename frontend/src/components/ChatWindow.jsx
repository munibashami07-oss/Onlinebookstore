import React, { useState, useRef, useEffect } from 'react';
import { useChatSocket } from '../hooks/useChatSocket';

const STATUS_LABEL = {
  connecting: 'Connecting…',
  open: 'Live',
  closed: 'Reconnecting…',
  error: 'Connection error',
};

const STATUS_DOT_CLASS = {
  connecting: 'bg-warning',
  open: 'bg-success',
  closed: 'bg-danger',
  error: 'bg-danger',
};

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/** Custom send icon -- plain bootstrap-icon glyphs render inconsistently
 *  at 0.8rem in some environments (can look like a stray "v"). This SVG
 *  is crisp at any size and doesn't depend on an icon font being loaded. */
function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M3.4 20.4l17.45-8.32a1 1 0 000-1.8L3.4 1.96a1 1 0 00-1.41 1.17L4.6 11 2 18.87a1 1 0 001.4 1.53z"
        fill="currentColor"
      />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M6 6l12 12M18 6L6 18"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
    </svg>
  );
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
 *   onClose        - optional; if provided, a close (X) button renders
 *                     in the header, on the same line as the name/status
 */
export default function ChatWindow({
  token,
  currentUserId,
  otherUserId,
  otherUserName = 'Chat',
  wsUrl,
  initialMessages = [],
  maxWidth = '380px',
  height = '540px',
  onClose,
}) {
  const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
  const resolvedWsUrl = wsUrl || `${API_URL.replace(/^http/, 'ws')}/ws/chat`;

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
      className="d-flex flex-column bg-white mx-auto"
      style={{
        maxWidth,
        height,
        borderRadius: '18px',
        overflow: 'hidden',
        boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
        border: '1px solid rgba(0,0,0,0.06)',
      }}
    >
      {/* Header -- avatar, name, status dot+label, and close button all on one row */}
      <div
        className="d-flex align-items-center justify-content-between px-3 py-2 text-white flex-shrink-0"
        style={{ backgroundColor: 'var(--color-accent)', minHeight: '56px' }}
      >
        <div className="d-flex align-items-center gap-2" style={{ minWidth: 0 }}>
          <div
            className="d-flex align-items-center justify-content-center flex-shrink-0"
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255,255,255,0.18)',
            }}
          >
            <i className="bi bi-person-fill fs-5"></i>
          </div>
          <div className="d-flex flex-column" style={{ minWidth: 0 }}>
            <span
              className="fw-semibold text-truncate"
              style={{ fontSize: '0.92rem', lineHeight: 1.2 }}
            >
              {otherUserName}
            </span>
            <span className="d-flex align-items-center gap-1" style={{ fontSize: '0.72rem', opacity: 0.9 }}>
              <span
                className={`rounded-circle ${STATUS_DOT_CLASS[status]}`}
                style={{ width: '7px', height: '7px', display: 'inline-block' }}
              ></span>
              {STATUS_LABEL[status]}
            </span>
          </div>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close chat"
            className="d-flex align-items-center justify-content-center flex-shrink-0 border-0"
            style={{
              width: '30px',
              height: '30px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255,255,255,0.14)',
              color: '#fff',
            }}
          >
            <CloseIcon />
          </button>
        )}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-grow-1 overflow-auto px-3 py-3"
        style={{ backgroundColor: '#f4f6f9' }}
      >
        {messages.length === 0 && (
          <div className="h-100 d-flex align-items-center justify-content-center text-muted small text-center px-4">
            No messages yet — say hello.
          </div>
        )}
        {messages.map((m, i) => {
          const mine = m.sender_id === currentUserId;
          return (
            <div
              key={m.id ?? i}
              className={`d-flex mb-2 ${mine ? 'justify-content-end' : 'justify-content-start'}`}
            >
              <div
                className={mine ? 'text-white' : 'bg-white text-dark'}
                style={{
                  maxWidth: '78%',
                  padding: '8px 13px',
                  borderRadius: mine ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.08)',
                  ...(mine ? { backgroundColor: 'var(--color-accent)' } : { border: '1px solid #e9ecef' }),
                }}
              >
                <div style={{ fontSize: '0.86rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {m.content}
                </div>
                <div
                  className={`d-flex align-items-center gap-1 mt-1 ${
                    mine ? 'justify-content-end text-white-50' : 'text-muted'
                  }`}
                  style={{ fontSize: '0.65rem' }}
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
      <div className="px-2 py-2 border-top bg-white flex-shrink-0">
        <div className="d-flex align-items-center gap-2">
          <input
            type="text"
            className="form-control form-control-sm rounded-pill px-3"
            placeholder="Type a message…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{ fontSize: '0.85rem' }}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!draft.trim() || status !== 'open'}
            className="d-flex align-items-center justify-content-center flex-shrink-0 border-0 text-white"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: 'var(--color-accent)',
              opacity: !draft.trim() || status !== 'open' ? 0.5 : 1,
            }}
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}