import apiClient from './client';

/**
 * Service for Payment Gateway operations and transactions.
 * Endpoints:
 *   POST /payments/create        — Create pending payment transaction
 *   POST /payments/confirm       — Confirm pending payment transaction
 *   POST /payments/cancel        — Cancel pending payment transaction
 *   GET  /payments/:transaction  — Get payment details by transaction ID
 */
const paymentService = {
  /**
   * Create pending payment transaction for an order.
   */
  createPayment: async (orderId, paymentMethod = 'stripe', cardNumber = null) => {
    const response = await apiClient.post('/payments/create', {
      order_id: orderId,
      payment_method: paymentMethod,
      card_number: cardNumber,
    });
    return response.data;
  },

  /**
   * Confirm pending payment transaction.
   */
  confirmPayment: async (transactionId) => {
    const response = await apiClient.post('/payments/confirm', {
      transaction_id: transactionId,
    });
    return response.data;
  },

  /**
   * Cancel pending payment transaction.
   */
  cancelPayment: async (transactionId) => {
    const response = await apiClient.post('/payments/cancel', {
      transaction_id: transactionId,
    });
    return response.data;
  },

  /**
   * Get payment details by transaction ID.
   */
  getPaymentDetails: async (transactionId) => {
    const response = await apiClient.get(`/payments/${transactionId}`);
    return response.data;
  },
};

export default paymentService;
