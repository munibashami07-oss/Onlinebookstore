import apiClient from './client';

/**
 * Service for Customer Order History and Management.
 */
const orderService = {
  /**
   * Fetch authenticated user's order history.
   */
  getMyOrders: async (page = 1, pageSize = 50) => {
    const response = await apiClient.get('/orders/me', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Cancel an order owned by the customer.
   */
  cancelOrder: async (orderId) => {
    const response = await apiClient.post(`/orders/${orderId}/cancel`);
    return response.data;
  },
};

export default orderService;
