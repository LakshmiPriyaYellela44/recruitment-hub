import client from './api';

const authService = {
  register: (data) => client.post('/auth/register', data),
  login: (data) => client.post('/auth/login', data),
  getCurrentUser: () => client.get('/auth/me'),
  changePassword: (data) => client.post('/auth/change-password', data),
  // Forgot Password - just need email and new password (no current password)
  forgotPassword: (email, newPassword) => 
    client.post('/auth/forgot-password', { 
      email, 
      new_password: newPassword 
    }),
};

export default authService;
