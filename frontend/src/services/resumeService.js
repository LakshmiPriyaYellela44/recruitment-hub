import client from './api';

const resumeService = {
  uploadResume: (formData) => client.post('/resumes/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getResume: (id) => client.get(`/resumes/${id}`),
  deleteResume: (id) => client.delete(`/resumes/${id}`),
  
  viewResume: async (resumeId) => {
    try {
      console.log(`Viewing resume: ${resumeId}`);
      
      // Construct the view URL
      const viewUrl = `${client.defaults.baseURL}/resumes/${resumeId}/view`;
      
      // Get auth token
      const token = localStorage.getItem('access_token');
      
      // Build query params for auth if needed
      const urlWithAuth = token ? `${viewUrl}?token=${token}` : viewUrl;
      
      // Open in new tab
      const newWindow = window.open(viewUrl, '_blank', 'noopener,noreferrer');
      
      // Add auth header by fetch with auth and creating blob
      // Actually, the browser will send Authorization header automatically
      
      return { success: true, url: viewUrl };
    } catch (error) {
      console.error('Resume view failed:', error);
      throw error;
    }
  },
  
  downloadResume: async (resumeId) => {
    try {
      const response = await client.get(`/resumes/${resumeId}/download`, {
        responseType: 'blob',
      });
      
      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'resume';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"\\]+)"?/);
        if (filenameMatch) filename = filenameMatch[1];
      }
      
      // Create blob URL and download
      const blob = new Blob([response.data]);
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      
      return { success: true };
    } catch (error) {
      console.error('Resume download failed:', error);
      throw error;
    }
  },
};

export default resumeService;
