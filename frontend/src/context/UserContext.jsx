import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import { AuthContext } from './AuthContext';
import userService from '../api/userService';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const { isAuthenticated } = useContext(AuthContext);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  /**
   * Fetch the current user's profile from GET /users/me.
   */
  const fetchProfile = useCallback(async () => {
    setLoading(true);
    try {
      const data = await userService.getProfile();
      setUser(data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * When auth state changes: fetch profile if authenticated, clear if not.
   */
  useEffect(() => {
    if (isAuthenticated) {
      fetchProfile();
    } else {
      setUser(null);
    }
  }, [isAuthenticated, fetchProfile]);

  /**
   * Update current user's profile via PUT /users/me.
   */
  const updateProfile = useCallback(async (data) => {
    setLoading(true);
    try {
      const updatedUser = await userService.updateProfile(data);
      setUser(updatedUser);
      return updatedUser;
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <UserContext.Provider value={{ user, loading, fetchProfile, updateProfile }}>
      {children}
    </UserContext.Provider>
  );
};
