import apiClient from './client';

/**
 * Service for Book Reviews and Ratings.
 * Endpoints:
 *   GET    /reviews/book/:book_id         — List reviews for a book
 *   GET    /reviews/book/:book_id/rating  — Get average rating & review count
 *   POST   /reviews                       — Create review { book_id, rating, review_text }
 *   PUT    /reviews/:review_id            — Update review { rating, review_text }
 *   DELETE /reviews/:review_id            — Delete review
 */
const reviewService = {
  /**
   * Get reviews for a specific book.
   */
  getBookReviews: async (bookId, page = 1, pageSize = 20) => {
    const response = await apiClient.get(`/reviews/book/${bookId}`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get average rating and count for a book.
   */
  getBookRating: async (bookId) => {
    const response = await apiClient.get(`/reviews/book/${bookId}/rating`);
    return response.data;
  },

  /**
   * Create a new review for a book.
   */
  createReview: async ({ book_id, rating, review_text }) => {
    const response = await apiClient.post('/reviews', {
      book_id,
      rating,
      review_text,
    });
    return response.data;
  },

  /**
   * Update an existing review.
   */
  updateReview: async (reviewId, { rating, review_text }) => {
    const response = await apiClient.put(`/reviews/${reviewId}`, {
      rating,
      review_text,
    });
    return response.data;
  },

  /**
   * Delete a review.
   */
  deleteReview: async (reviewId) => {
    const response = await apiClient.delete(`/reviews/${reviewId}`);
    return response.data;
  },
};

export default reviewService;
