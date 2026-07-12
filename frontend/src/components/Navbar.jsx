import React, { useContext, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';

const Navbar = () => {
  const { isAuthenticated, logout } = useContext(AuthContext);
  const { user } = useContext(UserContext);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/books?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogoutClick = () => {
    logout();
    navigate('/login');
  };

  const isAdmin = user?.role === 'admin' || user?.is_superuser === true;

  return (
    <nav className="navbar navbar-expand-lg navbar-custom sticky-top">
      <div className="container">
        {/* Brand */}
        <Link className="navbar-brand" to="/">
          <i className="bi bi-book-half"></i> BookHaven
        </Link>

        {/* Mobile Toggle */}
        <button
          className="navbar-toggler border-0"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarContent"
          aria-controls="navbarContent"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        {/* Navbar Collapse Content */}
        <div className="collapse navbar-collapse" id="navbarContent">
          {/* Search Form */}
          <form className="search-form mx-auto my-2 my-lg-0" onSubmit={handleSearchSubmit}>
            <i className="bi bi-search search-icon"></i>
            <input
              className="form-control search-input"
              type="search"
              placeholder="Search title, author, or ISBN..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search"
            />
          </form>

          {/* Links and Actions */}
          <ul className="navbar-nav ms-auto mb-2 mb-lg-0 align-items-center gap-1">
            <li className="nav-item">
              <NavLink className="nav-link" to="/">Home</NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" to="/books">Books</NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" to="/genres">Genres</NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" to="/stationery">Stationery</NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" to="/deals">Deals</NavLink>
            </li>


            {/* Auth / Cart Indicator */}
            {isAuthenticated ? (
              <>
                {/* Cart link */}
                <li className="nav-item me-2">
                  <Link className="nav-link position-relative" to="/cart" title="Shopping Cart">
                    <i className="bi bi-cart3 fs-5"></i>
                  </Link>
                </li>

                {/* User Dropdown */}
                <li className="nav-item dropdown">
                  <button
                    className="btn btn-outline-dark-custom dropdown-toggle px-3 py-1.5"
                    type="button"
                    id="userDropdown"
                    data-bs-toggle="dropdown"
                    aria-expanded="false"
                  >
                    <i className="bi bi-user me-1"></i> {user?.full_name || 'My Account'}
                  </button>
                  <ul className="dropdown-menu dropdown-menu-end shadow-sm" aria-labelledby="userDropdown">
                    <li>
                      <Link className="dropdown-item" to="/profile">
                        <i className="bi bi-person me-2"></i> Profile
                      </Link>
                    </li>
                    <li>
                      <Link className="dropdown-item" to="/orders">
                        <i className="bi bi-bag-check me-2"></i> Orders
                      </Link>
                    </li>
                    {isAdmin && (
                      <>
                        <li><hr className="dropdown-divider" /></li>
                        <li>
                          <Link className="dropdown-item fw-semibold text-primary" to="/admin">
                            <i className="bi bi-speedometer2 me-2"></i> Admin Panel
                          </Link>
                        </li>
                      </>
                    )}
                    <li><hr className="dropdown-divider" /></li>
                    <li>
                      <button className="dropdown-item text-danger" onClick={handleLogoutClick}>
                        <i className="bi bi-box-arrow-right me-2"></i> Logout
                      </button>
                    </li>
                  </ul>
                </li>
              </>
            ) : (
              <li className="nav-item ms-lg-2">
                <Link className="btn btn-accent px-4 py-2" to="/login">
                  Sign In
                </Link>
              </li>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;