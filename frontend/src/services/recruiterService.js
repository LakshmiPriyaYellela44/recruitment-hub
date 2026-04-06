import client from './api';

// Helper function to safely get header values (case-insensitive)
const getHeader = (headers, headerName) => {
  if (!headers) return undefined;
  
  // Try exact match first
  if (headers[headerName]) return headers[headerName];
  
  // Try lowercase
  const lowerName = headerName.toLowerCase();
  if (headers[lowerName]) return headers[lowerName];
  
  // Try to find by case-insensitive search
  for (const key in headers) {
    if (key.toLowerCase() === lowerName) {
      return headers[key];
    }
  }
  
  return undefined;
};

const recruiterService = {
  searchCandidates: (params) => client.get('/recruiters/search', { params }),
  getCandidateProfile: (id) => client.get(`/recruiters/candidate/${id}`),
  getCandidateDetail: (id) => client.get(`/recruiters/candidate/${id}`),
  sendEmail: (data) => client.post('/recruiters/send-email', data),
  getEmailTemplates: () => client.get('/recruiters/email-templates'),
  sendEmailWithTemplate: (data) => client.post('/recruiters/send-email-with-template', data),
  
  downloadCandidateResume: async (candidateId, resumeId) => {
    try {
      const response = await client.get(
        `/recruiters/candidate/${candidateId}/resume/${resumeId}/download`,
        { responseType: 'blob' }
      );
      
      // Log all response headers for debugging
      console.log(`[downloadCandidateResume] Response headers:`, response.headers);
      
      // PRIORITY 1: Get original filename from custom header (contains EXACT original filename with correct extension)
      // Using helper to handle case-insensitive header access
      let filename = getHeader(response.headers, 'x-original-filename');
      
      console.log(`[downloadCandidateResume] X-Original-Filename header: ${filename}`);
      
      // PRIORITY 2: Extract from Content-Disposition header if custom header not available
      if (!filename) {
        const contentDisposition = getHeader(response.headers, 'content-disposition');
        console.log(`[downloadCandidateResume] Content-Disposition: ${contentDisposition}`);
        
        if (contentDisposition) {
          // Try RFC 5987 filename* parameter first (properly encoded)
          const rfc5987Match = contentDisposition.match(/filename\*=UTF-8''([^;,\s]+)/i);
          if (rfc5987Match && rfc5987Match[1]) {
            try {
              filename = decodeURIComponent(rfc5987Match[1]);
              console.log(`[downloadCandidateResume] Extracted from RFC 5987 filename*: ${filename}`);
            } catch (e) {
              console.error(`[downloadCandidateResume] Error decoding RFC 5987 filename: ${e}`);
            }
          }
          
          // Fall back to standard filename parameter if RFC 5987 didn't work
          if (!filename) {
            const filenameMatch = contentDisposition.match(/filename="([^"]+)"/i);
            if (filenameMatch && filenameMatch[1]) {
              const name = filenameMatch[1];
              // Filter out .bin extension if present (server-added to prevent auto-open)
              if (name.endsWith('.bin')) {
                filename = name.replace(/\.bin$/, '');
                console.log(`[downloadCandidateResume] Removed .bin extension from filename parameter: ${filename}`);
              } else {
                filename = name;
                console.log(`[downloadCandidateResume] Extracted from filename parameter: ${filename}`);
              }
            }
          }
        }
      }
      
      // PRIORITY 3: Fallback - but DO NOT default to .pdf (preserve original file type which is in filename)
      if (!filename) {
        console.warn(`[downloadCandidateResume] WARNING: Could not extract filename from headers! Using fallback: 'resume'`);
        filename = 'resume'; // Only as absolute last resort, without any extension
        console.log(`[downloadCandidateResume] Using fallback filename: ${filename}`);
      }
      
      console.log(`[downloadCandidateResume] FINAL filename to download: ${filename}`);
      
      // Create blob with application/octet-stream type to force download
      // Explicitly set type to binary to prevent browser interpretation
      const blob = new Blob([response.data], { type: 'application/octet-stream' });
      
      // Use a more robust download method
      if (navigator.msSaveBlob) {
        // IE 10+
        navigator.msSaveBlob(blob, filename);
      } else {
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;  // The browser will use this as the actual download filename
        link.type = 'application/octet-stream';
        link.style.display = 'none';
        
        // Append to body and click
        document.body.appendChild(link);
        link.click();
        
        // Remove link and cleanup
        document.body.removeChild(link);
        
        // Clean up the blob URL after a delay
        setTimeout(() => {
          window.URL.revokeObjectURL(blobUrl);
        }, 100);
      }
      
      console.log(`[downloadCandidateResume] File downloaded successfully as: ${filename}`);
      return { success: true };
    } catch (error) {
      console.error('[downloadCandidateResume] Download failed:', error);
      throw error;
    }
  },
};

export default recruiterService;
