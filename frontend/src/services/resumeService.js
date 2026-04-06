import client from './api';

const resumeService = {
  uploadResume: (formData) => client.post('/resumes/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getResume: (id) => client.get(`/resumes/${id}`),
  deleteResume: (id) => client.delete(`/resumes/${id}`),
  
  downloadResume: async (resumeId) => {
    try {
      console.log(`[ResumeSvc] Downloading resume: ${resumeId}`);
      
      const response = await client.get(`/resumes/${resumeId}/download`, {
        responseType: 'blob',
      });
      
      const contentType = response.headers['content-type'];
      const disposition = response.headers['content-disposition'];
      
      console.log(`[ResumeSvc] Download response:
        ContentType: ${contentType}
        Disposition: ${disposition}
        Status: ${response.status}`);
      
      // Get filename from Content-Disposition header or use default
      let filename = 'resume';
      if (disposition) {
        const filenameMatch = disposition.match(/filename="?([^"\\]+)"?/);
        if (filenameMatch) filename = filenameMatch[1];
      }
      
      console.log(`[ResumeSvc] Downloading as: ${filename}`);
      
      // Create blob URL and download
      const blob = new Blob([response.data], { type: contentType });
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      
      console.log('[ResumeSvc] Download completed');
      return { success: true };
    } catch (error) {
      console.error('[ResumeSvc] Resume download failed:', error);
      throw error;
    }
  },
};

export default resumeService;
