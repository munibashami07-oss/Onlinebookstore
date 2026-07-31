import React, { useContext, useEffect, useRef, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';
import chatService from '../api/chatService';
import ChatWindow from './ChatWindow';

/**
 * Site-wide floating chat widget for logged-in customers.
 *
 * - Main bubble (headset icon): opens/closes the widget. Defaults to the
 *   fixed support admin (GET /chat/support-contact) the first time it's
 *   opened, same as before.
 * - Arrow button: toggles a contact list (every active registered user,
 *   merged with existing conversation threads so unread counts and last
 *   activity show up) so the customer can message anyone, not just
 *   support -- reuses the same endpoints as the Messages inbox page.
 * - Unread red dot: a lightweight poll of GET /chat/conversations every
 *   15s keeps per-contact unread badges (and a combined dot on the main
 *   bubble) current even while the widget is closed.
 * - Message history always comes from GET /chat/conversation/{id}, so
 *   switching contacts and coming back preserves the full old thread --
 *   nothing is ever cleared client-side.
 *
 * Renders nothing for guests or for admin accounts (admins use the
 * Support Inbox page instead, from the Admin Panel).
 */
const ChatSupportWidget = () => {
  const { isAuthenticated, token } = useContext(AuthContext);
  const { user } = useContext(UserContext);

  const [open, setOpen] = useState(false);
  const [contactListOpen, setContactListOpen] = useState(false);

  const [supportContact, setSupportContact] = useState(null);
  const [activeContact, setActiveContact] = useState(null);

  const [contacts, setContacts] = useState([]); // merged directory + conversations
  const [contactsLoading, setContactsLoading] = useState(false);
  const [totalUnread, setTotalUnread] = useState(0);

  const [initialMessages, setInitialMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const pollRef = useRef(null);

  const isCustomer = isAuthenticated && user && user.role !== 'admin';

  // Resolve the fixed support contact once, as soon as we know this is a
  // logged-in customer -- used as the default thread on first open.
  useEffect(() => {
    if (!isCustomer || supportContact) return;
    chatService.getSupportContact().then(setSupportContact).catch(() => {});
  }, [isCustomer, supportContact]);

  // Merge the full user directory with existing conversation threads so
  // the contact list shows unread counts / recency, but still includes
  // people the customer has never messaged yet.
  const refreshContacts = async () => {
    try {
      const [conversations, allUsers] = await Promise.all([
        chatService.getConversations(),
        chatService.searchUsers('', 0, 100),
      ]);
      const convByUserId = new Map(conversations.map((c) => [c.other_user.id, c]));
      const merged = allUsers.map((u) => {
        const conv = convByUserId.get(u.id);
        return {
          id: u.id,
          full_name: u.full_name,
          role: u.role,
          unread_count: conv?.unread_count || 0,
          last_message: conv?.last_message || null,
        };
      });
      merged.sort((a, b) => {
        if (a.unread_count !== b.unread_count) return b.unread_count - a.unread_count;
        if (a.last_message && !b.last_message) return -1;
        if (!a.last_message && b.last_message) return 1;
        return a.full_name.localeCompare(b.full_name);
      });
      setContacts(merged);
      setTotalUnread(merged.reduce((sum, c) => sum + c.unread_count, 0));
    } catch {
      // Silent fail -- keep whatever we last had rather than flashing an error.
    }
  };

  // Poll unread state periodically for the whole time the customer is
  // logged in, so the bubble's red dot stays current even if the widget
  // (and the contact list) are both closed.
  useEffect(() => {
    if (!isCustomer) return;
    refreshContacts();
    pollRef.current = setInterval(refreshContacts, 15000);
    return () => clearInterval(pollRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCustomer]);

  const loadHistoryFor = async (contactId) => {
    setLoading(true);
    setError('');
    try {
      const history = await chatService.getConversationHistory(contactId);
      setInitialMessages(history);
    } catch {
      setError('Could not load your previous messages.');
    } finally {
      setLoading(false);
    }
  };

  const handleBubbleToggle = async () => {
    if (open) {
      setOpen(false);
      setContactListOpen(false);
      return;
    }
    setOpen(true);
    setContactListOpen(false);
    const contact = activeContact || supportContact;
    if (!contact) return;
    setActiveContact(contact);
    await loadHistoryFor(contact.id);
  };

  const handleArrowToggle = async () => {
    setOpen(true);
    const willOpen = !contactListOpen;
    setContactListOpen(willOpen);
    if (willOpen) {
      setContactsLoading(true);
      await refreshContacts();
      setContactsLoading(false);
    }
  };

  const selectContact = async (contact) => {
    setActiveContact(contact);
    setContactListOpen(false);
    // Optimistically clear this contact's unread badge locally -- the
    // WebSocket's "read" ack (sent when ChatWindow mounts) confirms it
    // server-side a moment later.
    setContacts((prev) =>
      prev.map((c) => (c.id === contact.id ? { ...c, unread_count: 0 } : c))
    );
    setTotalUnread((prev) => Math.max(0, prev - (contact.unread_count || 0)));
    await loadHistoryFor(contact.id);
  };

  if (!isCustomer) return null;

  const displayContact = activeContact || supportContact;

  return (
    <>
      {/* Arrow button: opens the "message anyone" contact list */}
      <button
        type="button"
        onClick={handleArrowToggle}
        aria-label={contactListOpen ? 'Hide contacts' : 'Show all contacts'}
        className="shadow-lg border-0 d-flex align-items-center justify-content-center"
        style={{
          position: 'fixed',
          bottom: '88px',
          right: '100px',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: '#198754',
          color: '#fff',
          border: '0',
          zIndex: 1051,
          fontSize: '1rem',
        }}
        title={contactListOpen ? 'Hide contacts' : 'Message someone else'}
      >
        <i className={`bi ${contactListOpen ? 'bi-chevron-down' : 'bi-chevron-up'}`}></i>
      </button>

      {/* Main bubble */}
      <button
        type="button"
        onClick={handleBubbleToggle}
        aria-label={open ? 'Close support chat' : 'Chat with support'}
        className="shadow-lg border-0 d-flex align-items-center justify-content-center position-relative"
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
        {!open && totalUnread > 0 && (
          <span
            className="position-absolute translate-middle badge rounded-pill bg-danger"
            style={{ top: '8px', right: '4px', fontSize: '0.65rem' }}
          >
            {totalUnread > 9 ? '9+' : totalUnread}
          </span>
        )}
      </button>

      {/* Contact list panel */}
      {contactListOpen && (
        <div
          className="bg-white rounded-4 shadow-lg overflow-hidden"
          style={{
            position: 'fixed',
            bottom: '134px',
            right: '24px',
            zIndex: 1049,
            width: '320px',
            maxHeight: '360px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div className="p-3 border-bottom fw-bold small text-uppercase text-muted flex-shrink-0">
            Message someone
          </div>
          <div className="flex-grow-1 overflow-auto">
            {contactsLoading && (
              <div className="text-muted small p-3 text-center">Loading contacts…</div>
            )}
            {!contactsLoading && contacts.length === 0 && (
              <div className="text-muted small p-3 text-center">No other users found.</div>
            )}
            {!contactsLoading &&
              contacts.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className="btn w-100 text-start d-flex align-items-center gap-2 px-3 py-2 border-0 border-bottom rounded-0"
                  onClick={() => selectContact(c)}
                >
                  <span className="position-relative">
                    <i className="bi bi-person-circle fs-4 text-secondary"></i>
                    {c.unread_count > 0 && (
                      <span
                        className="position-absolute bg-danger rounded-circle"
                        style={{ width: '10px', height: '10px', top: '0', right: '0' }}
                      ></span>
                    )}
                  </span>
                  <span className="flex-grow-1 overflow-hidden">
                    <div className="d-flex justify-content-between">
                      <span className="small fw-semibold text-truncate">{c.full_name}</span>
                      {c.unread_count > 0 && (
                        <span className="badge rounded-pill bg-danger">{c.unread_count}</span>
                      )}
                    </div>
                    <div className="text-muted text-truncate" style={{ fontSize: '0.72rem' }}>
                      {c.last_message?.content || c.role}
                    </div>
                  </span>
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Active chat window */}
      {open && !contactListOpen && (
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
          {!loading && !error && !displayContact && (
            <div className="bg-white rounded-4 shadow-lg p-4 text-center text-muted small" style={{ width: '360px' }}>
              Support isn't available right now.
            </div>
          )}
          {!loading && !error && displayContact && (
            <div className="bg-white rounded-4 shadow-lg overflow-hidden" style={{ width: '360px' }}>
              <div className="d-flex justify-content-between align-items-center px-3 py-2 border-bottom bg-light">
                <span className="fw-semibold small">{displayContact.full_name || 'Support'}</span>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  aria-label={`Close chat with ${displayContact.full_name || 'Support'}`}
                  className="btn btn-sm btn-light border-0 d-flex align-items-center justify-content-center p-0"
                  style={{ width: '26px', height: '26px', borderRadius: '50%' }}
                  title="Close chat"
                >
                  <i className="bi bi-x-lg" style={{ fontSize: '0.85rem' }}></i>
                </button>
              </div>
              <ChatWindow
                token={token}
                currentUserId={user.id}
                otherUserId={displayContact.id}
                otherUserName={displayContact.full_name || 'Support'}
                initialMessages={initialMessages}
                maxWidth="360px"
                height="440px"
              />
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default ChatSupportWidget;