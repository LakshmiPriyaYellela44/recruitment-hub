import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import candidateService from '../services/candidateService';
import './MyProfilePage.css';

/**
 * MyProfilePage - Candidate personal profile view
 * Displays: Basic info, Skills (from resume), Experiences (from resume), Educations (from resume), Resumes
 */
export const MyProfilePage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const response = await candidateService.getProfile();
        setProfile(response.data);
        setError('');
      } catch (err) {
        console.error('Failed to load profile:', err);
        setError(err.response?.data?.detail || 'Failed to load your profile');
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  if (loading) {
    return (
      <div className="my-profile-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="my-profile-page">
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h2>Error Loading Profile</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="my-profile-page">
        <div className="error-container">
          <h2>Profile Not Found</h2>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Calculate skill count correctly for both categorized (object) and flat (array) formats
  const skillCount = profile?.skills
    ? typeof profile.skills === 'object' && !Array.isArray(profile.skills)
      ? Object.values(profile.skills).reduce((sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0)
      : (Array.isArray(profile.skills) ? profile.skills.length : 0)
    : 0;
  
  // DEBUG: Log skills data
  console.log('DEBUG: profile.skills =', profile?.skills);
  console.log('DEBUG: skillCount =', skillCount);
  console.log('DEBUG: typeof profile.skills =', typeof profile?.skills);
  console.log('DEBUG: Is array?', Array.isArray(profile?.skills));
  console.log('DEBUG: full profile =', profile);
  const experienceCount = profile?.experiences?.length || 0;
  const educationCount = profile?.educations?.length || 0;
  const resumeCount = profile?.resumes?.length || 0;

  return (
    <div className="my-profile-page">
      {/* Header */}
      <div className="profile-header">
        <button onClick={() => navigate(-1)} className="btn-back-arrow" title="Go back">
          ← Back
        </button>
        <div className="header-content">
          <h1>My Profile</h1>
          <p className="subtitle">View and manage your professional information</p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="quick-stats">
        <div className="stat-card">
          <div className="stat-icon">📄</div>
          <div className="stat-info">
            <div className="stat-number">{resumeCount}</div>
            <div className="stat-label">Resumes</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-info">
            <div className="stat-number">{skillCount}</div>
            <div className="stat-label">Skills</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💼</div>
          <div className="stat-info">
            <div className="stat-number">{experienceCount}</div>
            <div className="stat-label">Experiences</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🎓</div>
          <div className="stat-info">
            <div className="stat-number">{educationCount}</div>
            <div className="stat-label">Educations</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📋 Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'skills' ? 'active' : ''}`}
          onClick={() => setActiveTab('skills')}
        >
          🎯 Skills ({skillCount})
        </button>
        <button
          className={`tab-button ${activeTab === 'experience' ? 'active' : ''}`}
          onClick={() => setActiveTab('experience')}
        >
          💼 Experience ({experienceCount})
        </button>
        <button
          className={`tab-button ${activeTab === 'education' ? 'active' : ''}`}
          onClick={() => setActiveTab('education')}
        >
          🎓 Education ({educationCount})
        </button>
        <button
          className={`tab-button ${activeTab === 'resumes' ? 'active' : ''}`}
          onClick={() => setActiveTab('resumes')}
        >
          📁 Resumes ({resumeCount})
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="tab-pane active">
            <div className="card">
              <h2>Basic Information</h2>
              <div className="info-grid">
                <div className="info-item">
                  <label>First Name</label>
                  <p>{profile?.first_name || 'Not provided'}</p>
                </div>
                <div className="info-item">
                  <label>Last Name</label>
                  <p>{profile?.last_name || 'Not provided'}</p>
                </div>
                <div className="info-item full-width">
                  <label>Email Address</label>
                  <p>{profile?.email}</p>
                </div>
                <div className="info-item">
                  <label>Member Since</label>
                  <p>{new Date(profile?.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>

            {/* Summary of parsed resume data */}
            <div className="card">
              <h2>Resume Data Summary</h2>
              <p className="summary-text">
                Skills, experiences, and educations are automatically extracted from your uploaded resumes.
              </p>
              {resumeCount === 0 ? (
                <div className="empty-state">
                  <p>📄 No resumes uploaded yet. Upload a resume to auto-populate your skills, experiences, and education.</p>
                  <button onClick={() => { setActiveTab('resumes'); }} className="btn-secondary">
                    Upload Resume
                  </button>
                </div>
              ) : (
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="label">Total Resumes:</span>
                    <span className="value">{resumeCount}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Skills Identified:</span>
                    <span className="value">{skillCount}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Work Experiences:</span>
                    <span className="value">{experienceCount}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Education History:</span>
                    <span className="value">{educationCount}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === 'skills' && (
          <div className="tab-pane active">
            <div className="card">
              <h2>Your Skills</h2>
              {skillCount > 0 ? (
                typeof profile.skills === 'object' && !Array.isArray(profile.skills) ? (
                  // Categorized skills
                  <div className="skills-container">
                    <div className="skills-info">
                      <p className="info-text">
                        ✨ {skillCount} skills identified from your resumes (organized by category)
                      </p>
                      <div className="category-legend">
                        {Object.keys(profile.skills).filter(cat => profile.skills[cat]?.length > 0).map(cat => (
                          <span key={cat} className="legend-item">{cat.replace(/_/g, ' ')}: {profile.skills[cat].length}</span>
                        ))}
                      </div>
                    </div>
                    <div className="skills-by-category">
                      {Object.entries(profile.skills).map(([category, skillList]) => 
                        skillList && skillList.length > 0 && (
                          <div key={category} className="category-section">
                            <h3 className="category-title">{category.replace(/_/g, ' ')}</h3>
                            <div className="skills-grid">
                              {skillList.map((skill, idx) => (
                                <div key={idx} className="skill-badge">
                                  <span className="skill-name">{skill.name || skill}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                ) : (
                  // Flat skills (backwards compatibility)
                  <div className="skills-container">
                    <div className="skills-info">
                      <p className="info-text">
                        ✨ {skillCount} skills identified from your resumes
                      </p>
                    </div>
                    <div className="skills-grid">
                      {profile.skills.map((skill) => (
                        <div key={skill.id} className="skill-badge">
                          <span className="skill-name">{skill.name}</span>
                          {skill.category && <span className="skill-category">{skill.category}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              ) : (
                <div className="empty-state">
                  <p>No skills identified yet. Upload a resume to extract skills automatically.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Experience Tab */}
        {activeTab === 'experience' && (
          <div className="tab-pane active">
            <div className="card">
              <h2>Work Experience</h2>
              {experienceCount > 0 ? (
                <div className="timeline">
                  <div className="timeline-info">
                    <p className="info-text">
                      📍 {experienceCount} work experience(s) found in your resumes
                    </p>
                  </div>
                  {profile.experiences.map((exp, index) => (
                    <div key={exp.id} className={`timeline-item ${index % 2 === 0 ? 'left' : 'right'}`}>
                      <div className="timeline-dot"></div>
                      <div className="timeline-content">
                        <h3>{exp.job_title}</h3>
                        <p className="company">{exp.company_name}</p>
                        {exp.location && <p className="location">📍 {exp.location}</p>}
                        {exp.years && <p className="years">⏱️ {exp.years} years</p>}
                        {exp.description && <p className="description">{exp.description}</p>}
                        {exp.start_date && (
                          <p className="dates">
                            {new Date(exp.start_date).toLocaleDateString()} 
                            {exp.end_date ? ` - ${new Date(exp.end_date).toLocaleDateString()}` : ' - Present'}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>No work experience found. Upload a resume to extract experience details automatically.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Education Tab */}
        {activeTab === 'education' && (
          <div className="tab-pane active">
            <div className="card">
              <h2>Education</h2>
              {educationCount > 0 ? (
                <div className="education-list">
                  <div className="education-info">
                    <p className="info-text">
                      🎓 {educationCount} education record(s) from your resumes
                    </p>
                  </div>
                  {profile.educations.map((edu) => (
                    <div key={edu.id} className="education-item">
                      <div className="education-header">
                        <h3>{edu.degree}</h3>
                        {edu.field_of_study && (
                          <span className="field-badge">{edu.field_of_study}</span>
                        )}
                      </div>
                      <p className="institution">{edu.institution}</p>
                      {edu.start_date && (
                        <p className="dates">
                          📅 {new Date(edu.start_date).toLocaleDateString()}
                          {edu.end_date ? ` - ${new Date(edu.end_date).toLocaleDateString()}` : ''}
                        </p>
                      )}
                      {edu.description && <p className="description">{edu.description}</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>No education history found. Upload a resume to extract education details automatically.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Resumes Tab */}
        {activeTab === 'resumes' && (
          <div className="tab-pane active">
            <div className="card">
              <h2>Your Resumes</h2>
              {resumeCount > 0 ? (
                <div className="resumes-list">
                  {profile.resumes.map((resume) => (
                    <div key={resume.id} className={`resume-card status-${resume.status.toLowerCase()}`}>
                      <div className="resume-header">
                        <div className="resume-title">
                          <span className="file-icon">📄</span>
                          <span className="file-name">{resume.file_name}</span>
                        </div>
                        <span className={`status-badge ${resume.status.toLowerCase()}`}>
                          {resume.status}
                        </span>
                      </div>
                      <div className="resume-meta">
                        <span>📤 Uploaded: {new Date(resume.created_at).toLocaleDateString()}</span>
                        <span>📝 File type: {resume.file_type}</span>
                      </div>
                      {resume.status === 'PARSED' && (
                        <div className="resume-success-note">
                          ✅ Resume parsed successfully - Skills, experiences, and education extracted
                        </div>
                      )}
                      {resume.status === 'PARSING' && (
                        <div className="resume-processing-note">
                          ⏳ Processing your resume... This may take a few moments
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>No resumes uploaded yet.</p>
                </div>
              )}
              <button 
                onClick={() => navigate('/dashboard')} 
                className="btn-secondary mt-4"
              >
                ➕ Upload New Resume
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyProfilePage;
