import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import genreService from '../api/genreService';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { extractErrorMessage } from '../utils/errorUtils';

const Genres = () => {
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGenres = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await genreService.listGenres(1, 100);
        setGenres(data);
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to fetch literary genres.'));
      } finally {
        setLoading(false);
      }
    };

    fetchGenres();
  }, []);

  return (
    <div className="container py-4">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-5">
        <span className="badge bg-primary px-3 py-2 rounded-pill mb-2">
          <i className="bi bi-bookmarks-fill me-1"></i> Literary Categories
        </span>
        <h1 className="fw-bold display-5 mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
          Explore Genres & Categories
        </h1>
        <p className="text-muted lead">
          Browse through our curated collection of literary genres to find your next great read.
        </p>
      </div>

      {/* Content */}
      {loading ? (
        <LoadingSpinner message="Fetching literary categories..." />
      ) : error ? (
        <div className="alert alert-danger" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {error}
        </div>
      ) : genres.length === 0 ? (
        <EmptyState
          icon="bi-journal-bookmark"
          title="No Genres Found"
          message="There are no registered genres in the catalog at this time."
        />
      ) : (
        <div className="row g-4">
          {genres.map((genre) => (
            <div key={genre.id} className="col-12 col-md-6 col-lg-4">
              <div className="card h-100 border-0 shadow-sm rounded-4 p-4 hover-shadow transition-all bg-white d-flex flex-column justify-content-between">
                <div>
                  <div className="d-flex align-items-center mb-3">
                    <div
                      className="rounded-3 p-3 text-white me-3"
                      style={{
                        background: 'linear-gradient(135deg, var(--color-primary), var(--color-brand))',
                      }}
                    >
                      <i className="bi bi-journal-text fs-3"></i>
                    </div>
                    <div>
                      <h4 className="fw-bold mb-0 text-dark">{genre.name}</h4>
                      <small className="text-muted">Category ID #{genre.id}</small>
                    </div>
                  </div>
                  <p className="text-secondary mb-4">
                    {genre.description || 'Discover selected publications and releases in this literary theme.'}
                  </p>
                </div>
                <Link
                  to={`/books?genre_id=${genre.id}`}
                  className="btn btn-outline-primary rounded-pill w-100 py-2 fw-semibold"
                >
                  Browse {genre.name} Books <i className="bi bi-arrow-right ms-1"></i>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Genres;
