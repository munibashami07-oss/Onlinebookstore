import apiClient from './client';

/**
 * Service for Genre catalog endpoints.
 */
const genreService = {
  /**
   * List all genres.
   */
  listGenres: async (page = 1, pageSize = 50) => {
    const response = await apiClient.get('/genres', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get single genre details by ID.
   */
  getGenreById: async (id) => {
    const response = await apiClient.get(`/genres/${id}`);
    return response.data;
  },
};

export default genreService;
