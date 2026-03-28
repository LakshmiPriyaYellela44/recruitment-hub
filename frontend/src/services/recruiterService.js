import client from './api';

const recruiterService = {
  searchCandidates: (params) => client.get('/recruiters/search', { params }),
  getCandidateProfile: (id) => client.get(`/recruiters/candidate/${id}`),
  getCandidateDetail: (id) => client.get(`/recruiters/candidate/${id}`),
  sendEmail: (data) => client.post('/recruiters/send-email', data),
  getEmailTemplates: () => client.get('/recruiters/email-templates'),
  sendEmailWithTemplate: (data) => client.post('/recruiters/send-email-with-template', data),
};

export default recruiterService;
