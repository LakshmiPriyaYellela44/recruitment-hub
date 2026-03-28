import React, { useState, useEffect } from 'react';
import adminService from '../services/adminService';
import './AdminDashboard.css';

export const AdminDashboard = () => {
  // Recruiters state
  const [recruiters, setRecruiters] = useState([]);
  
  // Shared state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updating, setUpdating] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    fetchRecruiters();
  }, []);

  const fetchRecruiters = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getRecruiters(100, 0);
      setRecruiters(data.recruiters || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch recruiters');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscriptionUpdate = async (recruiterId, newSubscription) => {
    try {
      setUpdating(recruiterId);
      setError(null);
      
      await adminService.updateRecruiterSubscription(recruiterId, newSubscription);
      
      // Update local state
      setRecruiters(recruiters.map(r => 
        r.id === recruiterId 
          ? { ...r, subscription_type: newSubscription }
          : r
      ));
      
      setSuccessMessage(`Recruiter subscription updated to ${newSubscription}`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update subscription');
      console.error('Error updating subscription:', err);
    } finally {
      setUpdating(null);
    }
  };

  const handleDeactivateRecruiter = async (recruiterId) => {
    if (!window.confirm('Are you sure you want to deactivate this recruiter?')) {
      return;
    }

    try {
      setUpdating(recruiterId);
      setError(null);
      
      await adminService.deactivateRecruiter(recruiterId);
      
      // Update local state
      setRecruiters(recruiters.map(r => 
        r.id === recruiterId 
          ? { ...r, is_active: false }
          : r
      ));
      
      setSuccessMessage('Recruiter deactivated successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to deactivate recruiter');
      console.error('Error deactivating recruiter:', err);
    } finally {
      setUpdating(null);
    }
  };

  const handleActivateRecruiter = async (recruiterId) => {
    try {
      setUpdating(recruiterId);
      setError(null);
      
      await adminService.activateRecruiter(recruiterId);
      
      // Update local state
      setRecruiters(recruiters.map(r => 
        r.id === recruiterId 
          ? { ...r, is_active: true }
          : r
      ));
      
      setSuccessMessage('Recruiter activated successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to activate recruiter');
      console.error('Error activating recruiter:', err);
    } finally {
      setUpdating(null);
    }
  };

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>🛠️ Recruiter Management</h1>
        <p>Manage recruiters and their subscription licenses</p>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success">
          {successMessage}
        </div>
      )}

      <div className="recruiters-section">
        <div className="section-header">
          <h2>Recruiters ({recruiters.length})</h2>
          <button onClick={fetchRecruiters} disabled={loading} className="btn-refresh">
            🔄 Refresh
          </button>
        </div>

        {recruiters.length === 0 ? (
          <p className="no-data">No recruiters found</p>
        ) : (
          <div className="recruiters-table-container">
            <table className="recruiters-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Subscription</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recruiters.map((recruiter) => (
                  <tr key={recruiter.id} className={!recruiter.is_active ? 'inactive' : ''}>
                    <td>
                      <strong>
                        {recruiter.first_name} {recruiter.last_name}
                      </strong>
                    </td>
                    <td>{recruiter.email}</td>
                    <td>
                      <div className="subscription-cell">
                        <span className={`badge subscription-${recruiter.subscription_type.toLowerCase()}`}>
                          {recruiter.subscription_type}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge status-${recruiter.is_active ? 'active' : 'inactive'}`}>
                        {recruiter.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className="actions-cell">
                        <div className="subscription-actions">
                          <button
                            onClick={() => handleSubscriptionUpdate(recruiter.id, 'BASIC')}
                            disabled={
                              updating === recruiter.id || 
                              recruiter.subscription_type === 'BASIC'
                            }
                            className="btn btn-sm btn-basic"
                            title="Set to BASIC subscription"
                          >
                            To BASIC
                          </button>
                          <button
                            onClick={() => handleSubscriptionUpdate(recruiter.id, 'PRO')}
                            disabled={
                              updating === recruiter.id || 
                              recruiter.subscription_type === 'PRO'
                            }
                            className="btn btn-sm btn-pro"
                            title="Upgrade to PRO subscription"
                          >
                            To PRO
                          </button>
                        </div>

                        <div className="status-actions">
                          {recruiter.is_active ? (
                            <button
                              onClick={() => handleDeactivateRecruiter(recruiter.id)}
                              disabled={updating === recruiter.id}
                              className="btn btn-sm btn-danger"
                              title="Deactivate recruiter"
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              onClick={() => handleActivateRecruiter(recruiter.id)}
                              disabled={updating === recruiter.id}
                              className="btn btn-sm btn-success"
                              title="Activate recruiter"
                            >
                              Activate
                            </button>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="info-section">
        <h3>Admin Capabilities</h3>
        <ul>
          <li>✅ View all recruiters and their subscription status</li>
          <li>✅ Upgrade recruiters from BASIC to PRO</li>
          <li>✅ Downgrade recruiters from PRO to BASIC</li>
          <li>✅ Deactivate/reactivate recruiter accounts</li>
          <li>✅ Automatic audit logging of all subscription changes</li>
        </ul>
      </div>
    </div>
  );
};
