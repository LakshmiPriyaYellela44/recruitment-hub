import React from 'react';
import { useAuth } from '../context/AuthContext';
import { CandidateDashboard } from './CandidateDashboard';
import { RecruiterDashboard } from './RecruiterDashboard';
import { AdminDashboard } from './AdminDashboard';

export const Dashboard = () => {
  const { user } = useAuth();

  if (user?.role === 'ADMIN') {
    return <AdminDashboard />;
  }

  if (user?.role === 'RECRUITER') {
    return <RecruiterDashboard />;
  }

  return <CandidateDashboard />;
};
