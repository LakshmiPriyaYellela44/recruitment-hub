import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

export const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-6 py-3 flex justify-between items-center">
        {/* Logo Section */}
        <Link to="/" className="flex items-center gap-3 hover:opacity-90 transition">
          <div className="bg-white rounded-lg p-2">
            <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M20 6h-2.15c-.74-1.6-2.04-2.97-3.6-3.7-.33-.16-.67-.27-1.02-.35V2h-2v.2c-.35.08-.69.19-1.02.35-1.56.73-2.86 2.1-3.6 3.7H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-8 .25c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm6 12H6v-6h12v6z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold leading-tight">Recruitment Hub</h1>
            <p className="text-blue-100 text-xs">Find Top Talent</p>
          </div>
        </Link>

        {/* User Section */}
        {user && (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-semibold">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-xs text-blue-100 uppercase tracking-wide">
                  {user.role}
                </p>
              </div>
              {user.subscription_type === 'PRO' && (
                <div className="flex items-center gap-1 bg-yellow-300 text-yellow-900 px-3 py-1 rounded-full">
                  <span className="text-sm">★</span>
                  <span className="text-xs font-bold">PRO</span>
                </div>
              )}
            </div>

            <div className="h-8 border-r border-blue-400"></div>

            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-semibold transition duration-200 transform hover:scale-105"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
