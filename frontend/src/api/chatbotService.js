import apiClient from './client';

/**
 * Service for AI Chatbot and RAG Q&A endpoints.
 * Endpoints:
 *   POST   /chat          — Submit a question to AI chatbot
 *   GET    /chat/history  — Retrieve paginated user chat history
 *   DELETE /chat/history  — Clear user chat history
 */
const chatbotService = {
  /**
   * Submit a question to the AI Chatbot RAG pipeline.
   */
  askChatbot: async (question) => {
    const response = await apiClient.post('/chat', { question });
    return response.data;
  },

  /**
   * Retrieve user chat history.
   */
  getChatHistory: async (page = 1, pageSize = 50) => {
    const response = await apiClient.get('/chat/history', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Clear user chat history.
   */
  clearChatHistory: async () => {
    const response = await apiClient.delete('/chat/history');
    return response.data;
  },
};

export default chatbotService;
