import client from './api';

const candidateService = {
  getProfile: () => client.get('/candidates/me'),
};

export default candidateService;
