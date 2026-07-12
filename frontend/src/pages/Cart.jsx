import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import cartService from '../api/cartService';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { extractErrorMessage } from '../utils/errorUtils';

const Cart = () => {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingItemId, setUpdatingItemId] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchCart = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await cartService.getCart();
      setCart(data);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to retrieve your shopping cart.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) return;
    setUpdatingItemId(itemId);
    setError(null);
    try {
      await cartService.updateQuantity(itemId, newQuantity);
      await fetchCart();
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to update item quantity. Insufficient stock available.'));
    } finally {
      setUpdatingItemId(null);
    }
  };

  const handleRemoveItem = async (itemId) => {
    setUpdatingItemId(itemId);
    setError(null);
    try {
      await cartService.removeFromCart(itemId);
      await fetchCart();
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to remove item from cart.'));
    } finally {
      setUpdatingItemId(null);
    }
  };

  const handleClearCart = async () => {
    if (!window.confirm('Are you sure you want to clear your entire cart?')) return;
    setLoading(true);
    setError(null);
    try {
      await cartService.clearCart();
      await fetchCart();
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to clear cart.'));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Retrieving your shopping cart..." />;
  }

  const items = cart?.items || [];
  const isEmpty = items.length === 0;

  return (
    <div className="container py-4">
      {/* Title */}
      <div className="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom">
        <h1 className="fw-bold mb-0" style={{ fontFamily: 'var(--font-heading)' }}>
          <i className="bi bi-cart3 me-2 text-primary"></i> Shopping Cart
        </h1>
        {!isEmpty && (
          <button
            className="btn btn-outline-danger btn-sm rounded-pill"
            onClick={handleClearCart}
          >
            <i className="bi bi-trash me-1"></i> Clear Cart
          </button>
        )}
      </div>

      {/* Backend Error Alert */}
      {error && (
        <div className="alert alert-danger d-flex align-items-center mb-4" role="alert">
          <i className="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
          <div>{error}</div>
        </div>
      )}

      {isEmpty ? (
        <EmptyState
          icon="bi-cart-x"
          title="Your Cart is Empty"
          message="You haven't added any books to your shopping cart yet."
          actionText="Explore Book Catalog"
          onAction={() => navigate('/books')}
        />
      ) : (
        <div className="row g-4">
          {/* Cart Items List */}
          <div className="col-lg-8">
            <div className="card border-0 shadow-sm rounded-4 p-3 bg-white">
              <div className="table-responsive">
                <table className="table align-middle mb-0">
                  <thead className="table-light text-muted small uppercase">
                    <tr>
                      <th scope="col" style={{ width: '40%' }}>Book</th>
                      <th scope="col" className="text-center">Price</th>
                      <th scope="col" className="text-center">Quantity</th>
                      <th scope="col" className="text-end">Subtotal</th>
                      <th scope="col" className="text-center" style={{ width: '10%' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr key={item.id}>
                        {/* Book Details */}
                        <td>
                          <div className="d-flex align-items-center">
                            <div className="bg-light rounded p-2 text-center me-3" style={{ width: '48px', height: '60px' }}>
                              <i className="bi bi-book fs-3 text-secondary"></i>
                            </div>
                            <div>
                              <Link to={`/books/${item.book_id}`} className="fw-bold text-dark text-decoration-none">
                                {item.book_title}
                              </Link>
                              <small className="text-muted d-block">ID: #{item.book_id}</small>
                            </div>
                          </div>
                        </td>

                        {/* Unit Price */}
                        <td className="text-center fw-semibold">
                          ${parseFloat(item.price_at_add_time).toFixed(2)}
                        </td>

                        {/* Quantity Controls */}
                        <td className="text-center">
                          <div className="d-inline-flex align-items-center border rounded-pill p-1">
                            <button
                              className="btn btn-sm btn-link text-dark p-0 px-2"
                              onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}
                              disabled={updatingItemId === item.id || item.quantity <= 1}
                            >
                              <i className="bi bi-dash"></i>
                            </button>
                            <span className="px-2 fw-bold small">{item.quantity}</span>
                            <button
                              className="btn btn-sm btn-link text-dark p-0 px-2"
                              onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                              disabled={updatingItemId === item.id}
                            >
                              <i className="bi bi-plus"></i>
                            </button>
                          </div>
                        </td>

                        {/* Subtotal */}
                        <td className="text-end fw-bold text-accent" style={{ color: 'var(--color-accent)' }}>
                          ${parseFloat(item.subtotal).toFixed(2)}
                        </td>

                        {/* Delete Action */}
                        <td className="text-center">
                          <button
                            className="btn btn-sm btn-outline-danger border-0 rounded-circle"
                            onClick={() => handleRemoveItem(item.id)}
                            disabled={updatingItemId === item.id}
                            title="Remove Item"
                          >
                            <i className="bi bi-trash"></i>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Cart Order Summary Sidebar */}
          <div className="col-lg-4">
            <div className="card border-0 shadow-lg rounded-4 p-4 bg-white sticky-top" style={{ top: '100px' }}>
              <h4 className="fw-bold mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                Order Summary
              </h4>

              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Subtotal</span>
                <span className="fw-semibold">${parseFloat(cart?.subtotal || 0).toFixed(2)}</span>
              </div>

              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Discount</span>
                <span className="fw-semibold text-success">
                  -${parseFloat(cart?.discount || 0).toFixed(2)}
                </span>
              </div>

              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Tax (5%)</span>
                <span className="fw-semibold">${parseFloat(cart?.tax || 0).toFixed(2)}</span>
              </div>

              <div className="d-flex justify-content-between mb-3">
                <span className="text-muted">Flat Shipping</span>
                <span className="fw-semibold">${parseFloat(cart?.shipping || 0).toFixed(2)}</span>
              </div>

              <hr />

              <div className="d-flex justify-content-between align-items-center mb-4">
                <span className="fw-bold fs-5">Estimated Total</span>
                <span className="fw-bold fs-4 text-accent" style={{ color: 'var(--color-accent)' }}>
                  ${parseFloat(cart?.estimated_total || 0).toFixed(2)}
                </span>
              </div>

              <button
                className="btn btn-accent w-100 py-3 rounded-pill fw-bold shadow-sm"
                onClick={() => navigate('/checkout')}
              >
                Proceed to Checkout <i className="bi bi-arrow-right ms-2"></i>
              </button>

              <div className="text-center mt-3">
                <Link to="/books" className="text-muted small text-decoration-none">
                  <i className="bi bi-arrow-left me-1"></i> Continue Shopping
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cart;
