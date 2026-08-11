import React, { useContext, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { extractErrorMessage } from '../utils/errorUtils';

const ForgotPassword = () => {
  const { forgotPassword } = useContext(AuthContext);
  const [serverError, setServerError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ mode: 'onBlur' });

  const onSubmit = async (data) => {
    setServerError('');
    setSubmitting(true);
    try {
      await forgotPassword(data.email);
      // Always show success, regardless of whether the email exists,
      // so the form can't be used to enumerate registered accounts.
      setSent(true);
    } catch (error) {
      setServerError(extractErrorMessage(error, 'Something went wrong. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div
            className="card border-0 shadow-lg"
            style={{
              borderRadius: 'var(--radius-lg)',
              overflow: 'hidden',
            }}
          >
            {/* Card Header */}
            <div
              className="text-center py-4"
              style={{
                background: 'linear-gradient(135deg, #0f172a, #1e293b)',
                color: '#ffffff',
              }}
            >
              <i className="bi bi-key fs-1 mb-2 d-block" style={{ color: 'var(--color-accent)' }}></i>
              <h2 className="mb-1 fw-bold" style={{ fontFamily: 'var(--font-heading)', color: '#ffffff' }}>
                Forgot Password
              </h2>
              <p className="mb-0 small" style={{ color: '#94a3b8' }}>
                We&apos;ll email you a link to reset it
              </p>
            </div>

            {/* Card Body */}
            <div className="card-body p-4">
              {serverError && (
                <div className="alert alert-danger d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  <span>{serverError}</span>
                </div>
              )}

              {sent ? (
                <div className="alert alert-success d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-check-circle-fill me-2"></i>
                  <span>
                    If an account exists for that email, a reset link is on its way. Check your inbox
                    (and spam folder).
                  </span>
                </div>
              ) : (
                <form onSubmit={handleSubmit(onSubmit)} noValidate>
                  <div className="mb-3">
                    <label htmlFor="forgot-email" className="form-label fw-semibold">
                      Email Address
                    </label>
                    <div className="input-group">
                      <span className="input-group-text bg-light border-end-0">
                        <i className="bi bi-envelope"></i>
                      </span>
                      <input
                        id="forgot-email"
                        type="email"
                        className={`form-control border-start-0 ${errors.email ? 'is-invalid' : ''}`}
                        placeholder="you@example.com"
                        autoComplete="email"
                        {...register('email', {
                          required: 'Email is required.',
                          pattern: {
                            value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                            message: 'Enter a valid email address.',
                          },
                        })}
                      />
                      {errors.email && <div className="invalid-feedback">{errors.email.message}</div>}
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="btn btn-accent w-100 py-2 mt-2"
                    disabled={submitting}
                  >
                    {submitting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Sending link…
                      </>
                    ) : (
                      <>
                        <i className="bi bi-send me-2"></i>
                        Send Reset Link
                      </>
                    )}
                  </button>
                </form>
              )}

              <div className="text-center mt-4 pt-3" style={{ borderTop: '1px solid var(--border-light)' }}>
                <Link to="/login" className="fw-semibold text-decoration-none" style={{ color: 'var(--color-accent)' }}>
                  <i className="bi bi-arrow-left me-1"></i>
                  Back to Sign In
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;