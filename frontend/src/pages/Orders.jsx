import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import orderService from '../api/orderService';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [cancellingId, setCancellingId] = useState(null);
  const [cancelError, setCancelError] = useState(null);

  const formatDateTime = (isoString) => {
    if (!isoString) return null;
    return new Date(isoString).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  // Map the backend OrderResponse shape onto the fields this page renders.
  const normalizeOrder = (order) => {
    const purchasedItems = (order.items || []).map((item) => ({
      title: item.book?.title || `Book #${item.book_id}`,
      quantity: item.quantity,
      unit_price: Number(item.purchase_price),
      total_price: Number(item.purchase_price) * item.quantity,
    }));

    return {
      ...order,
      order_id: order.id,
      order_number: `ORD-${String(order.id).padStart(6, '0')}`,
      purchased_items: purchasedItems,
      grand_total: Number(order.total_amount),
      placed_at: order.created_at,
      delivered_at: order.delivered_at || null,
      subtotal: undefined,
      tax: undefined,
      shipping: undefined,
    };
  };

  const loadOrders = async () => {
    try {
      const data = await orderService.getMyOrders();
      const normalized = data.map(normalizeOrder);
      setOrders(normalized);
      // Keep the detail panel in sync with any status change (e.g. admin update)
      setSelectedOrder((prev) => {
        if (!prev) return prev;
        return normalized.find((o) => o.order_id === prev.order_id) || prev;
      });
      return normalized;
    } catch (err) {
      setCancelError(err?.response?.data?.detail || 'Failed to load orders.');
      return null;
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadOrders();
      setLoading(false);
    })();

    // Poll for status changes made elsewhere (e.g. by an admin) while this page is open.
    const intervalId = setInterval(loadOrders, 15000);

    // Also refresh immediately whenever the tab regains focus.
    const onFocus = () => loadOrders();
    window.addEventListener('focus', onFocus);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('focus', onFocus);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCancelOrder = async (order) => {
    if (order.status?.toLowerCase() !== 'pending') return;
    const confirmed = window.confirm(`Cancel order #${order.order_number}? This cannot be undone.`);
    if (!confirmed) return;

    setCancellingId(order.order_id);
    setCancelError(null);
    try {
      const updatedFromServer = await orderService.cancelOrder(order.order_id);
      const normalizedUpdated = normalizeOrder(updatedFromServer);
      const updated = orders.map((o) =>
        o.order_id === order.order_id ? normalizedUpdated : o
      );
      setOrders(updated);
      setSelectedOrder((prev) =>
        prev?.order_id === order.order_id ? normalizedUpdated : prev
      );
    } catch (err) {
      setCancelError(err?.response?.data?.detail || 'Failed to cancel order. Please try again.');
    } finally {
      setCancellingId(null);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading your order history..." />;
  }

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <span className="badge bg-success px-3 py-1.5 rounded-pill"><i className="bi bi-check-circle me-1"></i>Completed</span>;
      case 'pending':
        return <span className="badge bg-warning text-dark px-3 py-1.5 rounded-pill"><i className="bi bi-clock me-1"></i>Pending</span>;
      case 'processing':
        return <span className="badge bg-info text-dark px-3 py-1.5 rounded-pill"><i className="bi bi-gear-spin me-1"></i>Processing</span>;
      case 'cancelled':
        return <span className="badge bg-danger px-3 py-1.5 rounded-pill"><i className="bi bi-x-circle me-1"></i>Cancelled</span>;
      default:
        return <span className="badge bg-secondary px-3 py-1.5 rounded-pill">{status}</span>;
    }
  };

  return (
    <div className="container py-4">
      {/* Title */}
      <h1 className="fw-bold mb-4 pb-2 border-bottom" style={{ fontFamily: 'var(--font-heading)' }}>
        <i className="bi bi-bag-check me-2 text-primary"></i> Order History
      </h1>

      {orders.length === 0 ? (
        <EmptyState
          icon="bi-box"
          title="No Orders Placed Yet"
          message="When you purchase books, your completed orders and receipts will appear here."
          actionText="Browse Book Catalog"
          onAction={() => window.location.href = '/books'}
        />
      ) : (
        <div className="row g-4">
          {/* Orders List */}
          <div className="col-lg-7">
            <div className="d-flex flex-column gap-3">
              {orders.map((order, idx) => (
                <div
                  key={order.order_id || idx}
                  className={`card border-0 shadow-sm rounded-4 p-4 transition-all hover-shadow cursor-pointer ${
                    selectedOrder?.order_id === order.order_id ? 'border-primary border-2' : ''
                  }`}
                  onClick={() => setSelectedOrder(order)}
                >
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <div>
                      <h5 className="fw-bold text-dark mb-1">Order #{order.order_number}</h5>
                      <small className="text-muted">
                        <i className="bi bi-geo-alt me-1"></i> {order.shipping_address}
                      </small>
                    </div>
                    {getStatusBadge(order.status)}
                  </div>

                  <div className="d-flex justify-content-between align-items-center pt-3 border-top">
                    <div>
                      <span className="text-muted small d-block">Items: {order.purchased_items?.length || 0}</span>
                    </div>
                    <div className="text-end">
                      <span className="text-muted small d-block">Grand Total</span>
                      <span className="fw-bold fs-5 text-accent" style={{ color: 'var(--color-accent)' }}>
                        ${order.grand_total ? order.grand_total.toFixed(2) : '0.00'}
                      </span>
                    </div>
                  </div>

                  {order.status?.toLowerCase() === 'pending' && (
                    <div className="pt-3 mt-1 border-top text-end">
                      <button
                        type="button"
                        className="btn btn-outline-danger btn-sm rounded-pill px-3"
                        disabled={cancellingId === order.order_id}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCancelOrder(order);
                        }}
                      >
                        {cancellingId === order.order_id ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                            Cancelling...
                          </>
                        ) : (
                          <>
                            <i className="bi bi-x-circle me-1"></i> Cancel Order
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Selected Order Details Panel */}
          <div className="col-lg-5">
            {selectedOrder ? (
              <div className="card border-0 shadow-lg rounded-4 p-4 bg-white sticky-top" style={{ top: '100px' }}>
                <div className="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
                  <h4 className="fw-bold mb-0">Order Details</h4>
                  <button className="btn-close" onClick={() => setSelectedOrder(null)}></button>
                </div>

                <div className="mb-3">
                  <span className="text-muted small d-block">Order Reference</span>
                  <strong className="fs-5">#{selectedOrder.order_number}</strong>
                </div>

                <div className="mb-3">
                  <span className="text-muted small d-block">Status</span>
                  <div className="mt-1 d-flex align-items-center gap-2">
                    {getStatusBadge(selectedOrder.status)}
                    {selectedOrder.status?.toLowerCase() === 'pending' && (
                      <button
                        type="button"
                        className="btn btn-outline-danger btn-sm rounded-pill px-3"
                        disabled={cancellingId === selectedOrder.order_id}
                        onClick={() => handleCancelOrder(selectedOrder)}
                      >
                        {cancellingId === selectedOrder.order_id ? 'Cancelling...' : 'Cancel Order'}
                      </button>
                    )}
                  </div>
                  {cancelError && (
                    <div className="alert alert-danger py-2 px-3 mt-2 small mb-0">{cancelError}</div>
                  )}
                </div>

                <div className="mb-3">
                  <span className="text-muted small d-block">Shipping Address</span>
                  <p className="fw-semibold text-dark mb-0">{selectedOrder.shipping_address}</p>
                </div>

                <div className="mb-3">
                  <span className="text-muted small d-block">
                    <i className="bi bi-calendar-check me-1"></i> Order Placed
                  </span>
                  <p className="fw-semibold text-dark mb-0">
                    {formatDateTime(selectedOrder.placed_at) || '—'}
                  </p>
                </div>

                {selectedOrder.status?.toLowerCase() === 'delivered' && (
                  <div className="mb-3">
                    <span className="text-muted small d-block">
                      <i className="bi bi-box-seam me-1"></i> Delivered
                    </span>
                    <p className="fw-semibold text-success mb-0">
                      {formatDateTime(selectedOrder.delivered_at) || '—'}
                    </p>
                  </div>
                )}

                <h6 className="fw-bold mb-2 border-top pt-3">Purchased Items</h6>
                <div className="bg-light p-3 rounded-3 mb-3">
                  {selectedOrder.purchased_items?.map((item, i) => (
                    <div key={i} className="d-flex justify-content-between align-items-center mb-2">
                      <div>
                        <span className="fw-semibold text-dark d-block">{item.title}</span>
                        <small className="text-muted">Qty: {item.quantity} × ${item.unit_price.toFixed(2)}</small>
                      </div>
                      <span className="fw-bold">${item.total_price.toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                <div className="border-top pt-2">
                  <div className="d-flex justify-content-between fw-bold fs-5 text-dark mt-2 pt-2">
                    <span>Grand Total:</span>
                    <span className="text-accent" style={{ color: 'var(--color-accent)' }}>
                      ${selectedOrder.grand_total?.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="card border-0 shadow-sm rounded-4 p-4 text-center text-muted bg-light">
                <i className="bi bi-cursor display-4 mb-2"></i>
                <p className="mb-0">Click any order on the left to view detailed breakdown.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;