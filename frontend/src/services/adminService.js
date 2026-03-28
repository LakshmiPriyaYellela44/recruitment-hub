import axiosInstance from './api';

const adminService = {
  /**
   * Get all recruiters with their subscription status
   */
  getRecruiters: async (limit = 20, offset = 0) => {
    try {
      const response = await axiosInstance.get('/admin/recruiters', {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching recruiters:', error);
      throw error;
    }
  },

  /**
   * Get recruiter details
   */
  getRecruiterDetails: async (recruiterId) => {
    try {
      const response = await axiosInstance.get(`/admin/recruiters/${recruiterId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching recruiter details:', error);
      throw error;
    }
  },

  /**
   * Update recruiter subscription (BASIC or PRO)
   */
  updateRecruiterSubscription: async (recruiterId, subscriptionType) => {
    try {
      const response = await axiosInstance.patch(
        `/admin/recruiters/${recruiterId}/subscription`,
        null,
        {
          params: { subscription_type: subscriptionType }
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error updating recruiter subscription:', error);
      throw error;
    }
  },

  /**
   * Deactivate a recruiter account
   */
  deactivateRecruiter: async (recruiterId) => {
    try {
      const response = await axiosInstance.post(
        `/admin/recruiters/${recruiterId}/deactivate`
      );
      return response.data;
    } catch (error) {
      console.error('Error deactivating recruiter:', error);
      throw error;
    }
  },

  /**
   * Activate a recruiter account
   */
  activateRecruiter: async (recruiterId) => {
    try {
      const response = await axiosInstance.post(
        `/admin/recruiters/${recruiterId}/activate`
      );
      return response.data;
    } catch (error) {
      console.error('Error activating recruiter:', error);
      throw error;
    }
  },

  /**
   * Get all users for admin management
   */
  getAllUsers: async (limit = 20, offset = 0) => {
    try {
      const response = await axiosInstance.get('/admin/users', {
        params: { limit, offset }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching users:', error);
      throw error;
    }
  },

  /**
   * Change a user's role
   */
  changeUserRole: async (userId, newRole) => {
    try {
      const response = await axiosInstance.patch(`/admin/users/${userId}/role`, {
        new_role: newRole
      });
      return response.data;
    } catch (error) {
      console.error('Error changing user role:', error);
      throw error;
    }
  }
};

export default adminService;
