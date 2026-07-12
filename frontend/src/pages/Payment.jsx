import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import paymentService from '../api/paymentService';
import LoadingSpinner from '../components/LoadingSpinner';
import { extractErrorMessage } from '../utils/errorUtils';

const Payment = () => {
  const { orderId: routeOrderId } = useParams();
  const navigate = useNavigate();

  // Retrieve order details from parameter or recent order summary
  const orderId = routeOrderId ? parseInt(routeOrderId, 10) : null;

  // Payment states: 'input' | 'pending' | 'success' | 'failed'
  const [step, setStep] = useState('input');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form State
  const [paymentMethod, setPaymentMethod] = useState('stripe');
  const [cardNumber, setCardNumber] = useState('4242424242424242'); // Demo card for test/demo
  const [expiryDate, setExpiryDate] = useState('12/28');
  const [cvv, setCvv] = useState('123');

  // Transaction State
  const [transactionData, setTransactionData] = useState(null);
  const [receiptData, setReceiptData] = useState(null);

  // If no orderId in route, check if an order summary exists in sessionStorage
  const [activeOrder, setActiveOrder] = useState(null);

  useEffect(() => {
    const orders = JSON.parse(sessionStorage.getItem('my_orders') || '[]');
    if (orderId) {
      const match = orders.find((o) => o.order_id === orderId);
      if (match) setActiveOrder(match);
    } else if (orders.length > 0) {
      setActiveOrder(orders[0]);
    }
  }, [orderId]);

  const targetOrderId = orderId || activeOrder?.order_id;
  const targetAmount = activeOrder?.grand_total || 0;

  // Basic client-side card validation (Luhn check + expiry + CVV format).
  // Backend re-validates independently; this just gives instant feedback.
  const validateCardInput = () => {
    if (paymentMethod === 'paypal') return null;

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

  // Step 1: Initialize Payment Transaction
  const handleInitiatePayment = async (e) => {
    e.preventDefault();
    if (!targetOrderId) {
      setError('No valid order found for payment.');
      return;
    }
    const validationError = validateCardInput();
    if (validationError) {
      setError(validationError);
      return;
    }
    setLoading(true);
    setError('');
    try {
      // Call POST /payments/create
      const pendingData = await paymentService.createPayment(
        targetOrderId,
        paymentMethod,
        cardNumber
      );
      setTransactionData(pendingData);
      setStep('pending');
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to initialize payment gateway.'));
      setStep('failed');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Confirm Payment Transaction
  const handleConfirmPayment = async () => {
    if (!transactionData?.transaction_id) return;
    setLoading(true);
    setError('');
    try {
      // Call POST /payments/confirm
      const receipt = await paymentService.confirmPayment(transactionData.transaction_id);
      setReceiptData(receipt);
      setStep('success');

      // Update session order status if present
      const orders = JSON.parse(sessionStorage.getItem('my_orders') || '[]');
      const updated = orders.map((o) =>
        o.order_id === targetOrderId ? { ...o, status: 'completed', payment_status: 'succeeded' } : o
      );
      sessionStorage.setItem('my_orders', JSON.stringify(updated));
    } catch (err) {
      setError(extractErrorMessage(err, 'Payment authorization failed.'));
      setStep('failed');
    } finally {
      setLoading(false);
    }
  };

  // Cancel Payment Transaction
  const handleCancelPayment = async () => {
    if (!transactionData?.transaction_id) {
      setStep('input');
      return;
    }
    setLoading(true);
    try {
      await paymentService.cancelPayment(transactionData.transaction_id);
    } catch {
      // Non-fatal
    } finally {
      setLoading(false);
      setTransactionData(null);
      setStep('input');
    }
  };

  if (loading) {
    return <LoadingSpinner message="Communicating with secure payment gateway..." />;
  }

  return (
    <div className="container py-5">
      <div className="max-w-2xl mx-auto">
        {/* Title Header */}
        <div className="text-center mb-4">
          <h1 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
            <i className="bi bi-shield-check text-success me-2"></i> Secure Payment Gateway
          </h1>
          <p className="text-muted">Encrypted end-to-end payment processing</p>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="alert alert-danger d-flex align-items-center mb-4" role="alert">
            <i className="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
            <div>{error}</div>
          </div>
        )}

        {/* STEP SUCCESS: Digital Receipt */}
        {step === 'success' && receiptData && (
          <div className="card border-0 shadow-lg rounded-4 overflow-hidden p-4 p-md-5 bg-white">
            <div className="text-center mb-4">
              <div className="rounded-circle bg-success text-white d-inline-flex p-3 mb-3">
                <i className="bi bi-check-lg display-4"></i>
              </div>
              <h2 className="fw-bold text-success mb-1">Payment Successful!</h2>
              <p className="text-muted">Digital receipt has been generated.</p>
            </div>

            <div className="bg-light p-4 rounded-4 mb-4">
              <h6 className="fw-bold mb-3 border-bottom pb-2">Transaction Receipt</h6>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Transaction ID:</span>
                <span className="fw-bold">{receiptData.transaction_id || receiptData.receipt_number}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Order ID:</span>
                <span className="fw-semibold">#{targetOrderId}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Payment Method:</span>
                <span className="fw-semibold text-uppercase">{receiptData.payment_method || paymentMethod}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Card (Last 4):</span>
                <span className="fw-semibold">•••• •••• •••• {receiptData.last4 || '4242'}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Payment Status:</span>
                <span className="badge bg-success">SUCCEEDED</span>
              </div>
              <hr />
              <div className="d-flex justify-content-between fw-bold fs-4 text-dark">
                <span>Amount Paid:</span>
                <span className="text-accent" style={{ color: 'var(--color-accent)' }}>
                  ${(receiptData.amount || targetAmount).toFixed(2)}
                </span>
              </div>
            </div>

            <div className="d-flex gap-3">
              <Link to="/orders" className="btn btn-accent flex-grow-1 py-3 rounded-pill fw-bold">
                View Orders & Receipts
              </Link>
              <Link to="/books" className="btn btn-outline-secondary flex-grow-1 py-3 rounded-pill">
                Continue Shopping
              </Link>
            </div>
          </div>
        )}

        {/* STEP PENDING: Confirm Transaction */}
        {step === 'pending' && transactionData && (
          <div className="card border-0 shadow-lg rounded-4 p-4 p-md-5 bg-white text-center">
            <div className="mb-4">
              <span className="badge bg-warning text-dark px-3 py-2 fs-6 rounded-pill mb-2">
                <i className="bi bi-clock-history me-1"></i> Transaction Pending Authorization
              </span>
              <h3 className="fw-bold">Transaction Reference</h3>
              <p className="text-muted font-monospace">{transactionData.transaction_id}</p>
            </div>

            <div className="bg-light p-4 rounded-3 text-start mb-4">
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Order ID:</span>
                <span className="fw-bold">#{targetOrderId}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Method:</span>
                <span className="fw-semibold text-uppercase">{transactionData.payment_method}</span>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Card Last 4:</span>
                <span className="fw-semibold">•••• {transactionData.last4}</span>
              </div>
              <div className="d-flex justify-content-between fw-bold fs-5 text-dark mt-2 border-top pt-2">
                <span>Total Charge:</span>
                <span className="text-accent">${(transactionData.amount || targetAmount).toFixed(2)}</span>
              </div>
            </div>

            <div className="d-flex gap-3">
              <button
                className="btn btn-success flex-grow-1 py-3 rounded-pill fw-bold shadow-sm"
                onClick={handleConfirmPayment}
              >
                <i className="bi bi-check-circle me-2"></i> Confirm & Pay Now
              </button>
              <button
                className="btn btn-outline-danger flex-grow-1 py-3 rounded-pill"
                onClick={handleCancelPayment}
              >
                Cancel Transaction
              </button>
            </div>
          </div>
        )}

        {/* STEP FAILED: Payment Error Handler */}
        {step === 'failed' && (
          <div className="card border-0 shadow-lg rounded-4 p-4 p-md-5 bg-white text-center">
            <div className="rounded-circle bg-danger bg-opacity-10 text-danger d-inline-flex p-3 mb-3">
              <i className="bi bi-x-circle-fill display-4"></i>
            </div>
            <h3 className="fw-bold text-danger mb-2">Payment Failed or Cancelled</h3>
            <p className="text-muted mb-4">
              We could not authorize your payment transaction. Please verify card details and retry.
            </p>

            <div className="d-flex gap-3">
              <button
                className="btn btn-accent flex-grow-1 py-2 rounded-pill"
                onClick={() => setStep('input')}
              >
                <i className="bi bi-arrow-counterclockwise me-2"></i> Retry Payment
              </button>
              <Link to="/orders" className="btn btn-outline-secondary flex-grow-1 py-2 rounded-pill">
                Back to Orders
              </Link>
            </div>
          </div>
        )}

        {/* STEP INPUT: Form Entry */}
        {step === 'input' && (
          <div className="card border-0 shadow-lg rounded-4 p-4 p-md-5 bg-white">
            <div className="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
              <div>
                <h4 className="fw-bold mb-0">Payment Details</h4>
                <small className="text-muted">Order #{targetOrderId || 'Pending'}</small>
              </div>
              <span className="fs-4 fw-bold text-accent" style={{ color: 'var(--color-accent)' }}>
                ${targetAmount > 0 ? targetAmount.toFixed(2) : '0.00'}
              </span>
            </div>

            <form onSubmit={handleInitiatePayment}>
              {/* Payment Method Selector */}
              <div className="mb-4">
                <label className="form-label small fw-semibold">Payment Gateway Provider</label>
                <div className="d-flex gap-3">
                  <div className="form-check border p-3 rounded-3 flex-grow-1 bg-light">
                    <input
                      className="form-check-input ms-0 me-2"
                      type="radio"
                      name="payMethod"
                      id="stripeOpt"
                      value="stripe"
                      checked={paymentMethod === 'stripe'}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                    />
                    <label className="form-check-label fw-semibold" htmlFor="stripeOpt">
                      <i className="bi bi-credit-card me-1 text-primary"></i> Stripe Credit Card
                    </label>
                  </div>
                  <div className="form-check border p-3 rounded-3 flex-grow-1 bg-light">
                    <input
                      className="form-check-input ms-0 me-2"
                      type="radio"
                      name="payMethod"
                      id="paypalOpt"
                      value="paypal"
                      checked={paymentMethod === 'paypal'}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                    />
                    <label className="form-check-label fw-semibold" htmlFor="paypalOpt">
                      <i className="bi bi-paypal me-1 text-primary"></i> PayPal Express
                    </label>
                  </div>
                </div>
              </div>

              {/* Card Inputs */}
              <div className="mb-3">
                <label className="form-label small fw-semibold">Card Number</label>
                <div className="input-group">
                  <span className="input-group-text bg-light border-end-0">
                    <i className="bi bi-credit-card-2-back"></i>
                  </span>
                  <input
                    type="text"
                    className="form-control border-start-0"
                    placeholder="4242 4242 4242 4242"
                    value={cardNumber}
                    onChange={(e) => setCardNumber(e.target.value)}
                    maxLength={19}
                    required
                  />
                </div>
                <small className="text-muted" style={{ fontSize: '0.75rem' }}>
                  Only last 4 digits are transmitted for tokenization (never stored).
                </small>
              </div>

              <div className="row g-3 mb-4">
                <div className="col-6">
                  <label className="form-label small fw-semibold">Expiry Date</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="MM/YY"
                    value={expiryDate}
                    onChange={(e) => setExpiryDate(e.target.value)}
                    required
                  />
                </div>
                <div className="col-6">
                  <label className="form-label small fw-semibold">CVV Security Code</label>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="123"
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value)}
                    maxLength={4}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-accent w-100 py-3 rounded-pill fw-bold shadow-sm"
              >
                <i className="bi bi-lock-fill me-2"></i> Process Payment (${targetAmount.toFixed(2)})
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default Payment;
