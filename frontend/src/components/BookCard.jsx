import React, { useContext, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import cartService from '../api/cartService';
import { extractErrorMessage } from '../utils/errorUtils';

const BookCard = ({ book, genreName }) => {
  const { isAuthenticated } = useContext(AuthContext);
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [feedback, setFeedback] = useState({ message: '', type: '' });
  const [showUnavailable, setShowUnavailable] = useState(false);

  const fallbackCover = 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80';

  // Stock is considered unknown (treated as available) if inventory info
  // wasn't included in the API response, so the button isn't wrongly disabled.
  const stockQuantity = book.inventory?.stock_quantity;
  const inStock = stockQuantity === undefined || stockQuantity > 0;

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: window.location } });
      return;
    }

    // Short-circuit before hitting the API if we already know it's out of stock.
    if (!inStock) {
      setShowUnavailable(true);
      return;
    }

    setAdding(true);
    setFeedback({ message: '', type: '' });
    try {
      await cartService.addToCart(book.id, 1);
      setFeedback({ message: 'Added!', type: 'success' });
      setTimeout(() => setFeedback({ message: '', type: '' }), 2500);
    } catch (err) {
      const msg = extractErrorMessage(err, 'Failed to add item.');
      // If the backend rejects it for stock reasons (e.g. race condition
      // where stock hit 0 between page load and click), show the same popup.
      if (err?.response?.status === 400 && /stock/i.test(msg)) {
        setShowUnavailable(true);
      } else {
        setFeedback({ message: msg, type: 'error' });
        setTimeout(() => setFeedback({ message: '', type: '' }), 4000);
      }
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="card h-100 border-0 shadow-sm rounded-3 overflow-hidden transition-all hover-shadow">
      <div className="position-relative bg-light text-center py-3 px-2">
        <img
          src={book.cover_image_url || fallbackCover}
          alt={book.title}
          className="img-fluid rounded shadow-sm"
          style={{ height: '200px', objectFit: 'cover' }}
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = fallbackCover;
          }}
        />
        {genreName && (
          <span className="position-absolute top-0 end-0 m-2 badge bg-primary opacity-90 fw-normal">
            {genreName}
          </span>
        )}
        {!inStock && (
          <span className="position-absolute top-0 start-0 m-2 badge bg-danger opacity-90 fw-normal">
            Out of stock
          </span>
        )}
      </div>

      <div className="card-body d-flex flex-column justify-content-between p-3">
        <div>
          <h6 className="card-title fw-bold text-dark text-truncate mb-1" title={book.title}>
            {book.title}
          </h6>
          <p className="card-subtitle text-muted small mb-2">{book.author}</p>
          <small className="text-secondary d-block text-truncate mb-2" style={{ fontSize: '0.8rem' }}>
            ISBN: {book.isbn}
          </small>
        </div>

        {feedback.message && (
          <div
            className={`alert ${feedback.type === 'success' ? 'alert-success' : 'alert-danger'} py-1 px-2 mb-2 small text-center`}
            style={{ fontSize: '0.75rem' }}
          >
            {feedback.message}
          </div>
        )}

        <div className="d-flex align-items-center justify-content-between pt-2 border-top">
          <span className="fw-bold fs-5 text-accent" style={{ color: 'var(--color-accent)' }}>
            ${parseFloat(book.price).toFixed(2)}
          </span>
          <div className="d-flex gap-1">
            <button
              className="btn btn-sm btn-accent rounded-pill px-2"
              onClick={handleAddToCart}
              disabled={adding || !inStock}
              title={inStock ? 'Add to Cart' : 'Unavailable'}
            >
              {adding ? (
                <span className="spinner-border spinner-border-sm" role="status"></span>
              ) : inStock ? (
                <><i className="bi bi-cart-plus me-1"></i> Add</>
              ) : (
                'Unavailable'
              )}
            </button>
            <Link to={`/books/${book.id}`} className="btn btn-sm btn-outline-dark rounded-pill px-2">
              Details
            </Link>
          </div>
        </div>
      </div>

      {showUnavailable && (
        <div
          className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
          style={{ background: 'rgba(0,0,0,0.5)', zIndex: 1050 }}
          onClick={() => setShowUnavailable(false)}
        >
          <div
            className="bg-white rounded-3 shadow p-4 text-center"
            style={{ maxWidth: '320px' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h6 className="fw-bold mb-2">Unavailable</h6>
            <p className="text-muted small mb-3">
              "{book.title}" is currently out of stock.
            </p>
            <button
              className="btn btn-sm btn-accent rounded-pill px-4"
              onClick={() => setShowUnavailable(false)}
            >
              OK
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BookCard;