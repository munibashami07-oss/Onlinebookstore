import React, { useState, useRef, useEffect } from "react";
import { Send, Check, CheckCheck, Circle } from "lucide-react";
import { useChatSocket } from "./useChatSocket";

const STATUS_LABEL = {
  connecting: "Connecting…",
  open: "Live",
  closed: "Reconnecting…",
  error: "Connection error",
};

const STATUS_COLOR = {
  connecting: "text-amber-500 fill-amber-500",
  open: "text-emerald-500 fill-emerald-500",
  closed: "text-red-400 fill-red-400",
  error: "text-red-500 fill-red-500",
};

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/**
 * Drop-in chat thread between the current user and one other party
 * (customer<->admin). Wire `token` to wherever your app currently stores
 * the JWT access token -- check whatever code already sets the
 * `Authorization: Bearer <token>` header on your REST calls; that's the
 * same token this needs.
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
  currentUserId = 1,
  otherUserId = 2,
  otherUserName = "Support",
  wsUrl,
  initialMessages = [],
}) {
  const resolvedWsUrl =
    wsUrl ||
    `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/v1/ws/chat`;

  const { messages, sendMessage, status } = useChatSocket({
    token,
    wsUrl: resolvedWsUrl,
    currentUserId,
    otherUserId,
    initialMessages,
  });

  const [draft, setDraft] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length]);

  const handleSend = () => {
    if (sendMessage(draft)) setDraft("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[560px] w-full max-w-md rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50">
        <div>
          <div className="font-medium text-slate-800 text-sm">{otherUserName}</div>
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <Circle size={8} className={STATUS_COLOR[status]} />
            {STATUS_LABEL[status]}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-4 space-y-2 bg-white">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center text-sm text-slate-400">
            No messages yet — say hello.
          </div>
        )}
        {messages.map((m, i) => {
          const mine = m.sender_id === currentUserId;
          return (
            <div key={m.id ?? i} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm leading-snug ${
                  mine
                    ? "bg-indigo-600 text-white rounded-br-sm"
                    : "bg-slate-100 text-slate-800 rounded-bl-sm"
                }`}
              >
                <div>{m.content}</div>
                <div
                  className={`mt-1 flex items-center gap-1 text-[10px] ${
                    mine ? "text-indigo-200 justify-end" : "text-slate-400"
                  }`}
                >
                  {m.created_at && <span>{formatTime(m.created_at)}</span>}
                  {mine &&
                    (m.is_read ? (
                      <CheckCheck size={12} />
                    ) : (
                      <Check size={12} />
                    ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Composer */}
      <div className="flex items-end gap-2 border-t border-slate-100 px-3 py-3 bg-white">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Type a message…"
          className="flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        <button
          onClick={handleSend}
          disabled={!draft.trim() || status !== "open"}
          className="shrink-0 rounded-lg bg-indigo-600 p-2.5 text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-indigo-700 transition-colors"
          aria-label="Send message"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
