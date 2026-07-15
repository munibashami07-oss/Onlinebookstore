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
      <div className="row g-3" style={{ minHeight: '70vh' }}>
        {/* Conversation list / new chat search */}
        <div className="col-12 col-md-4">
          <div className="card border-0 shadow-sm rounded-4 h-100 d-flex flex-column">
            <div className="d-flex justify-content-between align-items-center p-3 border-bottom">
              <span className="fw-bold">Messages</span>
              <button
                type="button"
                className="btn btn-sm rounded-pill text-white"
                style={{ backgroundColor: 'var(--color-accent)' }}
                onClick={() => setNewChatOpen((v) => !v)}
              >
                <i className={`bi ${newChatOpen ? 'bi-x-lg' : 'bi-plus-lg'} me-1`}></i>
                {newChatOpen ? 'Cancel' : 'New chat'}
              </button>
            </div>

            {newChatOpen ? (
              <div className="p-3 flex-grow-1 overflow-auto">
                <input
                  type="text"
                  autoFocus
                  className="form-control form-control-sm rounded-pill px-3 mb-2"
                  placeholder="Search by name or email…"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                {searching && (
                  <div className="text-muted small px-2">Searching…</div>
                )}
                {!searching && searchTerm.trim() && searchResults.length === 0 && (
                  <div className="text-muted small px-2">No users found.</div>
                )}
                {!searching &&
                  searchResults
                    .filter((u) => u.id !== user?.id)
                    .map((u) => (
                      <button
                        key={u.id}
                        type="button"
                        className="btn btn-light w-100 text-start d-flex align-items-center gap-2 mb-1 rounded-3"
                        onClick={() => openThreadWith(u)}
                      >
                        <i className="bi bi-person-circle fs-5 text-secondary"></i>
                        <span className="flex-grow-1">
                          <div className="small fw-semibold">{u.full_name}</div>
                          <div className="text-muted" style={{ fontSize: '0.72rem' }}>
                            {u.role}
                          </div>
                        </span>
                      </button>
                    ))}
              </div>
            ) : (
              <div className="flex-grow-1 overflow-auto">
                {loadingConversations && (
                  <div className="text-muted small p-3">Loading…</div>
                )}
                {!loadingConversations && conversationsError && (
                  <div className="text-danger small p-3">{conversationsError}</div>
                )}
                {!loadingConversations && !conversationsError && conversations.length === 0 && (
                  <div className="text-muted small p-3">
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
                        className={`btn w-100 text-start d-flex align-items-center gap-2 px-3 py-2 border-0 border-bottom rounded-0 ${
                          active ? 'bg-light' : ''
                        }`}
                        onClick={() => openThreadWith(c.other_user)}
                      >
                        <i className="bi bi-person-circle fs-4 text-secondary"></i>
                        <span className="flex-grow-1 overflow-hidden">
                          <div className="d-flex justify-content-between">
                            <span className="small fw-semibold text-truncate">
                              {c.other_user.full_name}
                            </span>
                            {c.unread_count > 0 && (
                              <span className="badge rounded-pill bg-danger">
                                {c.unread_count}
                              </span>
                            )}
                          </div>
                          <div className="text-muted small text-truncate" style={{ maxWidth: '220px' }}>
                            {c.last_message?.content}
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
            <div className="card border-0 shadow-sm rounded-4 h-100 d-flex align-items-center justify-content-center text-muted">
              Select a conversation or start a new one.
            </div>
          )}
          {selectedUser && loadingThread && (
            <div className="card border-0 shadow-sm rounded-4 h-100 d-flex align-items-center justify-content-center text-muted">
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
              height="70vh"
            />
          )}
        </div>
      </div>
    </div>
  );
}