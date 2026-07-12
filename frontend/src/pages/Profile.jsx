import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { UserContext } from '../context/UserContext';
import { AuthContext } from '../context/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const Profile = () => {
  const { user, loading } = useContext(UserContext);
  const { logout } = useContext(AuthContext);

  if (loading || !user) {
    return <LoadingSpinner message="Loading profile..." />;
  }

  const memberSince = new Date(user.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const roleBadge =
    user.role === 'admin' ? (
      <span className="badge rounded-pill" style={{ backgroundColor: 'var(--color-brand)', fontSize: '0.8rem' }}>
        <i className="bi bi-shield-fill-check me-1"></i>Admin
      </span>
    ) : (
      <span className="badge rounded-pill bg-secondary" style={{ fontSize: '0.8rem' }}>
        <i className="bi bi-person-fill me-1"></i>Customer
      </span>
    );

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          {/* Header */}
          <div className="d-flex align-items-center justify-content-between mb-4">
            <h1 className="mb-0" style={{ fontFamily: 'var(--font-heading)' }}>
              My Profile
            </h1>
            {roleBadge}
          </div>

          {/* Profile Card */}
          <div
            className="card border-0 shadow-lg mb-4"
            style={{ borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}
          >
            {/* Card Header with gradient */}
            <div
              className="py-4 px-4"
              style={{
                background: 'linear-gradient(135deg, #0f172a, #1e293b)',
              }}
            >
              <div className="d-flex align-items-center">
                {/* Avatar */}
                <div
                  className="d-flex align-items-center justify-content-center rounded-circle flex-shrink-0"
                  style={{
                    width: '72px',
                    height: '72px',
                    background: 'linear-gradient(135deg, var(--color-accent), #f59e0b)',
                    fontSize: '1.8rem',
                    fontWeight: 700,
                    color: '#fff',
                    fontFamily: 'var(--font-heading)',
                  }}
                >
                  {user.full_name?.charAt(0).toUpperCase()}
                </div>
                <div className="ms-3">
                  <h3 className="mb-0 fw-bold" style={{ color: '#ffffff' }}>
                    {user.full_name}
                  </h3>
                  <p className="mb-0 small" style={{ color: '#94a3b8' }}>
                    {user.email}
                  </p>
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="card-body p-4">
              <div className="row g-4">
                <div className="col-sm-6">
                  <div className="d-flex align-items-center">
                    <div
                      className="d-flex align-items-center justify-content-center rounded flex-shrink-0"
                      style={{
                        width: '42px',
                        height: '42px',
                        backgroundColor: 'var(--color-accent-light)',
                        color: 'var(--color-accent)',
                      }}
                    >
                      <i className="bi bi-envelope-fill"></i>
                    </div>
                    <div className="ms-3">
                      <small className="text-muted d-block">Email</small>
                      <span className="fw-semibold">{user.email}</span>
                    </div>
                  </div>
                </div>

                <div className="col-sm-6">
                  <div className="d-flex align-items-center">
                    <div
                      className="d-flex align-items-center justify-content-center rounded flex-shrink-0"
                      style={{
                        width: '42px',
                        height: '42px',
                        backgroundColor: '#ede9fe',
                        color: '#7c3aed',
                      }}
                    >
                      <i className="bi bi-calendar-event-fill"></i>
                    </div>
                    <div className="ms-3">
                      <small className="text-muted d-block">Member Since</small>
                      <span className="fw-semibold">{memberSince}</span>
                    </div>
                  </div>
                </div>

                <div className="col-sm-6">
                  <div className="d-flex align-items-center">
                    <div
                      className="d-flex align-items-center justify-content-center rounded flex-shrink-0"
                      style={{
                        width: '42px',
                        height: '42px',
                        backgroundColor: user.is_active ? '#dcfce7' : '#fee2e2',
                        color: user.is_active ? '#16a34a' : '#dc2626',
                      }}
                    >
                      <i className={`bi ${user.is_active ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}`}></i>
                    </div>
                    <div className="ms-3">
                      <small className="text-muted d-block">Account Status</small>
                      <span className="fw-semibold">{user.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                  </div>
                </div>

                
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="row g-3">
            <div className="col-sm-4">
              <Link
                to="/orders"
                className="card border-0 shadow-sm text-decoration-none h-100"
                style={{
                  borderRadius: 'var(--radius-md)',
                  transition: 'var(--transition-fast)',
                  color: 'var(--text-main)',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-3px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
              >
                <div className="card-body text-center py-4">
                  <i className="bi bi-bag-check fs-2 mb-2 d-block" style={{ color: 'var(--color-accent)' }}></i>
                  <h6 className="fw-semibold mb-0">My Orders</h6>
                </div>
              </Link>
            </div>

            <div className="col-sm-4">
              <Link
                to="/cart"
                className="card border-0 shadow-sm text-decoration-none h-100"
                style={{
                  borderRadius: 'var(--radius-md)',
                  transition: 'var(--transition-fast)',
                  color: 'var(--text-main)',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-3px)')}
                onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
              >
                <div className="card-body text-center py-4">
                  <i className="bi bi-cart3 fs-2 mb-2 d-block" style={{ color: 'var(--color-brand)' }}></i>
                  <h6 className="fw-semibold mb-0">Shopping Cart</h6>
                </div>
              </Link>
            </div>

           
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
