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
import ForgotPassword from '../pages/ForgotPassword';
import ResetPassword from '../pages/ResetPassword';

// Protected Pages
import Profile from '../pages/Profile';
import Cart from '../pages/Cart';
import Checkout from '../pages/Checkout';
import Orders from '../pages/Orders';
import Payment from '../pages/Payment';
import MessagesPage from '../pages/MessagesPage';
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
      {/* Public: only Home, Login, and Register are reachable by guests.
          Everything else redirects to Home with a "please sign in" notice. */}
      <Route path="/" element={<Layout><Home /></Layout>} />
      <Route path="/login" element={<Layout><Login /></Layout>} />
      <Route path="/register" element={<Layout><Register /></Layout>} />
      <Route path="/forgot-password" element={<Layout><ForgotPassword /></Layout>} />
      <Route path="/reset-password" element={<Layout><ResetPassword /></Layout>} />

      {/* Now gated: browsing the catalog requires an account */}
      <Route path="/books" element={
        <ProtectedRoute>
          <Layout><Books /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/books/:id" element={
        <ProtectedRoute>
          <Layout><BookDetails /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/genres" element={
        <ProtectedRoute>
          <Layout><Genres /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/genres/:id" element={
        <ProtectedRoute>
          <Layout><Books /></Layout>
        </ProtectedRoute>
      } /> {/* Using Books page with genre filter */}
      {/* <Route path="/stationary" element={<Layout><Stationary /></Layout>} /> */}
      <Route path="/deals" element={
        <ProtectedRoute>
          <Layout><Deals /></Layout>
        </ProtectedRoute>
      } />

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
      <Route
        path="/messages"
        element={
        <ProtectedRoute>
            <Layout>
                <MessagesPage />
            </Layout>
        </ProtectedRoute>
         }/>
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