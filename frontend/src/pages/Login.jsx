import React, { useContext, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { extractErrorMessage } from '../utils/errorUtils';

const Login = () => {
  const { login, isAuthenticated } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  const [serverError, setServerError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Where to redirect after successful login
  const from = location.state?.from?.pathname || '/';

  // Registration success message passed via router state
  const successMessage = location.state?.message || '';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({ mode: 'onBlur' });

  // If already authenticated, redirect immediately
  if (isAuthenticated) {
    navigate(from, { replace: true });
    return null;
  }

  const onSubmit = async (data) => {
    setServerError('');
    setSubmitting(true);
    try {
      await login(data.email, data.password);
      navigate(from, { replace: true });
    } catch (error) {
      setServerError(extractErrorMessage(error, 'Invalid email or password.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          {/* Card */}
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
              <i className="bi bi-book-half fs-1 mb-2 d-block" style={{ color: 'var(--color-accent)' }}></i>
              <h2 className="mb-1 fw-bold" style={{ fontFamily: 'var(--font-heading)', color: '#ffffff' }}>
                Welcome Back
              </h2>
              <p className="mb-0 small" style={{ color: '#94a3b8' }}>
                Sign in to your BookHaven account
              </p>
            </div>

            {/* Card Body */}
            <div className="card-body p-4">
              {/* Registration success flash */}
              {successMessage && (
                <div className="alert alert-success d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-check-circle-fill me-2"></i>
                  <span>{successMessage}</span>
                </div>
              )}

              {/* Server error */}
              {serverError && (
                <div className="alert alert-danger d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  <span>{serverError}</span>
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} noValidate>
                {/* Email */}
                <div className="mb-3">
                  <label htmlFor="login-email" className="form-label fw-semibold">
                    Email Address
                  </label>
                  <div className="input-group">
                    <span className="input-group-text bg-light border-end-0">
                      <i className="bi bi-envelope"></i>
                    </span>
                    <input
                      id="login-email"
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

                {/* Password */}
                <div className="mb-3">
                  <div className="d-flex justify-content-between align-items-center">
                    <label htmlFor="login-password" className="form-label fw-semibold mb-0">
                      Password
                    </label>
                    <Link
                      to="/forgot-password"
                      className="small fw-semibold text-decoration-none"
                      style={{ color: 'var(--color-accent)' }}
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <div className="input-group mt-1">
                    <span className="input-group-text bg-light border-end-0">
                      <i className="bi bi-lock"></i>
                    </span>
                    <input
                      id="login-password"
                      type="password"
                      className={`form-control border-start-0 ${errors.password ? 'is-invalid' : ''}`}
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      {...register('password', {
                        required: 'Password is required.',
                      })}
                    />
                    {errors.password && <div className="invalid-feedback">{errors.password.message}</div>}
                  </div>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  className="btn btn-accent w-100 py-2 mt-2"
                  disabled={submitting}
                >
                  {submitting ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Signing in…
                    </>
                  ) : (
                    <>
                      <i className="bi bi-box-arrow-in-right me-2"></i>
                      Sign In
                    </>
                  )}
                </button>
              </form>

              {/* Register link */}
              <div className="text-center mt-4 pt-3" style={{ borderTop: '1px solid var(--border-light)' }}>
                <span className="text-muted">Don&apos;t have an account?</span>{' '}
                <Link to="/register" className="fw-semibold text-decoration-none" style={{ color: 'var(--color-accent)' }}>
                  Create one now
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;