import React from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import ChatWidget from '../components/ChatWidget';
import ChatSupportWidget from '../components/ChatSupportWidget';

const Layout = ({ children }) => {
  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar />
      <main className="flex-grow-1">
        {children}
      </main>
      <Footer />
      <ChatWidget />
      <ChatSupportWidget />
    </div>
  );
};

export default Layout;