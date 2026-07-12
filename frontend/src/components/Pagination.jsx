import React from 'react';

const Pagination = ({ currentPage, totalItems, pageSize, onPageChange }) => {
  const totalPages = Math.ceil(totalItems / pageSize);

  if (totalPages <= 1) return null;

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <nav aria-label="Page navigation" className="d-flex justify-content-center mt-4">
      <ul className="pagination pagination-md">
        <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
          <button
            className="page-item-link page-link"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            <i className="bi bi-chevron-left"></i> Previous
          </button>
        </li>
        {pages.map((page) => (
          <li key={page} className={`page-item ${page === currentPage ? 'active' : ''}`}>
            <button
              className="page-link"
              onClick={() => onPageChange(page)}
              style={page === currentPage ? { backgroundColor: 'var(--color-accent)', borderColor: 'var(--color-accent)' } : {}}
            >
              {page}
            </button>
          </li>
        ))}
        <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
          <button
            className="page-link"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next <i className="bi bi-chevron-right"></i>
          </button>
        </li>
      </ul>
    </nav>
  );
};

export default Pagination;
