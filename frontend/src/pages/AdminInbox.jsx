import React, { useContext, useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';
import chatService from '../api/chatService';
import ChatWindow from '../components/ChatWindow';
import LoadingSpinner from '../components/LoadingSpinner';

function formatTimestamp(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  return sameDay
    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

/**
 * Admin-side support inbox: every customer conversation on the left,
 * the live thread with the selected customer on the right -- a
 * WhatsApp-style layout over the same chat WebSocket used elsewhere.
 * Reached from the Admin Panel; also linkable directly per-customer
 * via /admin/inbox/:customerId (e.g. from the Users tab chat icon).
 */
const AdminInbox = () => {
  const { customerId } = useParams();
  const navigate = useNavigate();
  const { token } = useContext(AuthContext);
  const { user } = useContext(UserContext);

  const [conversations, setConversations] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState('');

  const [initialMessages, setInitialMessages] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const activeCustomerId = customerId ? Number(customerId) : null;
  const activeConversation = conversations.find((c) => c.other_user.id === activeCustomerId);

  const fetchConversations = useCallback(async () => {
    try {
      const data = await chatService.getConversations();
      setConversations(data);
      setListError('');
    } catch {
      setListError('Failed to load conversations.');
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Load message history whenever the selected thread changes.
  useEffect(() => {
    if (!activeCustomerId) {
      setInitialMessages([]);
      return;
    }
    setHistoryLoading(true);
    chatService
      .getConversationHistory(activeCustomerId)
      .then(setInitialMessages)
      .catch(() => setInitialMessages([]))
      .finally(() => setHistoryLoading(false));
  }, [activeCustomerId]);

  // Refresh the sidebar's unread badges/last-message shortly after opening
  // a thread (the socket's "read" ack has had time to land by then).
  useEffect(() => {
    if (!activeCustomerId) return;
    const timer = setTimeout(fetchConversations, 1000);
    return () => clearTimeout(timer);
  }, [activeCustomerId, fetchConversations]);

  return (
    <div className="container-fluid py-4 px-md-5">
      <div className="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
        <div>
          <h1 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
            <i className="bi bi-chat-dots-fill text-primary me-2"></i> Support Inbox
          </h1>
          <p className="text-muted mb-0">All customer conversations, live.</p>
        </div>
        <Link to="/admin" className="btn btn-outline-secondary btn-sm">
          <i className="bi bi-arrow-left me-1"></i> Back to Admin Panel
        </Link>
      </div>

      <div className="row g-3" style={{ height: '640px' }}>
        {/* Conversation list */}
        <div className="col-12 col-md-4 h-100">
          <div className="card border-0 shadow-sm rounded-4 h-100 overflow-hidden d-flex flex-column">
            <div className="p-3 border-bottom bg-light fw-bold small text-uppercase text-muted flex-shrink-0">
              Conversations
            </div>
            <div className="flex-grow-1 overflow-auto">
              {listLoading ? (
                <LoadingSpinner message="Loading conversations..." />
              ) : listError ? (
                <div className="p-3 text-danger small">{listError}</div>
              ) : conversations.length === 0 ? (
                <div className="p-3 text-muted small text-center">
                  No conversations yet — they'll show up here as customers message support.
                </div>
              ) : (
                conversations.map((c) => (
                  <button
                    key={c.other_user.id}
                    type="button"
                    onClick={() => navigate(`/admin/inbox/${c.other_user.id}`)}
                    className={`w-100 text-start btn rounded-0 border-0 border-bottom px-3 py-2 ${
                      activeCustomerId === c.other_user.id ? 'bg-light' : 'bg-white'
                    }`}
                  >
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="fw-semibold text-dark small">{c.other_user.full_name}</div>
                      <small className="text-muted" style={{ fontSize: '0.7rem' }}>
                        {formatTimestamp(c.last_message.created_at)}
                      </small>
                    </div>
                    <div className="d-flex justify-content-between align-items-center gap-2">
                      <small className="text-muted text-truncate" style={{ maxWidth: '170px' }}>
                        {c.last_message.content}
                      </small>
                      {c.unread_count > 0 && (
                        <span className="badge rounded-pill bg-danger">{c.unread_count}</span>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Active thread */}
        <div className="col-12 col-md-8 h-100">
          {!activeCustomerId ? (
            <div className="card border-0 shadow-sm rounded-4 h-100 d-flex align-items-center justify-content-center text-muted">
              <div className="text-center">
                <i className="bi bi-chat-square-text fs-1 d-block mb-2"></i>
                Select a conversation to start replying.
              </div>
            </div>
          ) : historyLoading ? (
            <div className="card border-0 shadow-sm rounded-4 h-100 d-flex align-items-center justify-content-center">
              <LoadingSpinner message="Loading conversation..." />
            </div>
          ) : (
            <ChatWindow
              token={token}
              currentUserId={user?.id}
              otherUserId={activeCustomerId}
              otherUserName={activeConversation?.other_user.full_name || `Customer #${activeCustomerId}`}
              initialMessages={initialMessages}
              maxWidth="100%"
              height="100%"
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminInbox;
