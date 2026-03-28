import client from './api';

const authService = {
  register: (data) => client.post('/auth/register', data),
  login: (data) => client.post('/auth/login', data),
  getCurrentUser: () => client.get('/auth/me'),
  changePassword: (data) => client.post('/auth/change-password', data),
};

export default authService;
