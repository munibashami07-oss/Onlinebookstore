import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import adminService from '../api/adminService';
import LoadingSpinner from '../components/LoadingSpinner';
import { extractErrorMessage } from '../utils/errorUtils';

// Chart.js & React-Chartjs-2
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Metrics & Reports State
  const [metrics, setMetrics] = useState(null);
  const [topBooks, setTopBooks] = useState([]);
  const [topGenres, setTopGenres] = useState([]);
  const [monthlyRevenue, setMonthlyRevenue] = useState([]);
  const [dailySales, setDailySales] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(null);

  // Managed Data States
  const [books, setBooks] = useState([]);
  const [genres, setGenres] = useState([]);
  const [stationery, setStationery] = useState([]);
  const [deals, setDeals] = useState([]);
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [lowStock, setLowStock] = useState([]);

  // Modals & Forms State
  const [showBookModal, setShowBookModal] = useState(false);
  const [bookFormData, setBookFormData] = useState({ title: '', author: '', isbn: '', price: '', genre_id: 1, description: '', cover_image_url: '' });
  const [editingBookId, setEditingBookId] = useState(null);
  const [uploadingBookImg, setUploadingBookImg] = useState(false);

  const [showStatModal, setShowStatModal] = useState(false);
  const [statForm, setStatForm] = useState({ name: '', price: '', stock: 10, description: '', cover_image_url: '' });
  const [editingStatId, setEditingStatId] = useState(null);
  const [uploadingStatImg, setUploadingStatImg] = useState(false);
  const [genreForm, setGenreForm] = useState({ name: '', description: '' });


  // Fetch Dashboard Overview
  const fetchOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, b, g, revenue] = await Promise.all([
    adminService.getDashboardMetrics().catch(() => ({
        total_users: 12,
        total_books: 45,
        total_orders: 28,
        total_revenue: 1450.50,
    })),
    adminService.getTopSellingBooks(5).catch(() => []),
    adminService.getMostPurchasedGenres(5).catch(() => []),
    adminService.getMonthlyRevenue().catch(() => []),
]);
      setMetrics(m);
      setTopBooks(b);
      setTopGenres(g);
      setMonthlyRevenue(revenue);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to fetch dashboard overview metrics.'));
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch Tab Specific Data
  const fetchTabData = useCallback(async (tab) => {
    setError(null);
    try {
      if (tab === 'books') {
        const data = await adminService.listBooks(1, 50);
        setBooks(data);
      } else if (tab === 'genres') {
        const data = await adminService.listGenres(0, 100);
        setGenres(data);
      } else if (tab === 'stationery') {
        const data = await adminService.listStationery(0, 100);
        setStationery(data);
      } else if (tab === 'deals') {
        const data = await adminService.listDeals(0, 100);
        setDeals(data);
      } else if (tab === 'inventory') {
        const data = await adminService.getLowStockReport(1, 50);
        setLowStock(data);
      } else if (tab === 'users') {
        const data = await adminService.listUsers(1, 50);
        setUsers(data);
      } else if (tab === 'orders') {
        const data = await adminService.listOrders(1, 50);
        setOrders(data);
      }
    } catch (err) {
      setError(extractErrorMessage(err, `Failed to load ${tab} data.`));
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchOverview();
    } else {
      fetchTabData(activeTab);
    }
  }, [activeTab, fetchOverview, fetchTabData]);
  const handleMonthClick = async (month) => {
    try {
        setSelectedMonth(month);

        const data = await adminService.getDailySales(month);

        setDailySales(data);
    } catch (err) {
        setError(
            extractErrorMessage(err, "Failed to load daily sales.")
        );
    }
};

  // ── File Upload Handlers ──────────────────────────────────────────────────
  const handleBookFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingBookImg(true);
    try {
      const res = await adminService.uploadImage(file);
      setBookFormData((prev) => ({ ...prev, cover_image_url: res.url }));
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to upload book cover image.'));
    } finally {
      setUploadingBookImg(false);
    }
  };

  const handleStatFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingStatImg(true);
    try {
      const res = await adminService.uploadImage(file);
      setStatForm((prev) => ({ ...prev, cover_image_url: res.url }));
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to upload stationery image.'));
    } finally {
      setUploadingStatImg(false);
    }
  };

  // ── Book Actions ─────────────────────────────────────────────────────────────
  const handleSaveBook = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...bookFormData,
        price: parseFloat(bookFormData.price),
        genre_id: parseInt(bookFormData.genre_id, 10),
      };
      if (editingBookId) {
        await adminService.updateBook(editingBookId, payload);
      } else {
        await adminService.createBook(payload);
      }
      setShowBookModal(false);
      setEditingBookId(null);
      setBookFormData({ title: '', author: '', isbn: '', price: '', genre_id: 1, description: '', cover_image_url: '' });
      fetchTabData('books');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to save book.'));
    }
  };

  const handleDeleteBook = async (id) => {
    if (!window.confirm('Delete this book record?')) return;
    try {
      await adminService.deleteBook(id);
      fetchTabData('books');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to delete book.'));
    }
  };

  // ── Stationery Actions ───────────────────────────────────────────────────────
  const handleSaveStationery = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...statForm,
        price: parseFloat(statForm.price),
        stock: parseInt(statForm.stock, 10),
      };
      if (editingStatId) {
        await adminService.updateStationery(editingStatId, payload);
      } else {
        await adminService.createStationery(payload);
      }
      setShowStatModal(false);
      setEditingStatId(null);
      setStatForm({ name: '', price: '', stock: 10, description: '', image_url: '' });
      fetchTabData('stationery');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to save stationery item.'));
    }
  };


  // ── Genre Actions ────────────────────────────────────────────────────────────
  const handleSaveGenre = async (e) => {
    e.preventDefault();
    try {
      await adminService.createGenre(genreForm);
      setGenreForm({ name: '', description: '' });
      fetchTabData('genres');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to create genre.'));
    }
  };

  const handleDeleteGenre = async (id) => {
    if (!window.confirm('Delete this genre?')) return;
    try {
      await adminService.deleteGenre(id);
      fetchTabData('genres');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to delete genre.'));
    }
  };

  // ── Inventory Actions ────────────────────────────────────────────────────────
  const handleAdjustStock = async (bookId, delta) => {
    try {
      if (delta > 0) {
        await adminService.increaseStock(bookId, delta);
      } else {
        await adminService.decreaseStock(bookId, Math.abs(delta));
      }
      fetchTabData('inventory');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to adjust stock quantity.'));
    }
  };

  // ── Order Status Update ──────────────────────────────────────────────────────
  const handleOrderStatus = async (orderId, newStatus) => {
    try {
      await adminService.updateOrderStatus(orderId, newStatus);
      fetchTabData('orders');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to update order status.'));
    }
  };

  // ── Charts Data Config ───────────────────────────────────────────────────────
const revenueChartData = {
  labels:
    monthlyRevenue.length > 0
      ? monthlyRevenue.map((item) => item.month)
      : ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],

  datasets: [
    {
      label: 'Monthly Revenue ($)',
      data:
        monthlyRevenue.length > 0
          ? monthlyRevenue.map((item) => item.revenue)
          : [0, 0, 0, 0, 0, 0],

      borderColor: '#4f46e5',
      backgroundColor: 'rgba(79,70,229,0.15)',
      fill: true,
      tension: 0.3,
    },
  ],
};

  // const topBooksChartData = {
  //   labels: topBooks.length > 0 ? topBooks.map((b) => b.title || `Book #${b.book_id}`) : ['Classic Literature', 'Sci-Fi Epic', 'Modern Fiction', 'Poetry', 'History'],
  //   datasets: [
  //     {
  //       label: 'Units Sold',
  //       data:
  //   topBooks.length > 0
  //       ? topBooks.map((b) => b.units_sold)
  //       : [0, 0, 0, 0, 0],
  //       backgroundColor: ['#d97706', '#4f46e5', '#22c55e', '#ec4899', '#3b82f6'],
  //     },
  //   ],
  // };
 const daysInMonth = 31;

const labels = Array.from(
  { length: daysInMonth },
  (_, i) => i + 1
);

const salesMap = {};

dailySales.forEach(item => {
  salesMap[item.day] = item.sales;
});

const salesData = labels.map(day => salesMap[day] || 0);

const dailySalesChartData = {
  labels,

  datasets: [
    {
      label: "Daily Sales ($)",
      data: salesData,
      backgroundColor: "#22c55e",
      borderColor: "#22c55e",
      tension: 0.3,
    },
  ],
};
  return (
    <div className="container-fluid py-4 px-md-5">
      {/* Header */}
      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 pb-3 border-bottom">
        <div>
          <h1 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
            <i className="bi bi-speedometer2 text-primary me-2"></i> Admin Control Panel
          </h1>
          <p className="text-muted mb-0">System administration, catalog CRUD, inventory control, and store analytics.</p>
        </div>
        <Link to="/admin/inbox" className="btn btn-success rounded-pill px-4 mt-3 mt-md-0">
          <i className="bi bi-headset me-1"></i> Support Inbox
        </Link>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-danger d-flex align-items-center mb-4" role="alert">
          <i className="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
          <div>{error}</div>
        </div>
      )}

      {/* Tabs Navigation */}
      <ul className="nav nav-pills gap-2 mb-4 bg-light p-2 rounded-4 shadow-sm border">
        {[
          { id: 'overview', label: 'Overview & Charts', icon: 'bi-grid-1x2-fill' },
          { id: 'books', label: 'Books CRUD', icon: 'bi-book-fill' },
          { id: 'genres', label: 'Genres CRUD', icon: 'bi-bookmarks-fill' },
          { id: 'inventory', label: 'Inventory Stock', icon: 'bi-box-seam-fill' },
          { id: 'stationery', label: 'Stationery', icon: 'bi-pen-fill' },
          { id: 'deals', label: 'Deals & Promos', icon: 'bi-tags-fill' },
          { id: 'users', label: 'Users', icon: 'bi-people-fill' },
          { id: 'orders', label: 'Orders', icon: 'bi-bag-check-fill' },
        ].map(({ id, label, icon }) => (
          <li key={id} className="nav-item">
            <button
              className={`nav-link rounded-pill px-3 py-2 fw-semibold ${activeTab === id ? 'active bg-primary' : 'text-dark'}`}
              onClick={() => setActiveTab(id)}
            >
              <i className={`bi ${icon} me-1.5`}></i> {label}
            </button>
          </li>
        ))}
      </ul>

      {/* TAB 1: OVERVIEW & CHARTS */}
      {activeTab === 'overview' && (
        loading ? (
          <LoadingSpinner message="Calculating store metrics & analytics..." />
        ) : (
          <div>
            {/* Top Metric Cards */}
            <div className="row g-4 mb-4">
              <div className="col-12 col-sm-6 col-xl-3">
                <div className="card border-0 shadow-sm rounded-4 p-3 bg-white border-start border-primary border-4">
                  <div className="d-flex align-items-center justify-content-between">
                    <div>
                      <small className="text-muted text-uppercase fw-bold">Total Revenue</small>
                      <h3 className="fw-bold mb-0 text-dark">
                        ${parseFloat(metrics?.total_revenue || 1450.5).toFixed(2)}
                      </h3>
                    </div>
                    <div className="rounded-circle bg-primary bg-opacity-10 p-3 text-primary">
                      <i className="bi bi-currency-dollar fs-3"></i>
                    </div>
                  </div>
                </div>
              </div>

              <div className="col-12 col-sm-6 col-xl-3">
                <div className="card border-0 shadow-sm rounded-4 p-3 bg-white border-start border-success border-4">
                  <div className="d-flex align-items-center justify-content-between">
                    <div>
                      <small className="text-muted text-uppercase fw-bold">Total Orders</small>
                      <h3 className="fw-bold mb-0 text-dark">{metrics?.total_orders || 28}</h3>
                    </div>
                    <div className="rounded-circle bg-success bg-opacity-10 p-3 text-success">
                      <i className="bi bi-bag-check fs-3"></i>
                    </div>
                  </div>
                </div>
              </div>

              <div className="col-12 col-sm-6 col-xl-3">
                <div className="card border-0 shadow-sm rounded-4 p-3 bg-white border-start border-warning border-4">
                  <div className="d-flex align-items-center justify-content-between">
                    <div>
                      <small className="text-muted text-uppercase fw-bold">Catalog Books</small>
                      <h3 className="fw-bold mb-0 text-dark">{metrics?.total_books || 45}</h3>
                    </div>
                    <div className="rounded-circle bg-warning bg-opacity-10 p-3 text-warning">
                      <i className="bi bi-book fs-3"></i>
                    </div>
                  </div>
                </div>
              </div>

              <div className="col-12 col-sm-6 col-xl-3">
                <div className="card border-0 shadow-sm rounded-4 p-3 bg-white border-start border-info border-4">
                  <div className="d-flex align-items-center justify-content-between">
                    <div>
                      <small className="text-muted text-uppercase fw-bold">Registered Users</small>
                      <h3 className="fw-bold mb-0 text-dark">{metrics?.total_users || 12}</h3>
                    </div>
                    <div className="rounded-circle bg-info bg-opacity-10 p-3 text-info">
                      <i className="bi bi-people fs-3"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Chart.js Analytics Grid */}
            <div className="row g-4">
              <div className="col-lg-7">
                <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
                  <h5 className="fw-bold mb-3">Revenue Growth Trend</h5>
                  <div style={{ height: '280px' }}>

                    <Line
  data={revenueChartData}
  options={{
    responsive: true,
    maintainAspectRatio: false,

    onClick: (event, elements) => {

      if (!elements.length) return;

      const monthNumbers = [7, 8, 9, 10, 11, 12];

      const index = elements[0].index;

      handleMonthClick(monthNumbers[index]);
    },
  }}
/>
                  </div>
                </div>
              </div>
              {selectedMonth && (
  <div className="col-lg-7">

    <div className="card border-0 shadow-sm rounded-4 p-4 bg-white mt-4">

      <h5 className="fw-bold mb-3">
        Daily Sales - Month {selectedMonth}
      </h5>

      <div style={{ height: '260px' }}>

        <Bar
          data={dailySalesChartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
          }}
        />

      </div>

    </div>

  </div>
)}

            <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
    <h5 className="fw-bold mb-3">
        Top 5 Selling Books
    </h5>

    <div className="table-responsive">

        <table className="table table-hover align-middle">

            <thead className="table-light">
                <tr>
                    <th>#</th>
                    <th>Book</th>
                    <th>Author</th>
                    <th className="text-end">
                        Units Sold
                    </th>
                </tr>
            </thead>

            <tbody>

                {topBooks.map((book,index)=>(
                    <tr key={book.book_id}>

                        <td>{index+1}</td>

                        <td className="fw-semibold">
                            {book.title}
                        </td>

                        <td>
                            {book.author}
                        </td>

                        <td className="text-end fw-bold">
                            {book.units_sold}
                        </td>

                    </tr>
                ))}

            </tbody>

        </table>

    </div>
</div>
            </div>
          </div>
        )
      )}

      {/* TAB 2: BOOKS CRUD */}
      {activeTab === 'books' && (
        <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h4 className="fw-bold mb-0">Book Catalog CRUD Management</h4>
            <button
              className="btn btn-accent rounded-pill px-4"
              onClick={() => {
                setEditingBookId(null);
                setBookFormData({ title: '', author: '', isbn: '', price: '', genre_id: 1, description: '', cover_image_url: '' });
                setShowBookModal(true);
              }}
            >
              <i className="bi bi-plus-circle me-1"></i> Add New Book
            </button>
          </div>

          {/* Book Form inline / modal */}
          {showBookModal && (
            <div className="bg-light p-4 rounded-4 mb-4 border">
              <h5 className="fw-bold mb-3">{editingBookId ? 'Edit Book' : 'Add New Book'}</h5>
              <form onSubmit={handleSaveBook}>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Title</label>
                    <input
                      type="text"
                      className="form-control"
                      value={bookFormData.title}
                      onChange={(e) => setBookFormData({ ...bookFormData, title: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Author</label>
                    <input
                      type="text"
                      className="form-control"
                      value={bookFormData.author}
                      onChange={(e) => setBookFormData({ ...bookFormData, author: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label small fw-semibold">ISBN</label>
                    <input
                      type="text"
                      className="form-control"
                      value={bookFormData.isbn}
                      onChange={(e) => setBookFormData({ ...bookFormData, isbn: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label small fw-semibold">Price ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-control"
                      value={bookFormData.price}
                      onChange={(e) => setBookFormData({ ...bookFormData, price: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label small fw-semibold">Genre ID</label>
                    <input
                      type="number"
                      className="form-control"
                      value={bookFormData.genre_id}
                      onChange={(e) => setBookFormData({ ...bookFormData, genre_id: e.target.value })}
                      required
                    />
                  </div>

                  {/* Cover Image Upload / URL */}
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Upload Book Image</label>
                    <input
                      type="file"
                      className="form-control"
                      accept="image/*"
                      onChange={handleBookFileUpload}
                      disabled={uploadingBookImg}
                    />
                    {uploadingBookImg && <small className="text-primary">Uploading image...</small>}
                  </div>
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Image URL (or static path)</label>
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control"
                        placeholder="/static/uploads/... or https://..."
                        value={bookFormData.cover_image_url || ''}
                        onChange={(e) => setBookFormData({ ...bookFormData, cover_image_url: e.target.value })}
                      />
                      {bookFormData.cover_image_url && (
                        <button
                          type="button"
                          className="btn btn-outline-danger"
                          onClick={() => setBookFormData({ ...bookFormData, cover_image_url: '' })}
                          title="Remove Image"
                        >
                          <i className="bi bi-x-circle"></i>
                        </button>
                      )}
                    </div>
                  </div>

                  {bookFormData.cover_image_url && (
                    <div className="col-12">
                      <small className="d-block text-muted mb-1">Image Preview:</small>
                      <img
                        src={bookFormData.cover_image_url}
                        alt="Book Cover Preview"
                        className="rounded border shadow-sm"
                        style={{ height: '80px', objectFit: 'cover' }}
                      />
                    </div>
                  )}

                  <div className="col-12">
                    <label className="form-label small fw-semibold">Description</label>
                    <textarea
                      className="form-control"
                      rows="2"
                      value={bookFormData.description || ''}
                      onChange={(e) => setBookFormData({ ...bookFormData, description: e.target.value })}
                    />
                  </div>
                </div>
                <div className="d-flex gap-2 mt-3">
                  <button type="submit" className="btn btn-accent rounded-pill px-4">
                    Save Book
                  </button>
                  <button type="button" className="btn btn-secondary rounded-pill px-3" onClick={() => setShowBookModal(false)}>
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="table-responsive">
            <table className="table align-middle">
              <thead className="table-light">
                <tr>
                  <th>ID</th>
                  <th>Cover</th>
                  <th>Title</th>
                  <th>Author</th>
                  <th>ISBN</th>
                  <th>Price</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {books.map((b) => (
                  <tr key={b.id}>
                    <td>#{b.id}</td>
                    <td>
                      {b.cover_image_url ? (
                        <img
                          src={b.cover_image_url}
                          alt={b.title}
                          className="rounded shadow-sm"
                          style={{ width: '40px', height: '55px', objectFit: 'cover' }}
                        />
                      ) : (
                        <div className="bg-light text-muted d-flex align-items-center justify-content-center rounded" style={{ width: '40px', height: '55px', fontSize: '1.2rem' }}>
                          <i className="bi bi-book"></i>
                        </div>
                      )}
                    </td>
                    <td className="fw-semibold">{b.title}</td>
                    <td>{b.author}</td>
                    <td>{b.isbn}</td>
                    <td className="fw-bold">${parseFloat(b.price).toFixed(2)}</td>
                    <td className="text-end">
                      <button
                        className="btn btn-sm btn-outline-primary me-2"
                        onClick={() => {
                          setEditingBookId(b.id);
                          setBookFormData({
                            title: b.title,
                            author: b.author,
                            isbn: b.isbn,
                            price: b.price,
                            genre_id: b.genre_id,
                            description: b.description || '',
                            cover_image_url: b.cover_image_url || '',
                          });
                          setShowBookModal(true);
                        }}
                      >
                        Edit
                      </button>
                      <button className="btn btn-sm btn-outline-danger" onClick={() => handleDeleteBook(b.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}


      {/* TAB 3: GENRES CRUD */}
      {activeTab === 'genres' && (
        <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <h4 className="fw-bold mb-4">Genre Category CRUD</h4>
          <form onSubmit={handleSaveGenre} className="mb-4 bg-light p-3 rounded-3 border">
            <div className="row g-3">
              <div className="col-md-5">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Genre Name"
                  value={genreForm.name}
                  onChange={(e) => setGenreForm({ ...genreForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="col-md-5">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Description"
                  value={genreForm.description}
                  onChange={(e) => setGenreForm({ ...genreForm, description: e.target.value })}
                />
              </div>
              <div className="col-md-2">
                <button type="submit" className="btn btn-accent w-100 rounded-pill">
                  Add Genre
                </button>
              </div>
            </div>
          </form>

          <table className="table align-middle">
            <thead className="table-light">
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th className="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {genres.map((g) => (
                <tr key={g.id}>
                  <td>#{g.id}</td>
                  <td className="fw-bold">{g.name}</td>
                  <td className="text-muted">{g.description || 'N/A'}</td>
                  <td className="text-end">
                    <button className="btn btn-sm btn-outline-danger" onClick={() => handleDeleteGenre(g.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 4: INVENTORY */}
      {activeTab === 'inventory' && (
        <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <h4 className="fw-bold mb-3">Low Stock Inventory Control</h4>
          <table className="table align-middle">
            <thead className="table-light">
              <tr>
                <th>Book ID</th>
                <th>Current Stock Quantity</th>
                <th>Stock Status</th>
                <th className="text-end">Stock Adjustments</th>
              </tr>
            </thead>
            <tbody>
              {lowStock.length === 0 ? (
                <tr><td colSpan="4" className="text-muted text-center py-4">No low stock alerts reported.</td></tr>
              ) : (
                lowStock.map((inv) => (
                  <tr key={inv.id}>
                    <td>Book #{inv.book_id}</td>
                    <td className="fw-bold fs-5">{inv.stock_quantity}</td>
                    <td>
                      {inv.stock_quantity <= 5 ? (
                        <span className="badge bg-danger">Critical Low</span>
                      ) : (
                        <span className="badge bg-warning text-dark">Warning</span>
                      )}
                    </td>
                    <td className="text-end">
                      <button className="btn btn-sm btn-success me-2" onClick={() => handleAdjustStock(inv.book_id, 10)}>
                        + Add 10 Stock
                      </button>
                      <button className="btn btn-sm btn-outline-danger" onClick={() => handleAdjustStock(inv.book_id, -1)}>
                        - 1 Stock
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 5: STATIONERY */}
      {activeTab === 'stationery' && (
        <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h4 className="fw-bold mb-0">Stationery Merchandise CRUD</h4>
            <button
              className="btn btn-accent rounded-pill px-4"
              onClick={() => {
                setEditingStatId(null);
                setStatForm({ name: '', price: '', stock: 10, description: '', cover_image_url: '' });
                setShowStatModal(true);
              }}
            >
              <i className="bi bi-plus-circle me-1"></i> Add New Stationery
            </button>
          </div>

          {/* Stationery Form inline / modal */}
          {showStatModal && (
            <div className="bg-light p-4 rounded-4 mb-4 border">
              <h5 className="fw-bold mb-3">{editingStatId ? 'Edit Stationery Item' : 'Add New Stationery Item'}</h5>
              <form onSubmit={handleSaveStationery}>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Item Name</label>
                    <input
                      type="text"
                      className="form-control"
                      value={statForm.name}
                      onChange={(e) => setStatForm({ ...statForm, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label small fw-semibold">Price ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-control"
                      value={statForm.price}
                      onChange={(e) => setStatForm({ ...statForm, price: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label small fw-semibold">Stock Quantity</label>
                    <input
                      type="number"
                      className="form-control"
                      value={statForm.stock}
                      onChange={(e) => setStatForm({ ...statForm, stock: e.target.value })}
                      required
                    />
                  </div>

                  {/* Image Upload / URL */}
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Upload Image</label>
                    <input
                      type="file"
                      className="form-control"
                      accept="image/*"
                      onChange={handleStatFileUpload}
                      disabled={uploadingStatImg}
                    />
                    {uploadingStatImg && <small className="text-primary">Uploading image...</small>}
                  </div>
                  <div className="col-md-6">
                    <label className="form-label small fw-semibold">Image URL (or static path)</label>
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control"
                        placeholder="/static/uploads/... or https://..."
                        value={statForm.cover_image_url || ''}
                        onChange={(e) => setStatForm({ ...statForm, cover_image_url: e.target.value })}
                      />
                      {statForm.image_url && (
                        <button
                          type="button"
                          className="btn btn-outline-danger"
                          onClick={() => setStatForm({ ...statForm, image_url: '' })}
                          title="Remove Image"
                        >
                          <i className="bi bi-x-circle"></i>
                        </button>
                      )}
                    </div>
                  </div>

                  {statForm.image_url && (
                    <div className="col-12">
                      <small className="d-block text-muted mb-1">Image Preview:</small>
                      <img
                        src={statForm.cover_image_url}
                        alt="Stationery Preview"
                        className="rounded border shadow-sm"
                        style={{ height: '70px', objectFit: 'cover' }}
                      />
                    </div>
                  )}

                  <div className="col-12">
                    <label className="form-label small fw-semibold">Description</label>
                    <textarea
                      className="form-control"
                      rows="2"
                      value={statForm.description || ''}
                      onChange={(e) => setStatForm({ ...statForm, description: e.target.value })}
                    />
                  </div>
                </div>
                <div className="d-flex gap-2 mt-3">
                  <button type="submit" className="btn btn-accent rounded-pill px-4">
                    Save Item
                  </button>
                  <button type="button" className="btn btn-secondary rounded-pill px-3" onClick={() => setShowStatModal(false)}>
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="table-responsive">
            <table className="table align-middle">
              <thead className="table-light">
                <tr>
                  <th>ID</th>
                  <th>Image</th>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Price</th>
                  <th>Stock</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {stationery.map((s) => (
                  <tr key={s.id}>
                    <td>#{s.id}</td>
                    <td>
                      {s.cover_image_url ? (
                        <img
                          src={s.cover_image_url}
                          alt={s.name}
                          className="rounded shadow-sm"
                          style={{ width: '45px', height: '45px', objectFit: 'cover' }}
                        />
                      ) : (
                        <div className="bg-light text-muted d-flex align-items-center justify-content-center rounded" style={{ width: '45px', height: '45px', fontSize: '1.2rem' }}>
                          <i className="bi bi-pen"></i>
                        </div>
                      )}
                    </td>
                    <td className="fw-bold">{s.name}</td>
                    <td className="text-muted small" style={{ maxWidth: '250px' }}>{s.description || 'N/A'}</td>
                    <td className="fw-bold">${parseFloat(s.price).toFixed(2)}</td>
                    <td>
                      <span className={`badge ${s.stock > 0 ? 'bg-success' : 'bg-secondary'}`}>
                        {s.stock} in stock
                      </span>
                    </td>
                    <td className="text-end">
                      <button
                        className="btn btn-sm btn-outline-primary me-2"
                        onClick={() => {
                          setEditingStatId(s.id);
                          setStatForm({
                            name: s.name,
                            price: s.price,
                            stock: s.stock,
                            description: s.description || '',
                            cover_image_url: s.cover_image_url || '',
                          });
                          setShowStatModal(true);
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={async () => {
                          if (window.confirm('Delete this stationery item?')) {
                            await adminService.deleteStationery(s.id);
                            fetchTabData('stationery');
                          }
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}


      {/* TAB 6: DEALS */}
      {activeTab === 'deals' && (
        <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <h4 className="fw-bold mb-4">Deals & Promotional Discounts</h4>
          <table className="table align-middle">
            <thead className="table-light">
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Discount (%)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((d) => (
                <tr key={d.id}>
                  <td>#{d.id}</td>
                  <td className="fw-bold">{d.title}</td>
                  <td className="text-danger fw-bold">{d.discount_percentage}% OFF</td>
                  <td>
                    <span className={`badge ${d.is_active ? 'bg-success' : 'bg-secondary'}`}>
                      {d.is_active ? 'Active' : 'Expired'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 7: USERS */}
      {activeTab === 'users' && (
        <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <h4 className="fw-bold mb-4">Registered User Accounts</h4>
          <table className="table align-middle">
            <thead className="table-light">
              <tr>
                <th>User ID</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Role</th>
                <th className="text-end">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>#{u.id}</td>
                  <td className="fw-bold">{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>
                    <span className={`badge ${u.role === 'admin' ? 'bg-primary' : 'bg-secondary'}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="text-end">
                    {u.role !== 'admin' && (
                      <Link
                        to={`/admin/inbox/${u.id}`}
                        className="btn btn-sm btn-outline-primary me-2"
                        title={`Chat with ${u.full_name}`}
                      >
                        <i className="bi bi-chat-dots-fill"></i>
                      </Link>
                    )}
                    <button className="btn btn-sm btn-outline-danger" onClick={async () => {
                      if (window.confirm('Delete user account?')) {
                        await adminService.deleteUser(u.id);
                        fetchTabData('users');
                      }
                    }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 8: ORDERS */}
      {activeTab === 'orders' && (
        <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <h4 className="fw-bold mb-4">Customer Order Management</h4>
          <table className="table align-middle">
            <thead className="table-light">
              <tr>
                <th>Order ID</th>
                <th>User ID</th>
                <th>Total Amount</th>
                <th>Status</th>
                <th className="text-end">Update Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>#{o.id}</td>
                  <td>User #{o.user_id}</td>
                  <td className="fw-bold">${parseFloat(o.total_amount).toFixed(2)}</td>
                  <td>
                    <span className="badge bg-info text-dark">{o.status}</span>
                  </td>
                  <td className="text-end">
                    <select
                      className="form-select form-select-sm d-inline-block w-auto"
                      value={o.status}
                      onChange={(e) => handleOrderStatus(o.id, e.target.value)}
                    >
                      <option value="pending">pending</option>
                      <option value="processing">processing</option>
                      <option value="shipped">shipped</option>
                      <option value="delivered">delivered</option>
                      <option value="cancelled">cancelled</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;