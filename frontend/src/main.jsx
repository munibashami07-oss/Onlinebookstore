import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Import Bootstrap 5 CSS, JS Bundle, and Bootstrap Icons
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import 'bootstrap-icons/font/bootstrap-icons.css';

// Import Global Styles
import './index.css';
import './App.css';

import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
