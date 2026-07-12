/**
 * Authentication API Service
 *
 * Wraps all backend /auth/* endpoints. Used by AuthContext.
 * Backend endpoints consumed:
 *   POST /auth/register   — RegisterRequest → UserResponse
 *   POST /auth/login      — OAuth2PasswordRequestForm → TokenResponse
 *   POST /auth/refresh    — RefreshTokenRequest → RefreshTokenResponse
 *   POST /auth/logout     — (authenticated) → { status, message }
 *   GET  /auth/me         — (authenticated) → UserResponse
 */

import apiClient from './client';

const authService = {
  /**
   * Register a new customer account.
   * @param {{ email: string, full_name: string, password: string }} data
   * @returns {Promise<object>} UserResponse from backend
   */
  register: async (data) => {
    const response = await apiClient.post('/auth/register', {
      email: data.email,
      full_name: data.full_name,
      password: data.password,
    });
    return response.data;
  },

  /**
   * Login with email and password via OAuth2 form-data flow.
   * Backend expects `application/x-www-form-urlencoded` with fields `username` and `password`.
   * @param {string} email
   * @param {string} password
   * @returns {Promise<{ access_token: string, refresh_token: string, token_type: string }>}
   */
  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  /**
   * Refresh access token using a valid refresh token.
   * @param {string} refreshToken
   * @returns {Promise<{ access_token: string, token_type: string }>}
   */
  refreshToken: async (refreshToken) => {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Logout the currently authenticated user.
   * Server-side: prepared for token blocklist architecture.
   * Client-side: caller must clear localStorage tokens.
   * @returns {Promise<{ status: string, message: string }>}
   */
  logout: async () => {
    const response = await apiClient.post('/auth/logout');
    return response.data;
  },

  /**
   * Get the currently authenticated user's profile from /auth/me.
   * @returns {Promise<object>} UserResponse
   */
  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

export default authService;
