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
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          Welcome, {profile?.first_name}! 👋
        </h1>
        <p className="text-gray-600">Manage your profile and apply for jobs</p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Resumes</div>
          <div className="text-2xl font-bold text-gray-800 mt-2">
            {profile?.resumes?.length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Skills</div>
          <div className="text-2xl font-bold text-gray-800 mt-2">
            {profile?.skills?.length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Experiences</div>
          <div className="text-2xl font-bold text-gray-800 mt-2">
            {profile?.experiences?.length || 0}
          </div>
        </div>
      </div>

      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-6 py-2 rounded font-medium transition ${
            activeTab === 'profile'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
        >
          Profile
        </button>
        <button
          onClick={() => setActiveTab('resumes')}
          className={`px-6 py-2 rounded font-medium transition ${
            activeTab === 'resumes'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
        >
          Resumes
        </button>
      </div>

      {activeTab === 'profile' && (
        <div className="bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold mb-6">Your Profile</h2>
          
          {/* Skills Section */}
          <div className="mb-8">
            <h3 className="font-bold text-lg mb-4">Skills</h3>
            {profile?.skills?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((skill) => (
                  <span
                    key={skill.id}
                    className="px-4 py-2 bg-purple-100 text-purple-800 rounded-full text-sm font-medium"
                  >
                    {skill.name}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No skills yet. Upload a resume to auto-populate!</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-bold text-lg mb-4">Experiences</h3>
              {profile?.experiences?.length > 0 ? (
                <div className="space-y-4">
                  {profile.experiences.map((exp) => (
                    <div key={exp.id} className="border-l-4 border-blue-500 pl-4">
                      <h4 className="font-bold">{exp.job_title}</h4>
                      <p className="text-sm text-gray-600">{exp.company_name}</p>
                      {exp.years && <p className="text-xs text-gray-500">{exp.years} years</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No experiences yet. Upload a resume to auto-populate!</p>
              )}
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4">Education</h3>
              {profile?.educations?.length > 0 ? (
                <div className="space-y-4">
                  {profile.educations.map((edu) => (
                    <div key={edu.id} className="border-l-4 border-green-500 pl-4">
                      <h4 className="font-bold">{edu.degree}</h4>
                      <p className="text-sm text-gray-600">{edu.institution}</p>
                      {edu.field_of_study && (
                        <p className="text-xs text-gray-500">{edu.field_of_study}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No education yet. Upload a resume to auto-populate!</p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'resumes' && (
        <ResumesTab profile={profile} onUpdate={loadProfile} />
      )}
    </div>
  );
};

const ResumesTab = ({ profile, onUpdate }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'
  const [deleting, setDeleting] = useState(null);
  const [viewing, setViewing] = useState(null); // Track which resume is being viewed
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
      if (err.message === 'Resume parsing took too long') {
        setMessage('Resume is being processed in the background. Please refresh the page in a moment.');
      } else {
        setMessage(err.message || 'Failed to upload resume');
      }
      setMessageType('error');
    } finally {
      setUploading(false);
    }
  };

  const handleView = async (resumeId, fileName) => {
    setViewing(resumeId);
    try {
      await resumeService.viewResume(resumeId);
      console.log(`Resume ${fileName} opened in new tab`);
    } catch (err) {
      console.error('Failed to view resume:', err);
      setMessage(`Failed to view resume: ${err.message || 'Unknown error'}`);
      setMessageType('error');
    } finally {
      setViewing(null);
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
    <div className="bg-white rounded-lg shadow p-8">
      <h2 className="text-2xl font-bold mb-6">Your Resumes</h2>

      <form onSubmit={handleUpload} className="mb-8 p-6 border-2 border-dashed border-blue-300 rounded">
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mb-4"
        />
        <button
          type="submit"
          disabled={!file || uploading}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded font-medium"
        >
          {uploading ? 'Uploading...' : 'Upload Resume'}
        </button>
        {message && (
          <p className={`mt-2 text-sm font-medium ${
            messageType === 'success' ? 'text-green-600' : 'text-red-600'
          }`}>
            {message}
          </p>
        )}
      </form>

      <div className="overflow-x-auto">
        {resumes && resumes.length > 0 ? (
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100 border-b">
                <th className="px-4 py-3 text-left font-semibold text-gray-800">File Name</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-800">Type</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-800">Status</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-800">Uploaded</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-800">Action</th>
              </tr>
            </thead>
            <tbody>
              {resumes.map((resume) => (
                <tr key={resume.id} className={`border-b ${resume.is_latest ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'}`}>
                  <td className="px-4 py-3 text-gray-800">
                    <div className="flex items-center gap-2">
                      <span>{resume.file_name}</span>
                      {resume.is_latest && (
                        <span className="px-2 py-1 bg-blue-500 text-white text-xs font-semibold rounded">Latest</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{resume.file_type.toUpperCase()}</td>
                  <td className="px-4 py-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      resume.status === 'UPLOADED' ? 'bg-green-100 text-green-800' :
                      resume.status === 'PARSED' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {resume.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-sm">
                    {new Date(resume.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={() => handleView(resume.id, resume.file_name)}
                        disabled={viewing === resume.id}
                        className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white text-sm rounded font-medium transition"
                      >
                        {viewing === resume.id ? 'Opening...' : 'View'}
                      </button>
                      <button
                        onClick={() => handleDelete(resume.id)}
                        disabled={deleting === resume.id}
                        className="px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white text-sm rounded font-medium transition"
                      >
                        {deleting === resume.id ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-8 text-gray-500">
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
