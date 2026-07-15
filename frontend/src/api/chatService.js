import apiClient from './client';

/**
 * Service for the Chat REST endpoints (message history + inbox).
 * The live message stream itself goes over the WebSocket
 * (`wss://.../ws/chat`, handled by useChatSocket) -- these endpoints only
 * cover what needs a plain HTTP round trip: loading past messages, listing
 * conversation threads, and resolving the fixed support contact.
 */
const chatService = {
  /**
   * Resolve the fixed support admin a customer's chat widget should message.
   * GET /chat/support-contact -> { id, full_name, role }
   */
  getSupportContact: async () => {
    const response = await apiClient.get('/chat/support-contact');
    return response.data;
  },

  /**
   * Fetch past messages with a specific user, oldest-first.
   * GET /chat/conversation/{otherUserId}
   */
  getConversationHistory: async (otherUserId, skip = 0, limit = 100) => {
    const response = await apiClient.get(`/chat/conversation/${otherUserId}`, {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * List every conversation thread for the current user (inbox view),
   * newest activity first.
   * GET /chat/conversations -> [{ other_user, last_message, unread_count }]
   */
  getConversations: async () => {
    const response = await apiClient.get('/chat/conversations');
    return response.data;
  },
};

export default chatService;
