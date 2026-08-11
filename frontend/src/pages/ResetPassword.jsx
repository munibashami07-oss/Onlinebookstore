import React, { useContext, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { extractErrorMessage } from '../utils/errorUtils';

const ResetPassword = () => {
  const { resetPassword } = useContext(AuthContext);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [serverError, setServerError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({ mode: 'onBlur' });

  const password = watch('password');

  const onSubmit = async (data) => {
    setServerError('');
    setSubmitting(true);
    try {
      await resetPassword(token, data.password);
      setDone(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (error) {
      setServerError(
        extractErrorMessage(error, 'This reset link is invalid or has expired. Please request a new one.')
      );
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
              <i className="bi bi-shield-lock fs-1 mb-2 d-block" style={{ color: 'var(--color-accent)' }}></i>
              <h2 className="mb-1 fw-bold" style={{ fontFamily: 'var(--font-heading)', color: '#ffffff' }}>
                Reset Password
              </h2>
              <p className="mb-0 small" style={{ color: '#94a3b8' }}>
                Choose a new password for your account
              </p>
            </div>

            {/* Card Body */}
            <div className="card-body p-4">
              {!token && (
                <div className="alert alert-danger d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  <span>
                    This link is missing its reset token. Please use the link from your email, or{' '}
                    <Link to="/forgot-password">request a new one</Link>.
                  </span>
                </div>
              )}

              {serverError && (
                <div className="alert alert-danger d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  <span>{serverError}</span>
                </div>
              )}

              {done ? (
                <div className="alert alert-success d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-check-circle-fill me-2"></i>
                  <span>Your password has been reset. Redirecting to sign in…</span>
                </div>
              ) : (
                <form onSubmit={handleSubmit(onSubmit)} noValidate>
                  <div className="mb-3">
                    <label htmlFor="new-password" className="form-label fw-semibold">
                      New Password
                    </label>
                    <div className="input-group">
                      <span className="input-group-text bg-light border-end-0">
                        <i className="bi bi-lock"></i>
                      </span>
                      <input
                        id="new-password"
                        type="password"
                        className={`form-control border-start-0 ${errors.password ? 'is-invalid' : ''}`}
                        placeholder="Enter new password"
                        autoComplete="new-password"
                        {...register('password', {
                          required: 'Password is required.',
                          minLength: {
                            value: 8,
                            message: 'Password must be at least 8 characters.',
                          },
                        })}
                      />
                      {errors.password && <div className="invalid-feedback">{errors.password.message}</div>}
                    </div>
                  </div>

                  <div className="mb-3">
                    <label htmlFor="confirm-password" className="form-label fw-semibold">
                      Confirm Password
                    </label>
                    <div className="input-group">
                      <span className="input-group-text bg-light border-end-0">
                        <i className="bi bi-lock-fill"></i>
                      </span>
                      <input
                        id="confirm-password"
                        type="password"
                        className={`form-control border-start-0 ${errors.confirmPassword ? 'is-invalid' : ''}`}
                        placeholder="Re-enter new password"
                        autoComplete="new-password"
                        {...register('confirmPassword', {
                          required: 'Please confirm your password.',
                          validate: (value) => value === password || 'Passwords do not match.',
                        })}
                      />
                      {errors.confirmPassword && (
                        <div className="invalid-feedback">{errors.confirmPassword.message}</div>
                      )}
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="btn btn-accent w-100 py-2 mt-2"
                    disabled={submitting || !token}
                  >
                    {submitting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Resetting…
                      </>
                    ) : (
                      <>
                        <i className="bi bi-check2-circle me-2"></i>
                        Reset Password
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

export default ResetPassword;