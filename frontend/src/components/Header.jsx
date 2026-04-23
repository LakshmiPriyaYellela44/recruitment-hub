import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

export const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-[#1a1f26] border-b-2 border-[#2d333f] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4 flex justify-between items-center">
        {/* Logo and Brand */}
        <Link to="/" className="flex items-center gap-2 sm:gap-3 hover:opacity-80 transition">
          <img 
            src="/images/logo.jpg" 
            alt="Buddy Recruitment Logo" 
            className="w-8 sm:w-10 h-8 sm:h-10 rounded-lg object-cover"
          />
          <div className="flex flex-col">
            <span className="text-lg sm:text-xl font-extrabold text-[#f5f7fa]">Tricon Infotech</span>
            <span className="text-xs font-medium text-[#8b95a5]">Buddy Recruitment</span>
          </div>
        </Link>
        
        {/* Desktop User Menu */}
        {user && (
          <div className="hidden sm:flex items-center gap-4 md:gap-6">
            <div className="flex items-center gap-2 md:gap-3">
              <div className="text-right">
                <p className="text-xs sm:text-sm font-semibold text-[#f5f7fa]">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-xs text-[#8b95a5] capitalize">{user.role}</p>
              </div>
              {user.subscription_type === 'PRO' && (
                <div className="ml-2 px-2 sm:px-3 py-1 bg-[#3a2a0a] text-[#ffd166] rounded-full text-xs font-bold border border-[#8b6f47]">
                  PRO
                </div>
              )}
            </div>
            <button
              onClick={handleLogout}
              style={{ backgroundColor: '#C41E3A' }}
              className="px-3 sm:px-4 py-2 hover:opacity-90 text-white rounded-md text-xs sm:text-sm font-semibold transition-all duration-200 transform hover:shadow-md active:scale-95"
            >
              Logout
            </button>
          </div>
        )}

        {/* Mobile Menu Toggle */}
        {user && (
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="sm:hidden flex flex-col gap-1.5 p-2 hover:bg-[#2d333f] rounded transition"
            aria-label="Toggle menu"
          >
            <span className={`w-5 h-0.5 bg-[#f5f7fa] transition-all ${mobileMenuOpen ? 'transform rotate-45 translate-y-2' : ''}`}></span>
            <span className={`w-5 h-0.5 bg-[#f5f7fa] transition-all ${mobileMenuOpen ? 'opacity-0' : ''}`}></span>
            <span className={`w-5 h-0.5 bg-[#f5f7fa] transition-all ${mobileMenuOpen ? 'transform -rotate-45 -translate-y-2' : ''}`}></span>
          </button>
        )}
      </div>

      {/* Mobile Menu */}
      {user && mobileMenuOpen && (
        <div className="sm:hidden bg-[#0f1419] border-t border-[#2d333f] px-4 py-4 space-y-4">
          <div className="text-left">
            <p className="text-sm font-semibold text-[#f5f7fa]">
              {user.first_name} {user.last_name}
            </p>
            <p className="text-xs text-[#8b95a5] capitalize mt-1">{user.role}</p>
            {user.subscription_type === 'PRO' && (
              <div className="mt-2 inline-block px-2 py-1 bg-[#3a2a0a] text-[#ffd166] rounded-full text-xs font-bold border border-[#8b6f47]">
                PRO
              </div>
            )}
          </div>
          <button
            onClick={() => {
              handleLogout();
              setMobileMenuOpen(false);
            }}
            style={{ backgroundColor: '#C41E3A' }}
            className="w-full px-4 py-2 hover:opacity-90 text-white rounded-md text-sm font-semibold transition-all duration-200"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
};;
