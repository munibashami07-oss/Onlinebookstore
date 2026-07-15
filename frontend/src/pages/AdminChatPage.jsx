import React, { useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';
import ChatWindow from '../components/ChatWindow';

/**
 * Admin-side chat thread with a single customer, reached via the chat
 * icon on the Users tab of AdminDashboard (/admin/chat/:customerId).
 */
const AdminChatPage = () => {
  const { customerId } = useParams();
  const { token } = useContext(AuthContext);
  const { user } = useContext(UserContext);

  return (
    <div className="container py-4">
      <Link to="/admin" className="btn btn-sm btn-outline-secondary mb-3">
        <i className="bi bi-arrow-left me-1"></i> Back to Admin Panel
      </Link>
      <ChatWindow
        token={token}
        currentUserId={user?.id}
        otherUserId={Number(customerId)}
        otherUserName={`Customer #${customerId}`}
      />
    </div>
  );
};

export default AdminChatPage;
