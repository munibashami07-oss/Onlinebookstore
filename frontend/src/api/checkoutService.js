import apiClient from './client';

/**
 * Service for Checkout operations.
 * Backend endpoint:
 *   POST /checkout — Process checkout with { shipping_address, payment_method }
 */
const checkoutService = {
  /**
   * Execute atomic checkout.
   */
  processCheckout: async (shippingAddress, paymentMethod = 'stripe') => {
    const response = await apiClient.post('/checkout', {
      shipping_address: shippingAddress,
      payment_method: paymentMethod,
    });
    return response.data;
  },
};

export default checkoutService;
