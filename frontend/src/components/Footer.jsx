import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="footer-custom mt-auto">
      <div className="container">
        <div className="row g-4 mb-4">
          {/* About */}
          <div className="col-lg-4 col-md-6">
            <h5 className="navbar-brand text-white mb-3">
              <i className="bi bi-book-half"></i> BookHaven
            </h5>
            <p className="small text-muted mb-3">
              Your premier online sanctuary for timeless literature, contemporary bestsellers, fine stationery, and curated deals.
            </p>
            <div className="d-flex">
              <a href="#" className="social-icon" aria-label="Facebook"><i class="bi bi-facebook"></i></a>
              <a href="#" class="social-icon" aria-label="Twitter"><i class="bi bi-twitter-x"></i></a>
              <a href="#" class="social-icon" aria-label="Instagram"><i class="bi bi-instagram"></i></a>
              <a href="#" class="social-icon" aria-label="Goodreads"><i class="bi bi-book"></i></a>
            </div>
          </div>

          {/* Quick Links */}
          <div className="col-lg-2 col-md-6">
            <h5 className="footer-title">Explore</h5>
            <ul className="footer-links">
              <li><Link to="/books">Browse Books</Link></li>
              <li><Link to="/genres">Genre Catalog</Link></li>
              <li><Link to="/stationery">Stationery</Link></li>
              <li><Link to="/deals">Active Deals</Link></li>
            </ul>
          </div>

          {/* Support */}
          <div className="col-lg-3 col-md-6">
            <h5 className="footer-title">Support</h5>
            <ul className="footer-links">
              <li><a href="#">Help Center</a></li>
              <li><a href="#">Shipping & Returns</a></li>
              <li><a href="#">Track Order</a></li>
              <li><a href="#">Privacy Policy</a></li>
            </ul>
          </div>

          {/* Newsletter */}
          <div className="col-lg-3 col-md-6">
            <h5 className="footer-title">Stay Connected</h5>
            <p className="small text-muted mb-3">Subscribe to receive exclusive book recommendations & special offers.</p>
            <form className="d-flex gap-2" onSubmit={(e) => { e.preventDefault(); alert('Thank you for subscribing!'); }}>
              <input type="email" className="form-control form-control-sm rounded-pill" placeholder="Enter your email" required />
              <button type="submit" className="btn btn-accent btn-sm rounded-pill px-3">Join</button>
            </form>
          </div>
        </div>

        <hr className="border-secondary my-4" />

        <div className="d-md-flex justify-content-between align-items-center text-center small text-muted">
          <p className="mb-0">&copy; 2026 BookHaven Inc. All rights reserved.</p>
          <p class="mb-0 mt-2 mt-md-0">Crafted with passion for book lovers worldwide.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
