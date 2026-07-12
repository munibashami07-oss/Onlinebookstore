import apiClient from './client';

/**
 * Service for Book catalog endpoints.
 */
const bookService = {
  /**
   * List books with filtering, sorting, and pagination.
   * Query params: page, page_size, genre_id, min_price, max_price, in_stock, sort_by
   */
  listBooks: async (params = {}) => {
    const response = await apiClient.get('/books', { params });
    return response.data;
  },

  /**
   * Search books by title, author, or ISBN.
   * Query params: q, page, page_size
   */
  searchBooks: async (query, page = 1, pageSize = 20) => {
    const response = await apiClient.get('/books/search', {
      params: { q: query, page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get books by Genre ID.
   */
  getBooksByGenre: async (genreId, page = 1, pageSize = 20) => {
    const response = await apiClient.get(`/books/genre/${genreId}`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get single book details by ID.
   */
  getBookById: async (id) => {
    const response = await apiClient.get(`/books/${id}`);
    return response.data;
  },
};

export default bookService;
