import apiClient from './client';

/**
 * Service for Stationary merchandise endpoints.
 */
const stationeryService = {
  /**
   * List all stationery products.
   */
  listStationery: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get('/stationery', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get single stationery item by ID.
   */
  getStationeryById: async (id) => {
    const response = await apiClient.get(`/stationary/${id}`);
    return response.data;
  },
};

export default stationeryService;
