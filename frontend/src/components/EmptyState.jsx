import React from 'react';

const EmptyState = ({
  icon = 'bi-inbox',
  title = 'No items found',
  message = 'Try adjusting your search query or filters.',
  actionText,
  onAction,
}) => {
  return (
    <div className="text-center py-5 my-4 px-3 bg-light rounded-3 shadow-sm">
      <i className={`bi ${icon} display-1 text-muted mb-3 d-block`}></i>
      <h4 className="fw-bold text-dark mb-2">{title}</h4>
      <p className="text-muted max-w-md mx-auto mb-4">{message}</p>
      {actionText && onAction && (
        <button className="btn btn-accent rounded-pill px-4" onClick={onAction}>
          {actionText}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
