import React, { createContext, useState, useEffect, useCallback } from 'react';
import authService from '../api/authService';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  /**
   * On mount: check for a stored access_token and validate it
   * against the server via GET /auth/me. If valid, mark authenticated.
   * If invalid (401), clear tokens and stay logged out.
   */
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        try {
          // Validate token server-side
          await authService.getMe();
          setToken(storedToken);
          setIsAuthenticated(true);
        } catch {
          // Token is invalid or expired (interceptor may have already cleared)
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setToken(null);
          setIsAuthenticated(false);
        }
      }
      setLoading(false);
    };

    initAuth();

    // Listen to refresh failures that trigger logout from the interceptor
    const handleForceLogout = () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setIsAuthenticated(false);
    };
    window.addEventListener('auth_logout', handleForceLogout);
    return () => {
      window.removeEventListener('auth_logout', handleForceLogout);
    };
  }, []);

  /**
   * Login via OAuth2 password form.
   * Stores both access and refresh tokens in localStorage.
   */
  const login = useCallback(async (email, password) => {
    setLoading(true);
    try {
      const data = await authService.login(email, password);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      setToken(data.access_token);
      setIsAuthenticated(true);
      return data;
    } catch (error) {
      // Don't clear state on login failure — user was never logged in
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Register a new customer account.
   * Does NOT auto-login. Caller should redirect to /login on success.
   */
  const register = useCallback(async (email, fullName, password) => {
    setLoading(true);
    try {
      const data = await authService.register({
        email,
        full_name: fullName,
        password,
      });
      return data;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Logout: notify backend (best-effort), then clear all client-side state.
   */
  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch {
      // Server-side logout is best-effort (token blocklist architecture)
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setIsAuthenticated(false);
  }, []);

  /**
   * Request a password reset email for the given address.
   * Does not touch auth state -- the user isn't logged in by this.
   */
  const forgotPassword = useCallback(async (email) => {
    return authService.forgotPassword(email);
  }, []);

  /**
   * Redeem a reset token (from the emailed link) and set a new password.
   * Does not auto-login. Caller should redirect to /login on success.
   */
  const resetPassword = useCallback(async (token, newPassword) => {
    return authService.resetPassword(token, newPassword);
  }, []);

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, token, loading, login, register, logout, forgotPassword, resetPassword }}
    >
      {children}
    </AuthContext.Provider>
  );
};