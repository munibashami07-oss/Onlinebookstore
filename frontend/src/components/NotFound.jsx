import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="container py-5 text-center my-5">
      <div className="max-w-md mx-auto">
        <div className="display-1 font-serif text-warning mb-3">404</div>
        <h1 className="h2 mb-3">Chapter Not Found</h1>
        <p class="text-muted lead fs-6 mb-4">
          The page you are looking for seems to have been misplaced or lost in the archives.
        </p>
        <Link to="/" className="btn btn-accent btn-lg px-4 rounded-pill">
          <i className="bi bi-house-door me-2"></i> Return to Homepage
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
