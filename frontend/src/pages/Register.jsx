import React, { useContext, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { extractErrorMessage, extractFieldErrors } from '../utils/errorUtils';

const Register = () => {
  const { register: registerUser, isAuthenticated } = useContext(AuthContext);
  const navigate = useNavigate();
  const [serverError, setServerError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    setError,
    watch,
    formState: { errors },
  } = useForm({ mode: 'onBlur' });

  const passwordValue = watch('password', '');

  // If already authenticated, redirect to home
  if (isAuthenticated) {
    navigate('/', { replace: true });
    return null;
  }

  // Password strength indicators
  const passwordChecks = {
    length: passwordValue.length >= 8,
    uppercase: /[A-Z]/.test(passwordValue),
    lowercase: /[a-z]/.test(passwordValue),
    digit: /[0-9]/.test(passwordValue),
  };
  const passwordStrength = Object.values(passwordChecks).filter(Boolean).length;

  const getStrengthColor = () => {
    if (passwordStrength <= 1) return '#ef4444';
    if (passwordStrength === 2) return '#f59e0b';
    if (passwordStrength === 3) return '#3b82f6';
    return '#22c55e';
  };

  const getStrengthLabel = () => {
    if (!passwordValue) return '';
    if (passwordStrength <= 1) return 'Weak';
    if (passwordStrength === 2) return 'Fair';
    if (passwordStrength === 3) return 'Good';
    return 'Strong';
  };

  const onSubmit = async (data) => {
    setServerError('');
    setSubmitting(true);
    try {
      await registerUser(data.email, data.full_name, data.password);
      // Redirect to login with success message
      navigate('/login', {
        state: { message: 'Account created successfully! Please sign in.' },
        replace: true,
      });
    } catch (error) {
      // Try to map server-side field-level errors to form fields
      const fieldErrors = extractFieldErrors(error);
      if (Object.keys(fieldErrors).length > 0) {
        Object.entries(fieldErrors).forEach(([field, message]) => {
          setError(field, { type: 'server', message });
        });
      } else {
        setServerError(extractErrorMessage(error, 'Registration failed. Please try again.'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-7 col-lg-5">
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
              <i className="bi bi-person-plus-fill fs-1 mb-2 d-block" style={{ color: 'var(--color-accent)' }}></i>
              <h2 className="mb-1 fw-bold" style={{ fontFamily: 'var(--font-heading)', color: '#ffffff' }}>
                Create Account
              </h2>
              <p className="mb-0 small" style={{ color: '#94a3b8' }}>
                Join BookHaven and start exploring
              </p>
            </div>

            {/* Card Body */}
            <div className="card-body p-4">
              {/* Server error */}
              {serverError && (
                <div className="alert alert-danger d-flex align-items-center py-2" role="alert">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  <span>{serverError}</span>
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} noValidate>
                {/* Full Name */}
                <div className="mb-3">
                  <label htmlFor="register-name" className="form-label fw-semibold">
                    Full Name
                  </label>
                  <div className="input-group">
                    <span className="input-group-text bg-light border-end-0">
                      <i className="bi bi-person"></i>
                    </span>
                    <input
                      id="register-name"
                      type="text"
                      className={`form-control border-start-0 ${errors.full_name ? 'is-invalid' : ''}`}
                      placeholder="John Doe"
                      autoComplete="name"
                      {...register('full_name', {
                        required: 'Full name is required.',
                        minLength: { value: 2, message: 'Name must be at least 2 characters.' },
                        maxLength: { value: 100, message: 'Name must be under 100 characters.' },
                      })}
                    />
                    {errors.full_name && <div className="invalid-feedback">{errors.full_name.message}</div>}
                  </div>
                </div>

                {/* Email */}
                <div className="mb-3">
                  <label htmlFor="register-email" className="form-label fw-semibold">
                    Email Address
                  </label>
                  <div className="input-group">
                    <span className="input-group-text bg-light border-end-0">
                      <i className="bi bi-envelope"></i>
                    </span>
                    <input
                      id="register-email"
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
                  <label htmlFor="register-password" className="form-label fw-semibold">
                    Password
                  </label>
                  <div className="input-group">
                    <span className="input-group-text bg-light border-end-0">
                      <i className="bi bi-lock"></i>
                    </span>
                    <input
                      id="register-password"
                      type={showPassword ? 'text' : 'password'}
                      className={`form-control border-start-0 border-end-0 ${errors.password ? 'is-invalid' : ''}`}
                      placeholder="Minimum 8 characters"
                      autoComplete="new-password"
                      {...register('password', {
                        required: 'Password is required.',
                        minLength: { value: 8, message: 'Password must be at least 8 characters.' },
                        validate: {
                          hasUppercase: (v) => /[A-Z]/.test(v) || 'Must contain at least one uppercase letter.',
                          hasLowercase: (v) => /[a-z]/.test(v) || 'Must contain at least one lowercase letter.',
                          hasDigit: (v) => /[0-9]/.test(v) || 'Must contain at least one digit.',
                        },
                      })}
                    />
                    <span
                      className="input-group-text bg-light border-start-0"
                      role="button"
                      tabIndex={0}
                      onClick={() => setShowPassword((prev) => !prev)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') setShowPassword((prev) => !prev);
                      }}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      style={{ cursor: 'pointer' }}
                    >
                      <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                    </span>
                    {errors.password && <div className="invalid-feedback">{errors.password.message}</div>}
                  </div>

                  {/* Password Strength Meter */}
                  {passwordValue && (
                    <div className="mt-2">
                      <div
                        className="progress"
                        style={{ height: '4px', borderRadius: '2px', backgroundColor: '#e2e8f0' }}
                      >
                        <div
                          className="progress-bar"
                          role="progressbar"
                          style={{
                            width: `${(passwordStrength / 4) * 100}%`,
                            backgroundColor: getStrengthColor(),
                            transition: 'width 0.3s ease, background-color 0.3s ease',
                          }}
                        ></div>
                      </div>
                      <small style={{ color: getStrengthColor() }} className="fw-semibold">
                        {getStrengthLabel()}
                      </small>
                      <div className="mt-1">
                        {[
                          { key: 'length', label: '8+ characters' },
                          { key: 'uppercase', label: 'Uppercase letter' },
                          { key: 'lowercase', label: 'Lowercase letter' },
                          { key: 'digit', label: 'Number' },
                        ].map(({ key, label }) => (
                          <small
                            key={key}
                            className="d-block"
                            style={{ color: passwordChecks[key] ? '#22c55e' : '#94a3b8' }}
                          >
                            <i className={`bi ${passwordChecks[key] ? 'bi-check-circle-fill' : 'bi-circle'} me-1`}></i>
                            {label}
                          </small>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Confirm Password */}
                <div className="mb-4">
                  <label htmlFor="register-confirm-password" className="form-label fw-semibold">
                    Confirm Password
                  </label>
                  <div className="input-group">
                    <span className="input-group-text bg-light border-end-0">
                      <i className="bi bi-lock-fill"></i>
                    </span>
                    <input
                      id="register-confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      className={`form-control border-start-0 border-end-0 ${errors.confirmPassword ? 'is-invalid' : ''}`}
                      placeholder="Re-enter your password"
                      autoComplete="new-password"
                      {...register('confirmPassword', {
                        required: 'Please confirm your password.',
                        validate: (value) => value === passwordValue || 'Passwords do not match.',
                      })}
                    />
                    <span
                      className="input-group-text bg-light border-start-0"
                      role="button"
                      tabIndex={0}
                      onClick={() => setShowConfirmPassword((prev) => !prev)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') setShowConfirmPassword((prev) => !prev);
                      }}
                      aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      style={{ cursor: 'pointer' }}
                    >
                      <i className={`bi ${showConfirmPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                    </span>
                    {errors.confirmPassword && (
                      <div className="invalid-feedback">{errors.confirmPassword.message}</div>
                    )}
                  </div>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  className="btn btn-accent w-100 py-2"
                  disabled={submitting}
                >
                  {submitting ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Creating Account…
                    </>
                  ) : (
                    <>
                      <i className="bi bi-person-plus me-2"></i>
                      Create Account
                    </>
                  )}
                </button>
              </form>

              {/* Login link */}
              <div className="text-center mt-4 pt-3" style={{ borderTop: '1px solid var(--border-light)' }}>
                <span className="text-muted">Already have an account?</span>{' '}
                <Link to="/login" className="fw-semibold text-decoration-none" style={{ color: 'var(--color-accent)' }}>
                  Sign in
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;