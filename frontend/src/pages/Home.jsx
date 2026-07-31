import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import bookService from '../api/bookService';
import genreService from '../api/genreService';
import BookCard from '../components/BookCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { extractErrorMessage } from '../utils/errorUtils';

const Home = () => {
  const [featuredBooks, setFeaturedBooks] = useState([]);
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAuthNotice, setShowAuthNotice] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();

  // If ProtectedRoute bounced a guest here, show a notice and clear the
  // redirect flag so it doesn't reappear on refresh or browser back/forward.
  useEffect(() => {
    if (location.state?.authRequired) {
      setShowAuthNotice(true);
      navigate(location.pathname, { replace: true, state: {} });
      const timer = setTimeout(() => setShowAuthNotice(false), 6000);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [booksData, genresData] = await Promise.all([
          bookService.listBooks({ page: 1, page_size: 8, sort_by: 'newest' }),
          genreService.listGenres(1, 6),
        ]);
        setFeaturedBooks(booksData);
        setGenres(genresData);
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to load store catalog home data.'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="home-page">
      {showAuthNotice && (
        <div
          className="alert shadow-lg d-flex align-items-start gap-3 border-0"
          role="alert"
          style={{
            position: 'fixed',
            top: '90px',
            right: '24px',
            zIndex: 2000,
            maxWidth: '360px',
            backgroundColor: '#fff7ed',
            borderLeft: '4px solid #f59e0b',
          }}
        >
          <i className="bi bi-shield-lock-fill text-warning fs-4"></i>
          <div className="flex-grow-1">
            <div className="fw-semibold small mb-1">Sign in required</div>
            <div className="text-muted small mb-2">
              Please sign in or create an account to continue browsing.
            </div>
            <div className="d-flex gap-2">
              <Link to="/login" className="btn btn-sm btn-accent rounded-pill px-3">
                Sign In
              </Link>
              <Link to="/register" className="btn btn-sm btn-outline-secondary rounded-pill px-3">
                Sign Up
              </Link>
            </div>
          </div>
          <button
            type="button"
            className="btn-close"
            aria-label="Close"
            onClick={() => setShowAuthNotice(false)}
          ></button>
        </div>
      )}

      {/* Hero Section */}
      <section
        className="hero-section text-white py-5 px-3 mb-5 rounded-4 position-relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #312e81 100%)',
        }}
      >
        <div className="container py-4 position-relative z-1">
          <div className="row align-items-center">
            <div className="col-lg-7">
              <span className="badge bg-warning text-dark px-3 py-2 rounded-pill fw-bold mb-3">
                <i className="bi bi-stars me-1"></i> Welcome to BookHaven
              </span>
              <h1 className="display-4 fw-bold mb-3 text-white" style={{ fontFamily: 'var(--font-serif)' }}>
                Discover World of Stories & Artisanal Stationary
              </h1>
              <p className="lead text-light mb-4 opacity-90">
                Explore thousands of curated books across classic literature, sci-fi, romance, and non-fiction, alongside handcrafted writing merchandise.
              </p>
              <div className="d-flex flex-wrap gap-3">
                <Link to="/books" className="btn btn-accent btn-lg px-4 rounded-pill shadow">
                  Browse Catalog <i className="bi bi-arrow-right ms-2"></i>
                </Link>
                <Link to="/deals" className="btn btn-outline-light btn-lg px-4 rounded-pill">
                  View Special Deals
                </Link>
              </div>
            </div>
            <div className="col-lg-5 d-none d-lg-block text-center">
              <img
                src="https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80"
                alt="Book collection"
                className="img-fluid rounded-4 shadow-lg border border-secondary border-opacity-25"
                style={{ maxHeight: '340px', objectFit: 'cover' }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Loading / Error State */}
      {loading ? (
        <LoadingSpinner message="Fetching literary collections..." />
      ) : error ? (
        <div className="alert alert-danger my-4 d-flex align-items-center" role="alert">
          <i className="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
          <div>{error}</div>
        </div>
      ) : (
        <>
          {/* Genre Category Quick Browse */}
          <section className="mb-5">
            <div className="d-flex justify-content-between align-items-end mb-4">
              <div>
                <h2 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
                  Browse by Genre
                </h2>
                <p className="text-muted mb-0">Find your favorite category of reading material</p>
              </div>
              <Link to="/genres" className="text-decoration-none fw-semibold text-accent" style={{ color: 'var(--color-accent)' }}>
                All Genres <i className="bi bi-arrow-right"></i>
              </Link>
            </div>
            <div className="row g-3">
              {genres.map((genre) => (
                <div key={genre.id} className="col-6 col-md-4 col-lg-2">
                  <Link
                    to={`/books?genre_id=${genre.id}`}
                    className="card h-100 border-0 shadow-sm text-center p-3 text-decoration-none text-dark rounded-3 hover-shadow transition-all"
                    style={{ backgroundColor: '#f8fafc' }}
                  >
                    <div className="mb-2 text-primary fs-3">
                      <i className="bi bi-bookmark-heart"></i>
                    </div>
                    <h6 className="fw-bold mb-1 text-truncate">{genre.name}</h6>
                    <small className="text-muted" style={{ fontSize: '0.75rem' }}>
                      {genre.description ? `${genre.description.substring(0, 30)}...` : 'Explore books'}
                    </small>
                  </Link>
                </div>
              ))}
            </div>
          </section>

          {/* Featured Books Section */}
          <section className="mb-5">
            <div className="d-flex justify-content-between align-items-end mb-4">
              <div>
                <h2 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
                  New & Featured Releases
                </h2>
                <p className="text-muted mb-0">Fresh arrivals straight from top publishers</p>
              </div>
              <Link to="/books" className="text-decoration-none fw-semibold text-accent" style={{ color: 'var(--color-accent)' }}>
                View All Books <i className="bi bi-arrow-right"></i>
              </Link>
            </div>
            {featuredBooks.length === 0 ? (
              <p className="text-muted">No books available in the catalog yet.</p>
            ) : (
              <div className="row g-4">
                {featuredBooks.map((book) => (
                  <div key={book.id} className="col-12 col-sm-6 col-md-4 col-lg-3">
                    <BookCard book={book} />
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Promo Section for Stationery */}
          <section className="bg-light p-4 p-md-5 rounded-4 shadow-sm mb-5">
            <div className="row align-items-center">
              <div className="col-md-7">
                <span className="badge bg-indigo text-white mb-2 px-3 py-1 rounded-pill" style={{ backgroundColor: '#4f46e5' }}>
                  Artisanal Collection
                </span>
                <h3 className="fw-bold mb-2">Premium Writing & Reading Accessories</h3>
                <p className="text-muted mb-4">
                  Elevate your reading nook with handcrafted leather journals, fountain pens, and aesthetic bookmarks.
                </p>
                <Link to="/stationery" className="btn btn-accent rounded-pill px-4">
                  Explore Stationery <i className="bi bi-pen ms-1"></i>
                </Link>
              </div>
              <div className="col-md-5 text-center mt-3 mt-md-0">
                <img
                  src="https://images.unsplash.com/photo-1585776245991-cf89dd7fc73a?auto=format&fit=crop&w=500&q=80"
                  alt="Stationery collection"
                  className="img-fluid rounded-3 shadow-sm"
                  style={{ maxHeight: '220px', objectFit: 'cover' }}
                />
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default Home;