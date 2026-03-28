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
    <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold">
          🎯 Recruitment
        </Link>
        
        {user && (
          <div className="flex items-center gap-6">
            <span className="text-sm">
              {user.first_name} {user.last_name}
              <span className="ml-2 px-2 py-1 bg-blue-500 rounded text-xs">
                {user.role}
              </span>
            </span>
            {user.subscription_type === 'PRO' && (
              <span className="px-2 py-1 bg-yellow-400 text-blue-900 rounded text-xs font-bold">
                ⭐ PRO
              </span>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 rounded text-sm font-medium transition"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
