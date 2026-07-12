import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import bookService from '../api/bookService';
import genreService from '../api/genreService';
import BookCard from '../components/BookCard';
import Pagination from '../components/Pagination';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { extractErrorMessage } from '../utils/errorUtils';

const Books = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { id: routeGenreId } = useParams();
  const navigate = useNavigate();

  // Data state
  const [books, setBooks] = useState([]);
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter & Search states initialized from URL params
  const searchQuery = searchParams.get('q') || '';
  const selectedGenre = routeGenreId || searchParams.get('genre_id') || '';
  const minPrice = searchParams.get('min_price') || '';
  const maxPrice = searchParams.get('max_price') || '';
  const inStockOnly = searchParams.get('in_stock') === 'true';
  const sortBy = searchParams.get('sort_by') || '';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 12;

  // Local form state for search input
  const [localSearch, setLocalSearch] = useState(searchQuery);

  // Sync local search input if searchParams change
  useEffect(() => {
    setLocalSearch(searchQuery);
  }, [searchQuery]);

  // Fetch genres for filter dropdown
  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const data = await genreService.listGenres(1, 100);
        setGenres(data);
      } catch (err) {
        console.error('Failed to load genres for filter:', err);
      }
    };
    fetchGenres();
  }, []);

  // Fetch books based on current query/filter state
  const fetchBooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let data = [];
      if (searchQuery.trim()) {
        // Search endpoint
        data = await bookService.searchBooks(searchQuery.trim(), currentPage, pageSize);
      } else {
        // Catalog endpoint with query filters
        const params = {
          page: currentPage,
          page_size: pageSize,
        };
        if (selectedGenre) params.genre_id = parseInt(selectedGenre, 10);
        if (minPrice) params.min_price = parseFloat(minPrice);
        if (maxPrice) params.max_price = parseFloat(maxPrice);
        if (inStockOnly) params.in_stock = true;
        if (sortBy) params.sort_by = sortBy;

        data = await bookService.listBooks(params);
      }
      setBooks(data);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to fetch book catalog.'));
      setBooks([]);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedGenre, minPrice, maxPrice, inStockOnly, sortBy, currentPage]);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  // Update query params helper.
  // NOTE: only resets to page 1 when a FILTER changes (genre, price, search,
  // sort, in-stock) -- not when `key === 'page'` itself, otherwise clicking
  // pagination controls would immediately get overwritten back to page 1.
  const updateParam = (key, value) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    if (key !== 'page') {
      newParams.set('page', '1'); // Reset to page 1 on filter change
    }
    setSearchParams(newParams);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    updateParam('q', localSearch.trim());
  };

  const handleResetFilters = () => {
    setLocalSearch('');
    if (routeGenreId) {
      navigate('/books');
    } else {
      setSearchParams({});
    }
  };

  return (
    <div className="container py-4">
      {/* Header */}
      <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 pb-3 border-bottom">
        <div>
          <h1 className="fw-bold mb-1" style={{ fontFamily: 'var(--font-heading)' }}>
            {selectedGenre
              ? `Books in ${genres.find((g) => g.id === parseInt(selectedGenre, 10))?.name || 'Selected Genre'}`
              : 'Book Catalog'}
          </h1>
          <p className="text-muted mb-0">Browse and filter our comprehensive collection of books.</p>
        </div>
        {(searchQuery || selectedGenre || minPrice || maxPrice || inStockOnly || sortBy) && (
          <button
            className="btn btn-outline-secondary btn-sm rounded-pill mt-3 mt-md-0"
            onClick={handleResetFilters}
          >
            <i className="bi bi-x-circle me-1"></i> Clear Filters
          </button>
        )}
      </div>

      <div className="row g-4">
        {/* Sidebar Filters */}
        <div className="col-lg-3">
          <div className="card border-0 shadow-sm rounded-3 p-3 bg-light">
            <h5 className="fw-bold mb-3 d-flex align-items-center">
              <i className="bi bi-funnel me-2 text-primary"></i> Filter Books
            </h5>

            {/* Search input */}
            <form onSubmit={handleSearchSubmit} className="mb-4">
              <label className="form-label small fw-semibold">Search Title / Author / ISBN</label>
              <div className="input-group input-group-sm">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Enter keywords..."
                  value={localSearch}
                  onChange={(e) => setLocalSearch(e.target.value)}
                />
                <button type="submit" className="btn btn-primary">
                  <i className="bi bi-search"></i>
                </button>
              </div>
            </form>

            {/* Genre Filter */}
            <div className="mb-4">
              <label className="form-label small fw-semibold">Genre</label>
              <select
                className="form-select form-select-sm"
                value={selectedGenre}
                onChange={(e) => updateParam('genre_id', e.target.value)}
              >
                <option value="">All Genres</option>
                {genres.map((g) => (
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Price Range */}
            <div className="mb-4">
              <label className="form-label small fw-semibold">Price Range ($)</label>
              <div className="d-flex gap-2">
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Min"
                  className="form-control form-control-sm"
                  value={minPrice}
                  onChange={(e) => updateParam('min_price', e.target.value)}
                />
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Max"
                  className="form-control form-control-sm"
                  value={maxPrice}
                  onChange={(e) => updateParam('max_price', e.target.value)}
                />
              </div>
            </div>

            {/* Availability */}
            <div className="mb-4 form-check">
              <input
                type="checkbox"
                className="form-check-input"
                id="inStockCheck"
                checked={inStockOnly}
                onChange={(e) => updateParam('in_stock', e.target.checked ? 'true' : '')}
              />
              <label className="form-check-label small fw-semibold" htmlFor="inStockCheck">
                In Stock Only
              </label>
            </div>
          </div>
        </div>

        {/* Catalog Main Content */}
        <div className="col-lg-9">
          {/* Sorting Bar */}
          <div className="d-flex flex-wrap justify-content-between align-items-center bg-white p-3 rounded-3 shadow-sm mb-4">
            <span className="text-muted small">
              Showing <strong>{books.length}</strong> items
            </span>
            <div className="d-flex align-items-center gap-2">
              <label className="small text-muted me-1 mb-0">Sort By:</label>
              <select
                className="form-select form-select-sm"
                style={{ width: 'auto' }}
                value={sortBy}
                onChange={(e) => updateParam('sort_by', e.target.value)}
              >
                <option value="">Default</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="newest">Newest First</option>
              </select>
            </div>
          </div>

          {/* Loading / Error / Content */}
          {loading ? (
            <LoadingSpinner message="Filtering catalog books..." />
          ) : error ? (
            <div className="alert alert-danger my-4" role="alert">
              <i className="bi bi-exclamation-triangle-fill me-2"></i>
              {error}
            </div>
          ) : books.length === 0 ? (
            <EmptyState
              icon="bi-search"
              title="No books match your criteria"
              message="Try broadening your search term or clearing price & genre filters."
              actionText="Reset All Filters"
              onAction={handleResetFilters}
            />
          ) : (
            <>
              <div className="row g-4">
                {books.map((book) => {
                  const genreObj = genres.find((g) => g.id === book.genre_id);
                  return (
                    <div key={book.id} className="col-12 col-sm-6 col-md-4">
                      <BookCard book={book} genreName={genreObj?.name} />
                    </div>
                  );
                })}
              </div>

              {/* Pagination */}
              <Pagination
                currentPage={currentPage}
                totalItems={books.length >= pageSize ? (currentPage + 1) * pageSize : currentPage * pageSize}
                pageSize={pageSize}
                onPageChange={(page) => updateParam('page', page.toString())}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Books;