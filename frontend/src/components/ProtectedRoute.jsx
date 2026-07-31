import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

/**
 * Wrap any route that should require a signed-in user. Guests get
 * redirected to the homepage with `state.authRequired = true`, which
 * Home.jsx reads to show a "please sign in / sign up" notice.
 */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useContext(AuthContext);
  const location = useLocation();

  // Wait for AuthContext to finish validating any stored token before
  // deciding -- otherwise a logged-in user gets bounced on every refresh.
  if (loading) return null;

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/"
        replace
        state={{ authRequired: true, from: location.pathname }}
      />
    );
  }

  return children;
};

export default ProtectedRoute;