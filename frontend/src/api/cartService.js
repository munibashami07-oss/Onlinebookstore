import apiClient from './client';

/**
 * Service for Shopping Cart endpoints.
 * Backend endpoints:
 *   GET    /cart              — Retrieve cart summary
 *   POST   /cart/items        — Add item to cart { book_id, quantity }
 *   PUT    /cart/items/:id    — Update item quantity { quantity }
 *   DELETE /cart/items/:id    — Remove item from cart
 *   DELETE /cart/clear        — Clear all items from cart
 */
const cartService = {
  /**
   * Get current user's cart summary (items, subtotal, discount, tax, shipping, total).
   */
  getCart: async () => {
    const response = await apiClient.get('/cart');
    return response.data;
  },

  /**
   * Add a book to cart with stock validation.
   */
  addToCart: async (bookId, quantity = 1) => {
    const response = await apiClient.post('/cart/items', {
      book_id: bookId,
      quantity,
    });
    return response.data;
  },

  /**
   * Update item quantity in cart.
   */
  updateQuantity: async (itemId, quantity) => {
    const response = await apiClient.put(`/cart/items/${itemId}`, {
      quantity,
    });
    return response.data;
  },

  /**
   * Remove item from cart.
   */
  removeFromCart: async (itemId) => {
    const response = await apiClient.delete(`/cart/items/${itemId}`);
    return response.data;
  },

  /**
   * Clear all items from cart.
   */
  clearCart: async () => {
    const response = await apiClient.delete('/cart/clear');
    return response.data;
  },
};

export default cartService;
