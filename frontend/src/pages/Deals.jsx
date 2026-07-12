import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import bookService from '../api/bookService';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { extractErrorMessage } from '../utils/errorUtils';

const Deals = () => {
  const [dealBooks, setDealBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fallbackCover = 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80';

  useEffect(() => {
    const fetchDeals = async () => {
      setLoading(true);
      setError(null);
      try {
        const books = await bookService.listBooks({ page: 1, page_size: 12 });
        // Map deal discount structure (e.g., 20% promotional discount)
        const formattedDeals = books.map((book, index) => {
          const discountPercent = [15, 20, 25, 30][index % 4];
          const originalPrice = (parseFloat(book.price) * (1 + discountPercent / 100)).toFixed(2);
          return {
            ...book,
            discountPercent,
            originalPrice,
          };
        });
        setDealBooks(formattedDeals);
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to fetch active promotions.'));
      } finally {
        setLoading(false);
      }
    };

    fetchDeals();
  }, []);

  return (
    <div className="container py-4">
      {/* Banner */}
      <div
        className="p-5 mb-5 rounded-4 text-white shadow-lg position-relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #d97706 0%, #b45309 50%, #78350f 100%)',
        }}
      >
        <div className="row align-items-center">
          <div className="col-lg-8">
            <span className="badge bg-white text-dark px-3 py-2 rounded-pill fw-bold mb-3">
              <i className="bi bi-percent me-1 text-danger"></i> Limited Time Offer
            </span>
            <h1 className="display-4 fw-bold mb-3" style={{ fontFamily: 'var(--font-serif)' }}>
              Exclusive Literary Deals & Bundles
            </h1>
            <p className="lead opacity-90 mb-0">
              Save up to 30% on bestselling titles, award winners, and editor picks this week.
            </p>
          </div>
          <div className="col-lg-4 d-none d-lg-block text-end">
            <i className="bi bi-tags-fill display-1 opacity-25"></i>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      {loading ? (
        <LoadingSpinner message="Calculating promotional discount deals..." />
      ) : error ? (
        <div className="alert alert-danger" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {error}
        </div>
      ) : dealBooks.length === 0 ? (
        <EmptyState
          icon="bi-tag"
          title="No Active Deals"
          message="Check back soon for upcoming holiday promotions and reading bundle deals."
        />
      ) : (
        <div className="row g-4">
          {dealBooks.map((book) => (
            <div key={book.id} className="col-12 col-sm-6 col-md-4 col-lg-3">
              <div className="card h-100 border-0 shadow-sm rounded-4 overflow-hidden position-relative hover-shadow transition-all">
                {/* Discount Badge */}
                <span className="position-absolute top-0 start-0 m-3 badge bg-danger fs-6 px-3 py-2 rounded-pill shadow-sm">
                  -{book.discountPercent}% OFF
                </span>

                <div className="bg-light text-center py-4 px-3">
                  <img
                    src={book.cover_image_url || fallbackCover}
                    alt={book.title}
                    className="img-fluid rounded shadow-sm"
                    style={{ height: '180px', objectFit: 'cover' }}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = fallbackCover;
                    }}
                  />
                </div>

                <div className="card-body d-flex flex-column justify-content-between p-3">
                  <div>
                    <h6 className="fw-bold text-dark text-truncate mb-1">{book.title}</h6>
                    <p className="text-muted small mb-3">{book.author}</p>
                  </div>

                  <div className="pt-2 border-top">
                    <div className="d-flex align-items-center gap-2 mb-3">
                      <span className="fs-4 fw-bold text-danger">${parseFloat(book.price).toFixed(2)}</span>
                      <span className="text-muted text-decoration-line-through small">
                        ${book.originalPrice}
                      </span>
                    </div>
                    <Link
                      to={`/books/${book.id}`}
                      className="btn btn-sm btn-accent w-100 rounded-pill py-2 fw-semibold"
                    >
                      View Deal Details
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Deals;
