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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f1419] to-[#1a1f26]">
      <div className="w-full max-w-md px-4">
        <div className="bg-[#1a1f26] rounded-lg shadow-xl p-8 border border-[#2d333f]">
          <h1 className="text-3xl font-bold text-center text-white mb-2">
            🎯 Recruitment Platform
          </h1>
          <p className="text-center text-[#8b95a5] text-sm mb-8">Login to your account</p>

          {(error || formError) && (
            <div className="mb-4 p-4 bg-[rgba(196,30,58,0.15)] border border-[rgba(196,30,58,0.3)] text-[#FF6B7A] rounded">
              {error || formError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-[#f5f7fa] mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-[#0f1419] border border-[#2d333f] text-[#f5f7fa] placeholder-[#6b7684] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#C41E3A]"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-[#f5f7fa] mb-2">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-[#0f1419] border border-[#2d333f] text-[#f5f7fa] placeholder-[#6b7684] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#C41E3A]"
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#C41E3A] hover:bg-[#A91930] disabled:bg-[#2d333f] text-white font-semibold rounded-lg transition duration-200 shadow-md hover:shadow-lg"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[#8b95a5]">
            Don't have an account?{' '}
            <Link to="/register" className="text-[#C41E3A] hover:text-[#FF6B7A] font-semibold">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
