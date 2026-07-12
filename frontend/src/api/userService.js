/**
 * User API Service
 *
 * Wraps backend /users/* endpoints.
 * Backend endpoints consumed:
 *   GET  /users/me  — (authenticated) → UserResponse
 *   PUT  /users/me  — UserUpdate → UserResponse
 */

import apiClient from './client';

const userService = {
  /**
   * Fetch the current user's profile.
   * @returns {Promise<object>} UserResponse
   */
  getProfile: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },

  /**
   * Update the current user's profile.
   * @param {{ email?: string, full_name?: string, password?: string, phone_number?: string }} data
   * @returns {Promise<object>} Updated UserResponse
   */
  updateProfile: async (data) => {
    const response = await apiClient.put('/users/me', data);
    return response.data;
  },
};

export default userService;
