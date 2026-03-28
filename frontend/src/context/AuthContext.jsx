import React, { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check if user is logged in on mount
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await authService.getCurrentUser();
          setUser(response.data);
        } catch (err) {
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    try {
      setError(null);
      const response = await authService.login({ email, password });
      localStorage.setItem('access_token', response.data.access_token);
      setUser(response.data.user);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.error?.message || 'Login failed';
      setError(message);
      throw err;
    }
  };

  const register = async (data) => {
    try {
      setError(null);
      const response = await authService.register(data);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.error?.message || 'Registration failed';
      setError(message);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, login, register, logout, loading, error, refetchUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const refetchUser = async () => {
  try {
    const response = await authService.getCurrentUser();
    return response.data;
  } catch (err) {
    return null;
  }
};
