import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';
import chatService from '../api/chatService';
import ChatWindow from './ChatWindow';

/**
 * Site-wide floating "Contact support" chat bubble for logged-in
 * customers. Distinct from `ChatWidget` (the AI book-recommendation
 * bot) -- this one is a real human/admin conversation over the
 * customer<->admin chat WebSocket, always aimed at the single fixed
 * support admin resolved from `GET /chat/support-contact`.
 *
 * Mounted once in Layout, next to ChatWidget. Renders nothing for
 * guests or for admin accounts (admins use the Support Inbox page
 * instead, from the Admin Panel).
 */
const ChatSupportWidget = () => {
  const { isAuthenticated, token } = useContext(AuthContext);
  const { user } = useContext(UserContext);

  const [open, setOpen] = useState(false);
  const [supportContact, setSupportContact] = useState(null);
  const [initialMessages, setInitialMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [historyLoaded, setHistoryLoaded] = useState(false);

  const isCustomer = isAuthenticated && user && user.role !== 'admin';

  // Resolve the fixed support contact once, as soon as we know this is a
  // logged-in customer -- not on every open, so re-opening is instant.
  useEffect(() => {
    if (!isCustomer || supportContact) return;
    chatService.getSupportContact().then(setSupportContact).catch(() => {});
  }, [isCustomer, supportContact]);

  const handleToggle = async () => {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (historyLoaded || !supportContact) return;
    setLoading(true);
    setError('');
    try {
      const history = await chatService.getConversationHistory(supportContact.id);
      setInitialMessages(history);
      setHistoryLoaded(true);
    } catch {
      setError('Could not load your previous messages.');
    } finally {
      setLoading(false);
    }
  };

  if (!isCustomer) return null;

  return (
    <>
      <button
        type="button"
        onClick={handleToggle}
        aria-label={open ? 'Close support chat' : 'Chat with support'}
        className="shadow-lg border-0 d-flex align-items-center justify-content-center"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '96px',
          width: '58px',
          height: '58px',
          borderRadius: '50%',
          backgroundColor: '#198754',
          color: '#fff',
          zIndex: 1050,
          fontSize: '1.5rem',
          transition: 'transform 0.15s ease',
        }}
        title={open ? 'Close support chat' : 'Chat with support'}
        onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.94)')}
        onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
      >
        <i className={`bi ${open ? 'bi-x-lg' : 'bi-headset'}`}></i>
      </button>

      {open && (
        <div
          style={{
            position: 'fixed',
            bottom: '92px',
            right: '24px',
            zIndex: 1049,
            maxWidth: 'calc(100vw - 32px)',
          }}
        >
          {loading && (
            <div className="bg-white rounded-4 shadow-lg p-4 text-center text-muted small" style={{ width: '360px' }}>
              Loading conversation…
            </div>
          )}
          {!loading && error && (
            <div className="bg-white rounded-4 shadow-lg p-4 text-center text-danger small" style={{ width: '360px' }}>
              {error}
            </div>
          )}
          {!loading && !error && !supportContact && (
            <div className="bg-white rounded-4 shadow-lg p-4 text-center text-muted small" style={{ width: '360px' }}>
              Support isn't available right now.
            </div>
          )}
          {!loading && !error && supportContact && (
            <ChatWindow
              token={token}
              currentUserId={user.id}
              otherUserId={supportContact.id}
              otherUserName={supportContact.full_name || 'Support'}
              initialMessages={initialMessages}
              maxWidth="360px"
              height="480px"
            />
          )}
        </div>
      )}
    </>
  );
};

export default ChatSupportWidget;
