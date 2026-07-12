/**
 * Utility: Extract human-readable error message from Axios/FastAPI error responses.
 *
 * FastAPI returns errors in several formats:
 *   - Validation errors: { detail: [ { loc, msg, type }, ... ] }
 *   - HTTPException:     { detail: "string message" }
 *   - Sometimes:         { message: "..." }
 *
 * This helper normalizes all of them into a single user-facing string.
 */

export function extractErrorMessage(error, fallback = 'An unexpected error occurred.') {
  if (!error) return fallback;

  const data = error.response?.data;

  if (!data) {
    // Network error or timeout
    if (error.code === 'ECONNABORTED') return 'Request timed out. Please try again.';
    if (error.message) return error.message;
    return fallback;
  }

  // FastAPI validation error array
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((err) => {
        const field = err.loc?.slice(-1)?.[0] || 'field';
        return `${field}: ${err.msg}`;
      })
      .join('\n');
  }

  // FastAPI HTTPException string
  if (typeof data.detail === 'string') {
    return data.detail;
  }

  // Generic message field
  if (typeof data.message === 'string') {
    return data.message;
  }

  return fallback;
}

/**
 * Extract field-level validation errors for react-hook-form setError().
 * Returns an object like { email: "message", password: "message" }.
 */
export function extractFieldErrors(error) {
  const data = error.response?.data;
  const fieldErrors = {};

  if (data && Array.isArray(data.detail)) {
    data.detail.forEach((err) => {
      const field = err.loc?.slice(-1)?.[0];
      if (field && field !== '__root__') {
        fieldErrors[field] = err.msg;
      }
    });
  }

  return fieldErrors;
}
