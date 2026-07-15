import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from '../layouts/Layout';

// Public Pages
import Home from '../pages/Home';
import Books from '../pages/Books';
import BookDetails from '../pages/BookDetails';
import Genres from '../pages/Genres';
import Deals from '../pages/Deals';
import Stationery from '../pages/Stationery';
import Login from '../pages/Login';
import Register from '../pages/Register';

// Protected Pages
import Profile from '../pages/Profile';
import Cart from '../pages/Cart';
import Checkout from '../pages/Checkout';
import Orders from '../pages/Orders';
import Payment from '../pages/Payment';

// Admin Page
import AdminDashboard from '../pages/AdminDashboard';
import AdminInbox from '../pages/AdminInbox';

// Reusable / Fallback Components
import ProtectedRoute from '../components/ProtectedRoute';
import AdminRoute from '../components/AdminRoute';
import NotFound from '../components/NotFound';

const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Routes with standard Layout wrapper */}
      <Route path="/" element={<Layout><Home /></Layout>} />
      <Route path="/books" element={<Layout><Books /></Layout>} />
      <Route path="/books/:id" element={<Layout><BookDetails /></Layout>} />
      <Route path="/genres" element={<Layout><Genres /></Layout>} />
      <Route path="/genres/:id" element={<Layout><Books /></Layout>} /> {/* Using Books page with genre filter */}
      {/* <Route path="/stationary" element={<Layout><Stationary /></Layout>} /> */}
      <Route path="/deals" element={<Layout><Deals /></Layout>} />
      <Route path="/login" element={<Layout><Login /></Layout>} />
      <Route path="/register" element={<Layout><Register /></Layout>} />

      {/* Protected Customer Routes */}
      <Route path="/profile" element={
        <ProtectedRoute>
          <Layout><Profile /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/cart" element={
        <ProtectedRoute>
          <Layout><Cart /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/checkout" element={
        <ProtectedRoute>
          <Layout><Checkout /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/payment" element={
        <ProtectedRoute>
          <Layout><Payment /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/payment/:orderId" element={
        <ProtectedRoute>
          <Layout><Payment /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/orders" element={
        <ProtectedRoute>
          <Layout><Orders /></Layout>
        </ProtectedRoute>
      } />
      {/* Protected Admin Routes */}
      <Route path="/admin" element={
        <AdminRoute>
          <Layout><AdminDashboard /></Layout>
        </AdminRoute>
      } />
      <Route path="/admin/inbox" element={
        <AdminRoute>
          <Layout><AdminInbox /></Layout>
        </AdminRoute>
      } />
      <Route path="/admin/inbox/:customerId" element={
        <AdminRoute>
          <Layout><AdminInbox /></Layout>
        </AdminRoute>
      } />

      {/* Fallback 404 Route */}
      <Route path="*" element={<Layout><NotFound /></Layout>} />
    </Routes>
  );
};

export default AppRoutes;