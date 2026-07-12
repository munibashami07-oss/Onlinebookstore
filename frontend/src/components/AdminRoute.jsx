import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';
import LoadingSpinner from './LoadingSpinner';

const AdminRoute = ({ children }) => {
  const { isAuthenticated, loading: authLoading } = useContext(AuthContext);
  const { user, loading: userLoading } = useContext(UserContext);

  if (authLoading || userLoading) {
    return <LoadingSpinner message="Checking authorization..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Allow if role is admin or is_superuser is true
  const isAdmin = user?.role === 'admin' || user?.is_superuser === true;

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default AdminRoute;
