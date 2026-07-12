import apiClient from './client';

/**
 * Service for Admin Operations, Management CRUD, Dashboard, and Analytics.
 */
const adminService = {
  // ── Image Upload ──────────────────────────────────────────────────────────
  uploadImage: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/admin/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // ── Dashboard Metrics & Analytics ──────────────────────────────────────────

getDashboardMetrics: async () => {
    const response = await apiClient.get('/admin/dashboard');
    return response.data;
},

getMonthlyRevenue: async () => {
    const response = await apiClient.get('/admin/dashboard/monthly-revenue');
    return response.data;
},

getDailySales: async (month) => {
    const response = await apiClient.get('/admin/dashboard/daily-sales', {
        params: { month },
    });
    return response.data;
},

getRevenueReport: async () => {
    const response = await apiClient.get('/admin/reports/revenue');
    return response.data;
},


  getTopSellingBooks: async (limit = 5) => {
    const response = await apiClient.get('/admin/reports/top-selling-books', { params: { limit } });
    return response.data;
  },

  getMostPurchasedGenres: async (limit = 5) => {
    const response = await apiClient.get('/admin/reports/most-purchased-genres', { params: { limit } });
    return response.data;
  },

  // ── Users Management ────────────────────────────────────────────────────────
  listUsers: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get('/admin/users', { params: { page, page_size: pageSize } });
    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await apiClient.delete(`/admin/users/${userId}`);
    return response.data;
  },

  // ── Books Admin CRUD ────────────────────────────────────────────────────────
  listBooks: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get('/admin/books', { params: { page, page_size: pageSize } });
    return response.data;
  },

  createBook: async (data) => {
    const response = await apiClient.post('/admin/books', data);
    return response.data;
  },

  updateBook: async (bookId, data) => {
    const response = await apiClient.put(`/admin/books/${bookId}`, data);
    return response.data;
  },

  deleteBook: async (bookId) => {
    const response = await apiClient.delete(`/admin/books/${bookId}`);
    return response.data;
  },

  // ── Genres Admin CRUD ───────────────────────────────────────────────────────
  listGenres: async (skip = 0, limit = 100) => {
    const response = await apiClient.get('/admin/genres', { params: { skip, limit } });
    return response.data;
  },

  createGenre: async (data) => {
    const response = await apiClient.post('/admin/genres', data);
    return response.data;
  },

  updateGenre: async (genreId, data) => {
    const response = await apiClient.put(`/admin/genres/${genreId}`, data);
    return response.data;
  },

  deleteGenre: async (genreId) => {
    const response = await apiClient.delete(`/admin/genres/${genreId}`);
    return response.data;
  },

  // ── Stationery Admin CRUD ───────────────────────────────────────────────────
  listStationery: async (skip = 0, limit = 100) => {
    const response = await apiClient.get('/admin/stationary', { params: { skip, limit } });
    return response.data;
  },

  createStationery: async (data) => {
    const response = await apiClient.post('/admin/stationery', data);
    return response.data;
  },

  updateStationery: async (stationaryId, data) => {
    const response = await apiClient.put(`/admin/stationery/${stationaryId}`, data);
    return response.data;
  },

  deleteStationery: async (stationaryId) => {
    const response = await apiClient.delete(`/admin/stationery/${stationaryId}`);
    return response.data;
  },

  // ── Deals Admin CRUD ────────────────────────────────────────────────────────
  listDeals: async (skip = 0, limit = 100) => {
    const response = await apiClient.get('/admin/deals', { params: { skip, limit } });
    return response.data;
  },

  // ── Inventory Operations ────────────────────────────────────────────────────
  getLowStockReport: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get('/admin/inventory/low-stock', { params: { page, page_size: pageSize } });
    return response.data;
  },

  increaseStock: async (bookId, quantity) => {
    const response = await apiClient.post(`/admin/inventory/${bookId}/increase`, null, { params: { quantity } });
    return response.data;
  },

  decreaseStock: async (bookId, quantity) => {
    const response = await apiClient.post(`/admin/inventory/${bookId}/decrease`, null, { params: { quantity } });
    return response.data;
  },

  // ── Orders Admin Operations ─────────────────────────────────────────────────
  listOrders: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get('/admin/orders', { params: { page, page_size: pageSize } });
    return response.data;
  },

  updateOrderStatus: async (orderId, status) => {
    const response = await apiClient.put(`/admin/orders/${orderId}/status`, null, { params: { order_status: status } });
    return response.data;
  },

  // ── Payments Admin Operations ───────────────────────────────────────────────
  listPayments: async (page = 1, pageSize = 20) => {
    const response = await apiClient.get('/admin/payments', { params: { page, page_size: pageSize } });
    return response.data;
  },
};

export default adminService;
