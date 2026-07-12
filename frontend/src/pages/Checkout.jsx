import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import cartService from '../api/cartService';
import checkoutService from '../api/checkoutService';
import paymentService from '../api/paymentService';
import LoadingSpinner from '../components/LoadingSpinner';
import { extractErrorMessage } from '../utils/errorUtils';

const Checkout = () => {
  const [cart, setCart] = useState(null);
  const [loadingCart, setLoadingCart] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [orderSummary, setOrderSummary] = useState(null);
  const [paymentOutcome, setPaymentOutcome] = useState(null); // 'paid' | 'pending_card_issue' | null

  // Form State
  const [shippingAddress, setShippingAddress] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('card'); // 'card' | 'cod'

  // Card Form State (only used when paymentMethod === 'card')
  const [cardNumber, setCardNumber] = useState('');
  const [nameOnCard, setNameOnCard] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [cvv, setCvv] = useState('');
  const [saveCard, setSaveCard] = useState(true);

  const navigate = useNavigate();

  // Basic client-side card validation (Luhn check + expiry + CVV format).
  // Backend re-validates independently; this just gives instant feedback.
  const validateCardInput = () => {
    if (!nameOnCard.trim()) {
      return 'Please enter the name on the card.';
    }

    const digitsOnly = cardNumber.replace(/\D/g, '');
    if (digitsOnly.length < 13 || digitsOnly.length > 19) {
      return 'Card number must be between 13 and 19 digits.';
    }
    let checksum = 0;
    const reversed = digitsOnly.split('').reverse();
    for (let i = 0; i < reversed.length; i++) {
      let d = parseInt(reversed[i], 10);
      if (i % 2 === 1) {
        d *= 2;
        if (d > 9) d -= 9;
      }
      checksum += d;
    }
    if (checksum % 10 !== 0) {
      return 'Card number is invalid. Please double-check the digits.';
    }

    const expiryMatch = /^(\d{2})\/(\d{2})$/.exec(expiryDate.trim());
    if (!expiryMatch) {
      return 'Expiry date must be in MM/YY format.';
    }
    const expMonth = parseInt(expiryMatch[1], 10);
    const expYear = 2000 + parseInt(expiryMatch[2], 10);
    if (expMonth < 1 || expMonth > 12) {
      return 'Expiry month is invalid.';
    }
    const now = new Date();
    const expiryDateObj = new Date(expYear, expMonth); // first day of month after expiry
    if (expiryDateObj <= now) {
      return 'This card has expired.';
    }

    if (!/^\d{3,4}$/.test(cvv.trim())) {
      return 'CVV must be 3 or 4 digits.';
    }

    return null;
  };

  useEffect(() => {
    const fetchCart = async () => {
      setLoadingCart(true);
      setError(null);
      try {
        const data = await cartService.getCart();
        setCart(data);
        if (!data.items || data.items.length === 0) {
          setError('Your cart is empty. Please add items before checking out.');
        }
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to fetch cart for checkout.'));
      } finally {
        setLoadingCart(false);
      }
    };

    fetchCart();
  }, []);

  const handleCheckoutSubmit = async (e) => {
    e.preventDefault();
    if (!shippingAddress.trim()) {
      setError('Please enter a valid shipping address.');
      return;
    }

    if (paymentMethod === 'card') {
      const cardValidationError = validateCardInput();
      if (cardValidationError) {
        setError(cardValidationError);
        return;
      }
    }

    setSubmitting(true);
    setError(null);
    try {
      // Step 1: Create the order via checkout
      const summary = await checkoutService.processCheckout(
        shippingAddress.trim(),
        paymentMethod === 'card' ? 'card' : 'cash_on_delivery'
      );

      if (paymentMethod === 'cod') {
        // Cash on Delivery: no gateway call needed, order is placed as-is.
        setOrderSummary(summary);
        setPaymentOutcome('cod');
      } else {
        // Card: immediately charge the card through the payment gateway.
        try {
          const pendingPayment = await paymentService.createPayment(
            summary.order_id,
            'card',
            cardNumber.replace(/\D/g, '')
          );
          const receipt = await paymentService.confirmPayment(pendingPayment.transaction_id);
          setOrderSummary({ ...summary, payment_status: 'succeeded' });
          setPaymentOutcome({ status: 'paid', receipt, last4: pendingPayment.last4 });
        } catch (paymentErr) {
          // Order was created successfully, but the card charge failed.
          // Let the user know they can retry payment from their Orders page.
          setOrderSummary(summary);
          setPaymentOutcome({
            status: 'card_failed',
            message: extractErrorMessage(paymentErr, 'Card payment could not be completed.'),
          });
        }
      }

      // Save created order into session storage for order details view
      const existingOrders = JSON.parse(sessionStorage.getItem('my_orders') || '[]');
      sessionStorage.setItem('my_orders', JSON.stringify([summary, ...existingOrders]));
    } catch (err) {
      setError(extractErrorMessage(err, 'Checkout failed. Please check stock availability or try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingCart) {
    return <LoadingSpinner message="Preparing checkout details..." />;
  }

  // Order Confirmation State after successful checkout
  if (orderSummary) {
    return (
      <div className="container py-5">
        <div className="card border-0 shadow-lg rounded-4 overflow-hidden max-w-2xl mx-auto p-4 p-md-5">
          <div className="text-center mb-4">
            <div className="rounded-circle bg-success bg-opacity-10 text-success d-inline-flex p-3 mb-3">
              <i className="bi bi-check-circle-fill display-4"></i>
            </div>
            <h2 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
              Order Placed Successfully!
            </h2>
            <p className="text-muted">Thank you for your purchase from BookHaven.</p>
            <span className="badge bg-secondary px-3 py-2 fs-6 rounded-pill">
              Order #{orderSummary.order_number}
            </span>
          </div>

          {paymentOutcome === 'cod' && (
            <div className="alert alert-info d-flex align-items-center mb-4" role="alert">
              <i className="bi bi-cash-coin fs-4 me-3"></i>
              <div>
                <strong>Cash on Delivery selected.</strong> Please have ${orderSummary.grand_total.toFixed(2)} ready
                for the courier when your order arrives.
              </div>
            </div>
          )}

          {paymentOutcome?.status === 'paid' && (
            <div className="alert alert-success d-flex align-items-center mb-4" role="alert">
              <i className="bi bi-check-circle-fill fs-4 me-3"></i>
              <div>
                <strong>Payment successful.</strong> Card ending in •••• {paymentOutcome.last4} was charged
                ${orderSummary.grand_total.toFixed(2)}.
              </div>
            </div>
          )}

          {paymentOutcome?.status === 'card_failed' && (
            <div className="alert alert-warning d-flex align-items-center mb-4" role="alert">
              <i className="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
              <div>
                <strong>Order placed, but card payment failed.</strong> {paymentOutcome.message} You can retry
                payment from{' '}
                <Link to={`/payment/${orderSummary.order_id}`} className="alert-link">
                  the payment page
                </Link>.
              </div>
            </div>
          )}

          <div className="bg-light p-4 rounded-3 mb-4">
            <h6 className="fw-bold mb-3 border-bottom pb-2">Order Breakdown</h6>
            {orderSummary.purchased_items.map((item, idx) => (
              <div key={idx} className="d-flex justify-content-between align-items-center mb-2">
                <div>
                  <span className="fw-semibold text-dark">{item.title}</span>
                  <small className="text-muted d-block">Qty: {item.quantity} × ${item.unit_price.toFixed(2)}</small>
                </div>
                <span className="fw-bold">${item.total_price.toFixed(2)}</span>
              </div>
            ))}
            <hr />
            <div className="d-flex justify-content-between mb-1 text-muted small">
              <span>Subtotal:</span>
              <span>${orderSummary.subtotal.toFixed(2)}</span>
            </div>
            <div className="d-flex justify-content-between mb-1 text-muted small">
              <span>Tax (5%):</span>
              <span>${orderSummary.tax.toFixed(2)}</span>
            </div>
            <div className="d-flex justify-content-between mb-1 text-muted small">
              <span>Shipping:</span>
              <span>${orderSummary.shipping.toFixed(2)}</span>
            </div>
            <div className="d-flex justify-content-between fw-bold fs-5 text-dark mt-2 border-top pt-2">
              <span>Grand Total:</span>
              <span className="text-accent" style={{ color: 'var(--color-accent)' }}>
                ${orderSummary.grand_total.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="mb-4">
            <small className="text-muted d-block">Shipping Address:</small>
            <strong className="text-dark">{orderSummary.shipping_address}</strong>
          </div>

          <div className="d-flex gap-3">
            <Link to="/orders" className="btn btn-accent flex-grow-1 py-2 rounded-pill">
              View All Orders
            </Link>
            <Link to="/books" className="btn btn-outline-secondary flex-grow-1 py-2 rounded-pill">
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const items = cart?.items || [];
  const isCartEmpty = items.length === 0;

  return (
    <div className="container py-4">
      {/* Title */}
      <h1 className="fw-bold mb-4 pb-2 border-bottom" style={{ fontFamily: 'var(--font-heading)' }}>
        <i className="bi bi-credit-card me-2 text-primary"></i> Checkout
      </h1>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-danger d-flex align-items-center mb-4" role="alert">
          <i className="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
          <div>{error}</div>
        </div>
      )}

      {isCartEmpty ? (
        <div className="text-center py-5">
          <p className="lead text-muted mb-4">Your cart has no items to check out.</p>
          <Link to="/books" className="btn btn-accent rounded-pill px-4">
            Return to Book Catalog
          </Link>
        </div>
      ) : (
        <div className="row g-4">
          {/* Shipping & Payment Form */}
          <div className="col-lg-7">
            <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
              <h4 className="fw-bold mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                1. Shipping Information
              </h4>

              <form onSubmit={handleCheckoutSubmit}>
                <div className="mb-4">
                  <label htmlFor="shippingAddress" className="form-label fw-semibold">
                    Full Shipping Address <span className="text-danger">*</span>
                  </label>
                  <textarea
                    id="shippingAddress"
                    className="form-control"
                    rows="3"
                    placeholder="Enter street address, city, state, zip code..."
                    value={shippingAddress}
                    onChange={(e) => setShippingAddress(e.target.value)}
                    required
                  />
                  <small className="text-muted mt-1 d-block">
                    Must be at least 5 characters long.
                  </small>
                </div>

                <h4 className="fw-bold mb-3 border-top pt-4" style={{ fontFamily: 'var(--font-heading)' }}>
                  2. Select Payment Method
                </h4>

                <div className="row g-3 mb-4">
                  <div className="col-sm-6">
                    <div
                      className={`border rounded-3 p-3 h-100 ${paymentMethod === 'card' ? 'border-2 bg-light' : ''}`}
                      style={paymentMethod === 'card' ? { borderColor: 'var(--color-accent)' } : undefined}
                      role="button"
                      onClick={() => setPaymentMethod('card')}
                    >
                      <div className="form-check">
                        <input
                          className="form-check-input ms-0 me-2"
                          type="radio"
                          name="paymentMethod"
                          id="paymentCard"
                          value="card"
                          checked={paymentMethod === 'card'}
                          onChange={(e) => setPaymentMethod(e.target.value)}
                        />
                        <label className="form-check-label fw-semibold" htmlFor="paymentCard">
                          <i className="bi bi-credit-card-2-front me-2 text-primary"></i> Pay by Card
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="col-sm-6">
                    <div
                      className={`border rounded-3 p-3 h-100 ${paymentMethod === 'cod' ? 'border-2 bg-light' : ''}`}
                      style={paymentMethod === 'cod' ? { borderColor: 'var(--color-accent)' } : undefined}
                      role="button"
                      onClick={() => setPaymentMethod('cod')}
                    >
                      <div className="form-check">
                        <input
                          className="form-check-input ms-0 me-2"
                          type="radio"
                          name="paymentMethod"
                          id="paymentCod"
                          value="cod"
                          checked={paymentMethod === 'cod'}
                          onChange={(e) => setPaymentMethod(e.target.value)}
                        />
                        <label className="form-check-label fw-semibold" htmlFor="paymentCod">
                          <i className="bi bi-cash-coin me-2 text-primary"></i> Cash on Delivery
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                {paymentMethod === 'card' && (
                  <div className="border rounded-4 p-4 mb-4 bg-white">
                    <div className="d-flex gap-2 mb-4">
                      <i className="bi bi-credit-card-fill fs-3 text-danger"></i>
                      <i className="bi bi-credit-card-2-front-fill fs-3 text-primary"></i>
                    </div>

                    <div className="mb-3">
                      <label htmlFor="cardNumber" className="form-label fw-semibold">
                        <span className="text-danger">*</span> Card number
                      </label>
                      <input
                        id="cardNumber"
                        type="text"
                        className="form-control py-2"
                        placeholder="Card number"
                        value={cardNumber}
                        onChange={(e) => setCardNumber(e.target.value)}
                        maxLength={19}
                        required
                      />
                    </div>

                    <div className="mb-3">
                      <label htmlFor="nameOnCard" className="form-label fw-semibold">
                        <span className="text-danger">*</span> Name on card
                      </label>
                      <input
                        id="nameOnCard"
                        type="text"
                        className="form-control py-2"
                        placeholder="Name on card"
                        value={nameOnCard}
                        onChange={(e) => setNameOnCard(e.target.value)}
                        required
                      />
                    </div>

                    <div className="row g-3 mb-3">
                      <div className="col-6">
                        <label htmlFor="expiryDate" className="form-label fw-semibold">
                          <span className="text-danger">*</span> Expiry date
                        </label>
                        <input
                          id="expiryDate"
                          type="text"
                          className="form-control py-2"
                          placeholder="MM/YY"
                          value={expiryDate}
                          onChange={(e) => setExpiryDate(e.target.value)}
                          maxLength={5}
                          required
                        />
                      </div>
                      <div className="col-6">
                        <label htmlFor="cvv" className="form-label fw-semibold">
                          <span className="text-danger">*</span> CVV{' '}
                          <i className="bi bi-info-circle text-info" title="3 or 4 digit security code on your card"></i>
                        </label>
                        <input
                          id="cvv"
                          type="password"
                          className="form-control py-2"
                          placeholder="CVV"
                          value={cvv}
                          onChange={(e) => setCvv(e.target.value)}
                          maxLength={4}
                          required
                        />
                      </div>
                    </div>

                    <div className="form-check mb-1">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id="saveCard"
                        checked={saveCard}
                        onChange={(e) => setSaveCard(e.target.checked)}
                      />
                      <label className="form-check-label fw-semibold" htmlFor="saveCard">
                        Save Card
                      </label>
                      <small className="text-muted d-block">
                        We will save this card for your convenience. If required, you can remove the card in the
                        "Payment Options" section in the "Account" menu.
                      </small>
                    </div>
                  </div>
                )}

                {paymentMethod === 'cod' && (
                  <div className="alert alert-secondary d-flex align-items-center mb-4" role="alert">
                    <i className="bi bi-info-circle fs-4 me-3"></i>
                    <div>
                      Pay in cash when your order is delivered. Please have the exact amount ready for the courier.
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  className="btn btn-accent w-100 py-3 rounded-pill fw-bold shadow-sm"
                  disabled={submitting}
                >
                  {submitting ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      {paymentMethod === 'card' ? 'Validating & Charging Card…' : 'Placing Order…'}
                    </>
                  ) : paymentMethod === 'card' ? (
                    <>
                      <i className="bi bi-shield-lock-fill me-2"></i> Pay Now (${parseFloat(cart?.estimated_total || 0).toFixed(2)})
                    </>
                  ) : (
                    <>
                      <i className="bi bi-cash-coin me-2"></i> Place Order (${parseFloat(cart?.estimated_total || 0).toFixed(2)})
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Checkout Order Summary */}
          <div className="col-lg-5">
            <div className="card border-0 shadow-sm rounded-4 p-4 bg-white">
              <h4 className="fw-bold mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                Order Summary ({items.length} {items.length === 1 ? 'item' : 'items'})
              </h4>

              <div className="mb-3 max-h-60 overflow-auto">
                {items.map((item) => (
                  <div key={item.id} className="d-flex justify-content-between align-items-center py-2 border-bottom">
                    <div>
                      <span className="fw-semibold text-dark d-block text-truncate" style={{ maxWidth: '200px' }}>
                        {item.book_title}
                      </span>
                      <small className="text-muted">Qty: {item.quantity} × ${parseFloat(item.price_at_add_time).toFixed(2)}</small>
                    </div>
                    <span className="fw-bold">${parseFloat(item.subtotal).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Subtotal</span>
                <span className="fw-semibold">${parseFloat(cart?.subtotal || 0).toFixed(2)}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Discount</span>
                <span className="fw-semibold text-success">-${parseFloat(cart?.discount || 0).toFixed(2)}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Tax (5%)</span>
                <span className="fw-semibold">${parseFloat(cart?.tax || 0).toFixed(2)}</span>
              </div>
              <div className="d-flex justify-content-between mb-3">
                <span className="text-muted">Shipping</span>
                <span className="fw-semibold">${parseFloat(cart?.shipping || 0).toFixed(2)}</span>
              </div>

              <hr />

              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="fw-bold fs-5">Grand Total</span>
                <span className="fw-bold fs-4 text-accent" style={{ color: 'var(--color-accent)' }}>
                  ${parseFloat(cart?.estimated_total || 0).toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Checkout;