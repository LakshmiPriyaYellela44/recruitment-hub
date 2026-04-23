import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login, error } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFormError('');

    try {
      await login(formData.email, formData.password);
      navigate('/dashboard');
    } catch (err) {
      setFormError(err.response?.data?.error?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f1419] via-[#1a1f26] to-[#0f1419] px-3 sm:px-4">
      <div className="w-full max-w-md px-2 sm:px-4">
        {/* Card Container */}
        <div className="bg-[#1a1f26] rounded-lg sm:rounded-xl shadow-lg p-6 sm:p-8 border border-[#2d333f]">
          {/* Professional Brand Header */}
          <div className="flex items-center justify-center gap-3 sm:gap-4 mb-8 sm:mb-10">
            {/* Logo Image */}
            <div className="flex-shrink-0">
              <img 
                src="/images/logo.jpg" 
                alt="Tricon Infotech Logo" 
                className="w-12 sm:w-16 h-12 sm:h-16 rounded-lg object-cover shadow-md"
              />
            </div>
            
            {/* Brand Text */}
            <div className="flex flex-col justify-center flex-grow">
              <h2 className="text-lg sm:text-xl font-extrabold text-[#f5f7fa] leading-tight">
                Tricon Infotech
              </h2>
              <p style={{ color: '#C41E3A' }} className="text-xs sm:text-sm font-semibold mt-0.5 uppercase tracking-wider">
                Buddy Recruitment
              </p>
            </div>
          </div>

          {/* Divider */}
          <div className="w-full h-px bg-gradient-to-r from-transparent via-[#2d333f] to-transparent mb-6 sm:mb-8"></div>

          {/* Heading */}
          <h1 className="text-xl sm:text-2xl font-bold text-center text-[#f5f7fa] mb-2">
            Welcome Back
          </h1>
          <p className="text-center text-[#8b95a5] text-xs sm:text-sm mb-6 sm:mb-8">
            Sign in to your account
          </p>

          {/* Error Alert */}
          {(error || formError) && (
            <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-[#3a0a0a] border border-[#5a1a1a] text-[#ff8a94] rounded-lg text-xs sm:text-sm font-medium">
              {error || formError}
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
            {/* Email Field */}
            <div>
              <label className="block text-xs sm:text-sm font-semibold text-[#f5f7fa] mb-2 uppercase tracking-wide">
                Email Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-[#2d333f] bg-[#0f1419] text-[#f5f7fa] placeholder-[#6d7a88] rounded-lg focus:outline-none focus:border-[#8B2635] focus:ring-4 focus:ring-[#5C1520] transition text-sm caret-[#8B2635]"
                placeholder="e-mail@gmail.com"
                required
              />
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-xs sm:text-sm font-semibold text-[#f5f7fa] mb-2 uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-[#2d333f] bg-[#0f1419] text-[#f5f7fa] placeholder-[#6d7a88] rounded-lg focus:outline-none focus:border-[#8B2635] focus:ring-4 focus:ring-[#5C1520] transition text-sm caret-[#8B2635]"
                placeholder="Enter your password"
                required
              />
            </div>

            {/* Login Button */}
            <button
              type="submit"
              disabled={loading}
              style={{ backgroundColor: '#C41E3A' }}
              className="w-full py-2 sm:py-3 hover:opacity-90 disabled:bg-[#3d4551] text-white font-semibold rounded-lg transition-all duration-200 transform hover:shadow-lg active:scale-95 disabled:cursor-not-allowed text-sm sm:text-base"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-3 h-3 sm:w-4 sm:h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Logging in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Signup Link */}
          <p className="mt-4 sm:mt-6 text-center text-xs sm:text-sm text-[#8b95a5]">
            Don't have an account?{' '}
            <Link 
              to="/register" 
              style={{ color: '#C41E3A' }}
              className="hover:opacity-80 font-semibold transition hover:underline"
            >
              Create Account
            </Link>
          </p>
        </div>

        {/* Footer Text */}
        <p className="text-center text-xs text-[#6d7a88] mt-4 sm:mt-6">
          © 2024 Buddy Recruitment Program. All rights reserved.
        </p>
      </div>
    </div>
  );
};
