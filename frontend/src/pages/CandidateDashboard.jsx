import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import candidateService from '../services/candidateService';
import resumeService from '../services/resumeService';

export const CandidateDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('profile');

  const loadProfile = async () => {
    try {
      const response = await candidateService.getProfile();
      setProfile(response.data);
    } catch (err) {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f1419] via-[#1a1f26] to-[#0f1419]">
      <div className="max-w-6xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#f5f7fa] mb-1 sm:mb-2">
            Hi, {profile?.first_name}!
          </h1>
          <p className="text-xs sm:text-sm text-[#8b95a5]">Upload and manage your resume</p>
        </div>

        {error && (
          <div className="mb-4 p-3 sm:p-4 bg-[#3a0a0a] border border-[#5a1a1a] text-[#ff8a94] rounded-lg text-xs sm:text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
          <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg shadow p-4 sm:p-6 cursor-pointer transition-all duration-300 hover:border-[#8B2635] hover:shadow-lg hover:bg-[#222a33]">
            <div className="text-xs sm:text-sm text-[#f5f7fa] font-semibold uppercase tracking-wide">Resumes</div>
            <div className="text-xl sm:text-2xl font-bold text-[#8B2635] mt-2">
              {profile?.resumes?.length || 0}
            </div>
          </div>
          <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg shadow p-4 sm:p-6 cursor-pointer transition-all duration-300 hover:border-[#8B2635] hover:shadow-lg hover:bg-[#222a33]">
            <div className="text-xs sm:text-sm text-[#f5f7fa] font-semibold uppercase tracking-wide">Skills</div>
            <div className="text-xl sm:text-2xl font-bold text-[#8B2635] mt-2">
              {(() => {
                if (!profile?.skills) return 0;
                if (Array.isArray(profile.skills)) return profile.skills.length;
                // Skills is an object (categorized), sum all skills
                return Object.values(profile.skills).reduce((sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0);
              })()}
            </div>
          </div>
          <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg shadow p-4 sm:p-6 cursor-pointer transition-all duration-300 hover:border-[#8B2635] hover:shadow-lg hover:bg-[#222a33]">
            <div className="text-xs sm:text-sm text-[#f5f7fa] font-semibold uppercase tracking-wide">Experiences</div>
            <div className="text-xl sm:text-2xl font-bold text-[#8B2635] mt-2">
              {profile?.experiences?.length || 0}
            </div>
          </div>
        </div>

        <div className="flex gap-2 sm:gap-4 mb-6 border-b border-[#2d333f] overflow-x-auto">
          <button
            onClick={() => setActiveTab('profile')}
            className={`px-3 sm:px-6 py-2 sm:py-3 rounded-t-lg font-semibold transition border-b-2 text-xs sm:text-sm whitespace-nowrap ${
              activeTab === 'profile'
                ? 'bg-[#1a1f26] text-[#C41E3A] border-b-[#C41E3A]'
                : 'bg-[#0f1419] text-[#8b95a5] border-b-transparent hover:text-[#f5f7fa]'
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setActiveTab('resumes')}
            className={`px-3 sm:px-6 py-2 sm:py-3 rounded-t-lg font-semibold transition border-b-2 text-xs sm:text-sm whitespace-nowrap ${
              activeTab === 'resumes'
                ? 'bg-[#1a1f26] text-[#8B2635] border-b-[#8B2635]'
                : 'bg-[#0f1419] text-[#8b95a5] border-b-transparent hover:text-[#f5f7fa]'
            }`}
          >
            Resumes
          </button>
      </div>

      {activeTab === 'profile' && (
        <div className="bg-[#1a1f26] rounded-lg shadow p-4 sm:p-6 lg:p-8 border border-[#2d333f]">
          <h2 className="text-xl sm:text-2xl font-bold text-[#f5f7fa] mb-4 sm:mb-6">Your Profile</h2>
          
          {/* Skills Section */}
          <div className="mb-6 sm:mb-8">
            <h3 className="font-bold text-lg sm:text-xl text-[#f5f7fa] mb-3 sm:mb-4">Skills</h3>
            {(() => {
              // Calculate skill count (handle both object and array formats)
              let skillCount = 0;
              let skillsToDisplay = [];
              
              if (profile?.skills) {
                if (Array.isArray(profile.skills)) {
                  // Old format: array of skills
                  skillCount = profile.skills.length;
                  skillsToDisplay = profile.skills;
                } else if (typeof profile.skills === 'object') {
                  // New format: object with categories
                  Object.values(profile.skills).forEach(arr => {
                    if (Array.isArray(arr)) {
                      skillCount += arr.length;
                      skillsToDisplay = [...skillsToDisplay, ...arr];
                    }
                  });
                }
              }
              
              return skillCount > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {skillsToDisplay.map((skill, idx) => (
                    <span
                      key={skill.id || idx}
                      className="px-4 py-2 bg-[#5C1520] text-[#C41E3A] rounded-full text-sm font-medium border border-[#6B1D2A]"
                    >
                      {skill.name || skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[#8b95a5]">No skills yet. Upload a resume to auto-populate!</p>
              );
            })()}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            <div>
              <h3 className="font-bold text-lg sm:text-xl text-[#f5f7fa] mb-3 sm:mb-4">Experiences</h3>
              {profile?.experiences?.length > 0 ? (
                <div className="space-y-4">
                  {profile.experiences.map((exp) => (
                    <div key={exp.id} className="border-l-4 border-[#8B2635] pl-4">
                      <h4 className="font-bold text-[#f5f7fa]">{exp.job_title}</h4>
                      <p className="text-sm text-[#8b95a5]">{exp.company_name}</p>
                      {exp.years && <p className="text-xs text-[#6d7a88]">{exp.years} years</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#8b95a5]">No experiences yet. Upload a resume to auto-populate!</p>
              )}
            </div>
            <div>
              <h3 className="font-bold text-lg sm:text-xl text-[#f5f7fa] mb-3 sm:mb-4">Education</h3>
              {profile?.educations?.length > 0 ? (
                <div className="space-y-4">
                  {profile.educations.map((edu) => (
                    <div key={edu.id} className="border-l-4 border-[#4ade80] pl-4">
                      <h4 className="font-bold text-[#f5f7fa]">{edu.degree}</h4>
                      <p className="text-sm text-[#8b95a5]">{edu.institution}</p>
                      {edu.field_of_study && (
                        <p className="text-xs text-[#6d7a88]">{edu.field_of_study}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#8b95a5]">No education yet. Upload a resume to auto-populate!</p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'resumes' && (
        <ResumesTab profile={profile} onUpdate={loadProfile} />
      )}
    </div>
  </div>
  );
};

const ResumesTab = ({ profile, onUpdate }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'
  const [deleting, setDeleting] = useState(null);
  const [downloading, setDownloading] = useState(null); // Track which resume is being downloaded
  const [resumes, setResumes] = useState(profile?.resumes || []);
  const [selectedResume, setSelectedResume] = useState(null); // Track selected (latest) resume

  // Update selected resume when profile resumes change (initialization or after delete)
  useEffect(() => {
    if (profile?.resumes && profile.resumes.length > 0) {
      // Find the latest resume (marked with is_latest or first one if is_latest not available)
      const latestResume = profile.resumes.find(r => r.is_latest) || profile.resumes[0];
      setSelectedResume(latestResume);
      setResumes(profile.resumes);
    } else {
      setSelectedResume(null);
      setResumes([]);
    }
  }, [profile?.resumes]);

  // Poll for resume parsing completion
  const waitForResumeParsing = async (resumeId, maxAttempts = 30) => {
    let attempts = 0;
    const pollInterval = 2000; // Poll every 2 seconds
    
    while (attempts < maxAttempts) {
      try {
        const response = await resumeService.getResume(resumeId);
        const resume = response.data;
        
        if (resume.status === 'PARSED') {
          return true; // Parsing complete
        }
        
        if (resume.status === 'FAILED') {
          throw new Error('Resume parsing failed');
        }
        
        // Still processing, wait and retry
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        attempts++;
      } catch (err) {
        console.error('Error checking resume status:', err);
        // Continue polling on error
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        attempts++;
      }
    }
    
    throw new Error('Resume parsing took too long');
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const uploadResponse = await resumeService.uploadResume(formData);
      const resumeId = uploadResponse.data.id;
      
      setMessage('Resume uploaded! Processing...');
      setMessageType('success');
      
      // Wait for parsing to complete
      await waitForResumeParsing(resumeId);
      
      setMessage('Resume parsed successfully!');
      setMessageType('success');
      setFile(null);
      setTimeout(() => setMessage(''), 5000);
      
      // Add slight delay to ensure backend has completed all sync operations
      // This ensures database is fully updated before we query for the new data
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Reload profile to show the newly parsed skills and experiences
      // The profile endpoint will aggregate all skills/experiences/educations from parsed resumes
      if (onUpdate) {
        console.log('[UPLOAD_SUCCESS] Calling onUpdate to refresh profile with newly parsed data');
        await onUpdate();
        console.log('[UPLOAD_SUCCESS] Profile refreshed successfully');
      }
    } catch (err) {
      console.error('[UPLOAD_ERROR] Upload/parsing error:', err);
      
      // Extract detailed error message from API response if available
      let errorMessage = 'Failed to upload resume';
      
      if (err.response?.data?.detail) {
        // API returned validation error
        errorMessage = err.response.data.detail;
      } else if (err.response?.status === 422) {
        // Validation error - bad file
        errorMessage = 'Resume validation failed. Please upload a valid PDF or Word document with actual content.';
      } else if (err.message === 'Resume parsing took too long') {
        errorMessage = 'Resume is being processed in the background. Please refresh the page in a moment.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setMessage(errorMessage);
      setMessageType('error');
      setFile(null); // Clear the selected file so user can try again
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (resumeId, fileName) => {
    setDownloading(resumeId);
    try {
      await resumeService.downloadResume(resumeId);
      console.log(`Resume ${fileName} downloaded`);
    } catch (err) {
      console.error('Failed to download resume:', err);
      setMessage(`Failed to download resume: ${err.message || 'Unknown error'}`);
      setMessageType('error');
    } finally {
      setDownloading(null);
    }
  };

  const handleDelete = async (resumeId) => {
    if (!window.confirm('Are you sure you want to delete this resume? This action cannot be undone.')) {
      return;
    }

    const resumeBeingDeleted = resumes.find(r => r.id === resumeId);
    const isDeletedLatest = resumeBeingDeleted?.is_latest;
    
    setDeleting(resumeId);
    
    // Optimistic UI update - immediately remove from the UI
    const updatedResumes = resumes.filter(r => r.id !== resumeId);
    setResumes(updatedResumes);
    
    // If we deleted the latest, update selected to new latest
    if (isDeletedLatest) {
      const newLatest = updatedResumes.length > 0 ? updatedResumes[0] : null;
      setSelectedResume(newLatest);
      console.log(`[DELETE_LATEST] Latest resume deleted. New latest: ${newLatest?.file_name || 'None'}`);
    } else if (selectedResume?.id === resumeId) {
      // If deleted resume was selected but not latest, just clear selection
      setSelectedResume(null);
    }
    
    try {
      await resumeService.deleteResume(resumeId);
      setMessage('Resume deleted successfully!');
      setMessageType('success');
      setTimeout(() => setMessage(''), 3000);
      
      // Reload profile to update counts and derived data
      if (onUpdate) {
        await onUpdate();
      }
    } catch (err) {
      console.error('Delete error:', err);
      setMessage(`Failed to delete resume: ${err.response?.data?.detail || err.message || 'Unknown error'}`);
      setMessageType('error');
      
      // Restore the resume if deletion failed
      if (profile?.resumes) {
        setResumes(profile.resumes);
        const latestResume = profile.resumes.find(r => r.is_latest) || profile.resumes[0];
        setSelectedResume(latestResume);
      }
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="bg-[#1a1f26] rounded-lg shadow p-4 sm:p-6 lg:p-8 border border-[#2d333f]">
      <h2 className="text-xl sm:text-2xl font-bold text-[#f5f7fa] mb-4 sm:mb-6">Your Resumes</h2>

      <form onSubmit={handleUpload} className="mb-6 sm:mb-8">
        <div className="relative">
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="hidden"
            id="resume-upload"
            disabled={uploading}
          />
          <label
            htmlFor="resume-upload"
            className="block p-4 sm:p-5 border-2 border-dashed border-[#8B2635] rounded-lg bg-gradient-to-br from-[#5C1520] to-[#3D0F17] bg-opacity-40 cursor-pointer transition-all duration-300 hover:border-[#C41E3A] hover:bg-opacity-60 hover:shadow-lg"
          >
            <div className="flex flex-col items-center justify-center">
              <div className="w-10 sm:w-12 h-10 sm:h-12 bg-gradient-to-br from-[#8B2635] to-[#6B1D2A] rounded-full flex items-center justify-center mb-2 sm:mb-3 shadow-lg">
                <svg className="w-5 sm:w-6 h-5 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <h3 className="text-base sm:text-lg font-bold text-[#f5f7fa] text-center mb-1">
                Drop your resume here
              </h3>
              <p className="text-xs text-[#8b95a5] text-center mb-2">
                or click to browse
              </p>
              <p className="text-xs text-[#6d7a88] text-center">
                Supported formats: PDF, DOCX • Max 10MB
              </p>
            </div>
          </label>
          {file && (
            <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-[#0a5a0a] bg-opacity-30 border border-[#4ade80] rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 bg-[#4ade80] rounded flex items-center justify-center">
                  <svg className="w-5 h-5 text-[#0a5a0a]" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.707 5.293a1 1 0 010 1.414L5.414 10l3.293 3.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm font-semibold text-[#4ade80] truncate">{file.name}</p>
                  <p className="text-xs text-[#8b95a5]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="text-[#4ade80] hover:text-[#C41E3A] transition"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          )}
        </div>

        <div className="flex gap-2 sm:gap-3 mt-4 sm:mt-6">
          <button
            type="submit"
            disabled={!file || uploading}
            className="flex-1 px-4 sm:px-6 py-2.5 sm:py-3 bg-gradient-to-r from-[#C41E3A] to-[#A91930] hover:from-[#A91930] hover:to-[#8B1425] disabled:from-[#3d4551] disabled:to-[#3d4551] text-white rounded-lg font-semibold transition-all duration-300 text-xs sm:text-sm shadow-lg hover:shadow-xl disabled:shadow-none"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Uploading...
              </span>
            ) : (
              'Upload Resume'
            )}
          </button>
        </div>

        {message && (
          <p className={`mt-4 sm:mt-5 text-xs sm:text-sm font-medium p-3 sm:p-4 rounded-lg ${
            messageType === 'success' 
              ? 'bg-[#0a5a0a] bg-opacity-40 border border-[#4ade80] text-[#4ade80]' 
              : 'bg-[#5a0a17] bg-opacity-40 border border-[#C41E3A] text-[#C41E3A]'
          }`}>
            {message}
          </p>
        )}
      </form>

      <div className="overflow-x-auto">
        {resumes && resumes.length > 0 ? (
          <table className="w-full border-collapse text-xs sm:text-sm">
            <thead>
              <tr className="bg-[#0f1419] border-b-2 border-[#2d333f]">
                <th className="px-3 sm:px-4 py-2 sm:py-3 text-left font-semibold text-[#f5f7fa]">File Name</th>
                <th className="px-3 sm:px-4 py-2 sm:py-3 text-left font-semibold text-[#f5f7fa]">Type</th>
                <th className="px-3 sm:px-4 py-2 sm:py-3 text-left font-semibold text-[#f5f7fa]">Status</th>
                <th className="px-3 sm:px-4 py-2 sm:py-3 text-left font-semibold text-[#f5f7fa]">Uploaded</th>
                <th className="px-3 sm:px-4 py-2 sm:py-3 text-center font-semibold text-[#f5f7fa]">Action</th>
              </tr>
            </thead>
            <tbody>
              {resumes.map((resume, idx) => (
                <tr key={resume.id} className={`border-b border-[#2d333f] ${
                  resume.is_latest ? 'bg-[#5a0a17] bg-opacity-30' : idx % 2 === 0 ? 'bg-[#1a1f26]' : 'bg-[#0f1419]'
                }`}>
                  <td className="px-3 sm:px-4 py-2 sm:py-3 text-[#f5f7fa]">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{resume.file_name}</span>
                      {resume.is_latest && (
                        <span className="px-2 py-1 bg-[#C41E3A] text-white text-xs font-semibold rounded whitespace-nowrap">Latest</span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 sm:px-4 py-2 sm:py-3 text-[#8b95a5]">{resume.file_type.toUpperCase()}</td>
                  <td className="px-3 sm:px-4 py-2 sm:py-3">
                    <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-semibold ${
                      resume.status === 'UPLOADED' ? 'bg-[#5a0a17] text-[#C41E3A]' :
                      resume.status === 'PARSED' ? 'bg-[#0a5a0a] text-[#4ade80]' :
                      'bg-[#2d333f] text-[#8b95a5]'
                    }`}>
                      {resume.status}
                    </span>
                  </td>
                  <td className="px-3 sm:px-4 py-2 sm:py-3 text-[#8b95a5] text-xs sm:text-sm">
                    {new Date(resume.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-3 sm:px-4 py-2 sm:py-3 text-center">
                    <div className="flex gap-1 sm:gap-2 justify-center">
                      <button
                        onClick={() => handleDownload(resume.id, resume.file_name)}
                        disabled={downloading === resume.id}
                        className="p-1.5 sm:p-2 bg-[#0a5a0a] hover:bg-[#167a16] disabled:bg-[#3d4551] text-[#4ade80] rounded-lg font-medium transition text-xs sm:text-sm"
                        title="Download resume"
                      >
                        {downloading === resume.id ? (
                          <span className="inline-block animate-spin">
                            <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </span>
                        ) : (
                          <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(resume.id)}
                        disabled={deleting === resume.id}
                        className="p-1.5 sm:p-2 bg-[#5a0a17] hover:bg-[#C41E3A] disabled:bg-[#3d4551] text-[#C41E3A] rounded-lg font-medium transition text-xs sm:text-sm"
                        title="Delete resume"
                      >
                        {deleting === resume.id ? (
                          <span className="inline-block animate-spin">
                            <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </span>
                        ) : (
                          <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3H4v2h16V7h-3.5z" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-8 text-[#6b7280]">
            <p>No resumes uploaded yet. Upload your first resume to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
};

const UpgradeModal = ({ onClose, onUpgrade }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
    <div className="bg-white rounded-lg p-8 max-w-md">
      <h2 className="text-2xl font-bold mb-4">Upgrade to PRO</h2>
      <p className="text-gray-600 mb-6">
        Get access to premium features and advanced recruitment tools.
      </p>
      <div className="space-y-2 mb-6">
        <p className="text-sm">✓ Priority in search results</p>
        <p className="text-sm">✓ Direct messaging with recruiters</p>
        <p className="text-sm">✓ Advanced profile analytics</p>
      </div>
      <div className="flex gap-4">
        <button
          onClick={onClose}
          className="flex-1 px-4 py-2 border border-gray-300 rounded font-medium hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={onUpgrade}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
        >
          Upgrade
        </button>
      </div>
    </div>
  </div>
);
