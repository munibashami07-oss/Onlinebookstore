import React, { useEffect, useState, useContext, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import bookService from '../api/bookService';
import genreService from '../api/genreService';
import reviewService from '../api/reviewService';
import cartService from '../api/cartService';
import { AuthContext } from '../context/AuthContext';
import { UserContext } from '../context/UserContext';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { extractErrorMessage } from '../utils/errorUtils';

const BookDetails = () => {
  const { id } = useParams();
  const { isAuthenticated } = useContext(AuthContext);
  const { user } = useContext(UserContext);
  const navigate = useNavigate();

  // Book & Genre State
  const [book, setBook] = useState(null);
  const [genre, setGenre] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  // Cart action state
  const [addingToCart, setAddingToCart] = useState(false);
  const [cartFeedback, setCartFeedback] = useState('');

  // Reviews State
  const [reviews, setReviews] = useState([]);
  const [ratingSummary, setRatingSummary] = useState({ average_rating: 0, total_reviews: 0 });
  const [reviewsLoading, setReviewsLoading] = useState(false);

  // Review Form State
  const [newRating, setNewRating] = useState(5);
  const [newComment, setNewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [editingReviewId, setEditingReviewId] = useState(null);

  const fallbackCover = 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80';

  // Fetch reviews & rating
  const fetchReviews = useCallback(async () => {
    setReviewsLoading(true);
    try {
      const [reviewsData, ratingData] = await Promise.all([
        reviewService.getBookReviews(id),
        reviewService.getBookRating(id),
      ]);
      setReviews(reviewsData);
      setRatingSummary(ratingData);
    } catch {
      // Non-fatal if reviews fetch encounters issue
    } finally {
      setReviewsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    const fetchBook = async () => {
      setLoading(true);
      setError(null);
      setNotFound(false);
      try {
        const data = await bookService.getBookById(id);
        setBook(data);

        if (data.genre_id) {
          try {
            const genreData = await genreService.getGenreById(data.genre_id);
            setGenre(genreData);
          } catch {
            // Non-fatal if genre detail fails
          }
        }

        await fetchReviews();
      } catch (err) {
        if (err.response?.status === 404) {
          setNotFound(true);
        } else {
          setError(extractErrorMessage(err, 'Failed to fetch book details.'));
        }
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchBook();
    }
  }, [id, fetchReviews]);

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: window.location } });
      return;
    }
    setAddingToCart(true);
    setCartFeedback('');
    try {
      await cartService.addToCart(book.id, 1);
      setCartFeedback('Item added to cart!');
      setTimeout(() => setCartFeedback(''), 3000);
    } catch (err) {
      setCartFeedback(extractErrorMessage(err, 'Failed to add item to cart.'));
    } finally {
      setAddingToCart(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    setSubmittingReview(true);
    setReviewError('');
    try {
      if (editingReviewId) {
        await reviewService.updateReview(editingReviewId, {
          rating: newRating,
          review_text: newComment,
        });
        setEditingReviewId(null);
      } else {
        await reviewService.createReview({
          book_id: parseInt(id, 10),
          rating: newRating,
          review_text: newComment,
        });
      }
      setNewComment('');
      setNewRating(5);
      await fetchReviews();
    } catch (err) {
      setReviewError(extractErrorMessage(err, 'Failed to submit review.'));
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleEditClick = (review) => {
    setEditingReviewId(review.id);
    setNewRating(review.rating);
    setNewComment(review.review_text || '');
  };

  const handleDeleteClick = async (reviewId) => {
    if (!window.confirm('Delete this review?')) return;
    try {
      await reviewService.deleteReview(reviewId);
      await fetchReviews();
    } catch (err) {
      setReviewError(extractErrorMessage(err, 'Failed to delete review.'));
    }
  };

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <i
        key={i}
        className={`bi ${i < rating ? 'bi-star-fill text-warning' : 'bi-star text-secondary opacity-50'} me-1`}
      ></i>
    ));
  };

  if (loading) {
    return <LoadingSpinner message="Retrieving book details..." />;
  }

  if (notFound) {
    return (
      <div className="container py-5">
        <EmptyState
          icon="bi-journal-x"
          title="Book Not Found"
          message={`We couldn't find a book with ID #${id}. It may have been removed.`}
          actionText="Back to Catalog"
          onAction={() => navigate('/books')}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {error}
        </div>
        <Link to="/books" className="btn btn-outline-secondary mt-3">
          <i className="bi bi-arrow-left me-1"></i> Back to Catalog
        </Link>
      </div>
    );
  }

  const avgRating = ratingSummary.average_rating || 0;
  const totalReviews = ratingSummary.total_reviews || 0;

  return (
    <div className="container py-5">
      {/* Breadcrumb */}
      <nav aria-label="breadcrumb" className="mb-4">
        <ol className="breadcrumb">
          <li className="breadcrumb-item">
            <Link to="/" className="text-decoration-none">Home</Link>
          </li>
          <li className="breadcrumb-item">
            <Link to="/books" className="text-decoration-none">Books</Link>
          </li>
          {genre && (
            <li className="breadcrumb-item">
              <Link to={`/books?genre_id=${genre.id}`} className="text-decoration-none">{genre.name}</Link>
            </li>
          )}
          <li className="breadcrumb-item active" aria-current="page">{book.title}</li>
        </ol>
      </nav>

      {/* Book Main Section */}
      <div className="card border-0 shadow-lg rounded-4 overflow-hidden p-4 mb-5">
        <div className="row g-4">
          {/* Cover Image */}
          <div className="col-md-5 col-lg-4 text-center">
            <div className="bg-light p-4 rounded-3 d-inline-block w-100">
              <img
                src={book.cover_image_url || fallbackCover}
                alt={book.title}
                className="img-fluid rounded-3 shadow-md"
                style={{ maxHeight: '420px', objectFit: 'cover' }}
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = fallbackCover;
                }}
              />
            </div>
          </div>

          {/* Book Info */}
          <div className="col-md-7 col-lg-8 d-flex flex-column justify-content-between">
            <div>
              {genre && (
                <span className="badge bg-primary px-3 py-2 rounded-pill fw-normal mb-2">
                  {genre.name}
                </span>
              )}
              <h1 className="fw-bold mb-2 text-dark" style={{ fontFamily: 'var(--font-serif)' }}>
                {book.title}
              </h1>
              <p className="lead text-muted mb-2">By <strong className="text-dark">{book.author}</strong></p>

              {/* Star Rating Overview */}
              <div className="d-flex align-items-center mb-3">
                {renderStars(Math.round(avgRating))}
                <span className="fw-bold ms-2 me-1">{avgRating.toFixed(1)}</span>
                <span className="text-muted small">({totalReviews} {totalReviews === 1 ? 'review' : 'reviews'})</span>
              </div>

              <div className="d-flex align-items-center gap-3 mb-4">
                <span className="display-6 fw-bold text-accent" style={{ color: 'var(--color-accent)' }}>
                  ${parseFloat(book.price).toFixed(2)}
                </span>
                <span className="badge bg-success bg-opacity-10 text-success border border-success px-3 py-2 rounded-pill">
                  <i className="bi bi-check-circle me-1"></i> In Stock & Ready to Ship
                </span>
              </div>

              <hr className="my-4" />

              <h5 className="fw-bold mb-2">Synopsis & Description</h5>
              <p className="text-secondary leading-relaxed mb-4">
                {book.description || 'No detailed description available for this publication.'}
              </p>

              {/* Publication Specs */}
              <div className="bg-light p-3 rounded-3 mb-4">
                <div className="row g-2 text-center text-md-start">
                  <div className="col-6 col-sm-4">
                    <small className="text-muted d-block">ISBN</small>
                    <span className="fw-semibold text-dark">{book.isbn}</span>
                  </div>
                  <div className="col-6 col-sm-4">
                    <small className="text-muted d-block">Publication Date</small>
                    <span className="fw-semibold text-dark">
                      {new Date(book.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="col-6 col-sm-4">
                    <small className="text-muted d-block">Catalog ID</small>
                    <span className="fw-semibold text-dark">#{book.id}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            {cartFeedback && (
              <div className="alert alert-info py-2 px-3 mb-3 small" role="alert">
                {cartFeedback}
              </div>
            )}

            <div className="d-flex flex-wrap gap-3 align-items-center border-top pt-4">
              <button
                className="btn btn-accent btn-lg rounded-pill px-4 fw-bold shadow-sm"
                onClick={handleAddToCart}
                disabled={addingToCart}
              >
                {addingToCart ? (
                  <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                ) : (
                  <i className="bi bi-cart-plus me-2"></i>
                )}
                Add to Cart
              </button>
              <Link to="/books" className="btn btn-outline-secondary px-4 rounded-pill">
                <i className="bi bi-arrow-left me-2"></i> Back to Catalog
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Reviews & Ratings Section */}
      <div className="card border-0 shadow-lg rounded-4 p-4 p-md-5">
        <h3 className="fw-bold mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
          Customer Reviews & Ratings
        </h3>

        {/* Rating Breakdown Header */}
        <div className="row align-items-center bg-light p-4 rounded-4 mb-4">
          <div className="col-md-4 text-center border-end-md">
            <h1 className="display-3 fw-bold text-dark mb-0">{avgRating.toFixed(1)}</h1>
            <div className="mb-1">{renderStars(Math.round(avgRating))}</div>
            <span className="text-muted small">Based on {totalReviews} customer ratings</span>
          </div>
          <div className="col-md-8 mt-3 mt-md-0 ps-md-4">
            <h5 className="fw-bold mb-2">Have you read this book?</h5>
            <p className="text-muted small mb-0">
              Share your thoughts and rate this book to help fellow readers decide.
            </p>
          </div>
        </div>

        {/* Submit / Edit Review Form */}
        <div className="card border p-4 rounded-3 mb-5 bg-white">
          <h5 className="fw-bold mb-3">
            {editingReviewId ? 'Edit Your Review' : 'Write a Review'}
          </h5>

          {reviewError && (
            <div className="alert alert-danger py-2 px-3 mb-3 small">
              {reviewError}
            </div>
          )}

          {!isAuthenticated ? (
            <div className="text-muted small">
              Please <Link to="/login" className="fw-bold text-accent">Sign In</Link> to submit a review for this book.
            </div>
          ) : (
            <form onSubmit={handleReviewSubmit}>
              <div className="mb-3">
                <label className="form-label small fw-semibold me-3">Your Rating:</label>
                <div className="d-inline-flex gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      type="button"
                      key={star}
                      className="btn btn-link p-0 text-decoration-none"
                      onClick={() => setNewRating(star)}
                    >
                      <i
                        className={`bi ${star <= newRating ? 'bi-star-fill text-warning' : 'bi-star text-secondary'} fs-4`}
                      ></i>
                    </button>
                  ))}
                </div>
              </div>

              <div className="mb-3">
                <textarea
                  className="form-control"
                  rows="3"
                  placeholder="Share details of your experience with this book..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  maxLength={2000}
                ></textarea>
              </div>

              <div className="d-flex gap-2">
                <button
                  type="submit"
                  className="btn btn-accent rounded-pill px-4"
                  disabled={submittingReview}
                >
                  {submittingReview ? 'Submitting…' : editingReviewId ? 'Update Review' : 'Submit Review'}
                </button>
                {editingReviewId && (
                  <button
                    type="button"
                    className="btn btn-outline-secondary rounded-pill px-3"
                    onClick={() => {
                      setEditingReviewId(null);
                      setNewComment('');
                    }}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          )}
        </div>

        {/* Reviews List */}
        {reviewsLoading ? (
          <LoadingSpinner message="Fetching reviews..." />
        ) : reviews.length === 0 ? (
          <p className="text-muted text-center py-4">No reviews submitted yet. Be the first to review this book!</p>
        ) : (
          <div className="d-flex flex-column gap-3">
            {reviews.map((rev) => {
              const isOwner = user && user.id === rev.user_id;
              return (
                <div key={rev.id} className="border-bottom pb-3">
                  <div className="d-flex justify-content-between align-items-start mb-1">
                    <div>
                      <strong className="text-dark">{rev.reviewer_name || `User #${rev.user_id}`}</strong>
                      <span className="ms-3">{renderStars(rev.rating)}</span>
                    </div>
                    <small className="text-muted">{new Date(rev.created_at).toLocaleDateString()}</small>
                  </div>
                  <p className="text-secondary mb-2">{rev.review_text || 'No review text provided.'}</p>

                  {isOwner && (
                    <div className="d-flex gap-2">
                      <button
                        className="btn btn-sm btn-link text-primary p-0 me-2"
                        onClick={() => handleEditClick(rev)}
                      >
                        <i className="bi bi-pencil me-1"></i> Edit
                      </button>
                      <button
                        className="btn btn-sm btn-link text-danger p-0"
                        onClick={() => handleDeleteClick(rev.id)}
                      >
                        <i className="bi bi-trash me-1"></i> Delete
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default BookDetails;
