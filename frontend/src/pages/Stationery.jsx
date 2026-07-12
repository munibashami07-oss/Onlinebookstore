import React, { useEffect, useState } from 'react';
import stationeryService from '../api/stationeryService';
import Pagination from '../components/Pagination';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { extractErrorMessage } from '../utils/errorUtils';

const Stationery = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;

  const fallbackImage = 'https://images.unsplash.com/photo-1585776245991-cf89dd7fc73a?auto=format&fit=crop&w=400&q=80';

  useEffect(() => {
    const fetchStationery = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await stationeryService.listStationery(currentPage, pageSize);
        setItems(data);
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to fetch stationery merchandise.'));
        setItems([]);
      } finally {
        setLoading(false);
      }
    };

    fetchStationery();
  }, [currentPage]);

  return (
    <div className="container py-4">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-5">
        <span className="badge bg-indigo text-white px-3 py-2 rounded-pill mb-2" style={{ backgroundColor: '#4f46e5' }}>
          <i className="bi bi-pen-fill me-1"></i> Artisanal Merchandise
        </span>
        <h1 className="fw-bold display-5 mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
          Artisanal Stationery & Reading Goods
        </h1>
        <p className="text-muted lead">
          Elevate your daily reading & writing habits with handcrafted notebooks, pens, and bookmarks.
        </p>
      </div>

      {/* Main Grid */}
      {loading ? (
        <LoadingSpinner message="Loading stationery merchandise catalog..." />
      ) : error ? (
        <div className="alert alert-danger" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {error}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon="bi-box-seam"
          title="No Stationery Products Available"
          message="Our stationery catalog is currently being updated. Please check back shortly!"
        />
      ) : (
        <>
          <div className="row g-4">
            {items.map((item) => (
              <div key={item.id} className="col-12 col-sm-6 col-md-4 col-lg-3">
                <div className="card h-100 border-0 shadow-sm rounded-4 overflow-hidden hover-shadow transition-all">
                  <div className="bg-light text-center py-3 px-3 position-relative">
                    <img
                      src={item.cover_image_url || fallbackImage}
                      alt={item.name}
                      className="img-fluid rounded shadow-sm"
                      style={{ height: '180px', objectFit: 'cover', width: '100%' }}
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = fallbackImage;
                      }}
                    />
                    <span className={`position-absolute top-0 end-0 m-2 badge ${item.stock > 0 ? 'bg-success' : 'bg-secondary'}`}>
                      {item.stock > 0 ? `${item.stock} in stock` : 'Out of Stock'}
                    </span>
                  </div>

                  <div className="card-body d-flex flex-column justify-content-between p-3">
                    <div>
                      <h6 className="fw-bold text-dark text-truncate mb-1" title={item.name}>
                        {item.name}
                      </h6>
                      <p className="text-muted small line-clamp-2 mb-3" style={{ fontSize: '0.85rem' }}>
                        {item.description || 'Premium writing instrument and reading accessory.'}
                      </p>
                    </div>

                    <div className="d-flex align-items-center justify-content-between pt-2 border-top">
                      <span className="fs-5 fw-bold text-dark">${parseFloat(item.price).toFixed(2)}</span>
                      <button
                        className="btn btn-sm btn-outline-dark rounded-pill px-3"
                        onClick={() => alert(`Product: ${item.name}\nPrice: $${item.price}\nStock: ${item.stock}`)}
                      >
                        <i className="bi bi-info-circle me-1"></i> Info
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <Pagination
            currentPage={currentPage}
            totalItems={items.length >= pageSize ? (currentPage + 1) * pageSize : currentPage * pageSize}
            pageSize={pageSize}
            onPageChange={(page) => setCurrentPage(page)}
          />
        </>
      )}
    </div>
  );
};

export default Stationery;
