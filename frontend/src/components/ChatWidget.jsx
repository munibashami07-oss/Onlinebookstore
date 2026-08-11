import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';
import chatService from '../api/chatService';
import ChatWindow from './ChatWindow';

/**
 * MessagesPage
 * -----------------------------------------------------------------------
 * The general-purpose messaging hub. Unlike `ChatSupportWidget` (which is
 * hard-wired to the single fixed support admin), this page lets any
 * logged-in user message *any other registered, active user* -- customer
 * to admin, admin to customer, or customer to customer.
 *
 * Left column: existing conversation threads (GET /chat/conversations),
 * plus a "New chat" search box that queries GET /chat/users to find
 * anyone to start a thread with. Right column: the active thread,
 * rendered with the existing `ChatWindow` (unchanged -- it already
 * supports messaging an arbitrary `otherUserId` over the chat WebSocket).
 *
 * Route this at e.g. `/messages` for any authenticated user (customer or
 * admin) -- it deliberately doesn't gate on role.
 */

const AVATAR_COLORS = [
  '#6366f1', '#0ea5e9', '#10b981', '#f59e0b',
  '#ef4444', '#8b5cf6', '#14b8a6', '#ec4899',
];

function avatarColorFor(name = '') {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function initialsFor(name = '') {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0 || !parts[0]) return '?';
  return parts.length === 1 ? parts[0][0].toUpperCase() : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function Avatar({ name, size = 42 }) {
  return (
    <div
      className="d-flex align-items-center justify-content-center flex-shrink-0 text-white fw-semibold"
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: avatarColorFor(name),
        fontSize: size * 0.36,
      }}
    >
      {initialsFor(name)}
    </div>
  );
}

export default function MessagesPage() {
  const { isAuthenticated, token } = useContext(AuthContext);
  const { user } = useContext(UserContext);

  const [conversations, setConversations] = useState([]);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [conversationsError, setConversationsError] = useState('');

  const [selectedUser, setSelectedUser] = useState(null); // { id, full_name, role }
  const [initialMessages, setInitialMessages] = useState([]);
  const [loadingThread, setLoadingThread] = useState(false);

  const [newChatOpen, setNewChatOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const searchDebounceRef = useRef(null);

  const loadConversations = useCallback(async () => {
    setLoadingConversations(true);
    setConversationsError('');
    try {
      const data = await chatService.getConversations();
      setConversations(data);
    } catch {
      setConversationsError('Could not load your conversations.');
    } finally {
      setLoadingConversations(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) loadConversations();
  }, [isAuthenticated, loadConversations]);

  // Debounced "new chat" user search -- fires 300ms after typing stops.
  useEffect(() => {
    if (!newChatOpen) return;
    clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const results = await chatService.searchUsers(searchTerm.trim());
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => clearTimeout(searchDebounceRef.current);
  }, [searchTerm, newChatOpen]);

  const openThreadWith = async (otherUser) => {
    setSelectedUser(otherUser);
    setNewChatOpen(false);
    setSearchTerm('');
    setLoadingThread(true);
    try {
      const history = await chatService.getConversationHistory(otherUser.id);
      setInitialMessages(history);
    } catch {
      setInitialMessages([]);
    } finally {
      setLoadingThread(false);
    }
    // Refresh the inbox in the background so unread counts / ordering stay
    // current once the user goes back to the list.
    loadConversations();
  };

  if (!isAuthenticated) return null;

  return (
    <div className="container-fluid py-4" style={{ maxWidth: '1100px' }}>
      <div className="row g-3" style={{ minHeight: '75vh' }}>
        {/* Conversation list / new chat search */}
        <div className="col-12 col-md-4">
          <div
            className="bg-white h-100 d-flex flex-column"
            style={{
              borderRadius: '18px',
              overflow: 'hidden',
              boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
              border: '1px solid rgba(0,0,0,0.06)',
            }}
          >
            <div className="d-flex justify-content-between align-items-center px-3 py-3 border-bottom flex-shrink-0">
              <span className="fw-bold fs-6">Messages</span>
              <button
                type="button"
                className="btn btn-sm rounded-pill text-white d-flex align-items-center gap-1 px-3"
                style={{ backgroundColor: 'var(--color-accent)' }}
                onClick={() => setNewChatOpen((v) => !v)}
              >
                <i className={`bi ${newChatOpen ? 'bi-x-lg' : 'bi-plus-lg'}`}></i>
                {newChatOpen ? 'Cancel' : 'New chat'}
              </button>
            </div>

            {newChatOpen ? (
              <div className="p-3 flex-grow-1 overflow-auto">
                <div className="position-relative mb-2">
                  <i
                    className="bi bi-search position-absolute text-muted"
                    style={{ left: '14px', top: '50%', transform: 'translateY(-50%)', fontSize: '0.8rem' }}
                  ></i>
                  <input
                    type="text"
                    autoFocus
                    className="form-control form-control-sm rounded-pill ps-4 pe-3"
                    placeholder="Search by name or email…"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{ paddingLeft: '30px' }}
                  />
                </div>
                {searching && <div className="text-muted small px-2 py-2">Searching…</div>}
                {!searching && searchTerm.trim() && searchResults.length === 0 && (
                  <div className="text-muted small px-2 py-2">No users found.</div>
                )}
                {!searching &&
                  searchResults
                    .filter((u) => u.id !== user?.id)
                    .map((u) => (
                      <button
                        key={u.id}
                        type="button"
                        className="btn w-100 text-start d-flex align-items-center gap-2 mb-1 px-2 py-2 border-0 rounded-3"
                        onClick={() => openThreadWith(u)}
                        style={{ transition: 'background-color 0.12s ease' }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f4f6f9')}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                      >
                        <Avatar name={u.full_name} size={38} />
                        <span className="flex-grow-1 overflow-hidden">
                          <div className="small fw-semibold text-truncate">{u.full_name}</div>
                          <div className="text-muted text-truncate" style={{ fontSize: '0.72rem' }}>
                            {u.role}
                          </div>
                        </span>
                      </button>
                    ))}
              </div>
            ) : (
              <div className="flex-grow-1 overflow-auto">
                {loadingConversations && (
                  <div className="text-muted small p-3 text-center">Loading…</div>
                )}
                {!loadingConversations && conversationsError && (
                  <div className="text-danger small p-3 text-center">{conversationsError}</div>
                )}
                {!loadingConversations && !conversationsError && conversations.length === 0 && (
                  <div className="text-muted small p-4 text-center">
                    <i className="bi bi-chat-square-text fs-2 d-block mb-2 opacity-50"></i>
                    No conversations yet — start a new chat.
                  </div>
                )}
                {!loadingConversations &&
                  conversations.map((c) => {
                    const active = selectedUser && selectedUser.id === c.other_user.id;
                    return (
                      <button
                        key={c.other_user.id}
                        type="button"
                        className="btn w-100 text-start d-flex align-items-center gap-2 px-3 py-2 border-0 border-bottom rounded-0"
                        onClick={() => openThreadWith(c.other_user)}
                        style={{
                          backgroundColor: active ? '#eef2ff' : 'transparent',
                          borderLeft: active ? '3px solid var(--color-accent)' : '3px solid transparent',
                        }}
                      >
                        <Avatar name={c.other_user.full_name} />
                        <span className="flex-grow-1 overflow-hidden">
                          <div className="d-flex justify-content-between align-items-center">
                            <span className="small fw-semibold text-truncate">
                              {c.other_user.full_name}
                            </span>
                            {c.unread_count > 0 && (
                              <span
                                className="badge rounded-pill text-white flex-shrink-0 ms-2"
                                style={{ backgroundColor: 'var(--color-accent)', fontSize: '0.68rem' }}
                              >
                                {c.unread_count}
                              </span>
                            )}
                          </div>
                          <div className="text-muted text-truncate" style={{ fontSize: '0.76rem', maxWidth: '220px' }}>
                            {c.last_message?.content || 'No messages yet'}
                          </div>
                        </span>
                      </button>
                    );
                  })}
              </div>
            )}
          </div>
        </div>

        {/* Active thread */}
        <div className="col-12 col-md-8">
          {!selectedUser && (
            <div
              className="bg-white h-100 d-flex flex-column align-items-center justify-content-center text-muted"
              style={{
                borderRadius: '18px',
                boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
                border: '1px solid rgba(0,0,0,0.06)',
              }}
            >
              <i className="bi bi-chat-dots fs-1 mb-2 opacity-50"></i>
              <span className="small">Select a conversation or start a new one.</span>
            </div>
          )}
          {selectedUser && loadingThread && (
            <div
              className="bg-white h-100 d-flex align-items-center justify-content-center text-muted"
              style={{
                borderRadius: '18px',
                boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
                border: '1px solid rgba(0,0,0,0.06)',
              }}
            >
              Loading conversation…
            </div>
          )}
          {selectedUser && !loadingThread && (
            <ChatWindow
              token={token}
              currentUserId={user.id}
              otherUserId={selectedUser.id}
              otherUserName={selectedUser.full_name}
              initialMessages={initialMessages}
              maxWidth="100%"
              height="75vh"
            />
          )}
        </div>
      </div>
    </div>
  );
}