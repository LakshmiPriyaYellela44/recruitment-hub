import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import recruiterService from '../services/recruiterService';
import { useAuth } from '../context/AuthContext';
import EmailSendLive from '../components/EmailSendLive';
import './CandidateProfilePage.css';

export const CandidateProfilePage = () => {
  const { candidateId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    const fetchCandidateProfile = async () => {
      try {
        const response = await recruiterService.getCandidateProfile(candidateId);
        console.log('[CandidateProfilePage] API Response:', response.data);
        console.log('[CandidateProfilePage] Resumes:', response.data?.resumes);
        setCandidate(response.data);
        setLoading(false);
      } catch (err) {
        console.error('[CandidateProfilePage] Error:', err);
        setError(err.response?.data?.detail || 'Failed to load candidate profile');
        setLoading(false);
      }
    };

    fetchCandidateProfile();
  }, [candidateId]);

  const handleGoBack = () => {
    // If opened in new tab, close it. Otherwise navigate back
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      window.close();
    }
  };

  const handleDownloadResume = async (resumeId, fileName) => {
    setDownloading(resumeId);
    try {
      await recruiterService.downloadCandidateResume(candidateId, resumeId);
      console.log(`Resume ${fileName} downloaded successfully`);
    } catch (err) {
      console.error('Failed to download resume:', err);
      alert(`Failed to download resume: ${err.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setDownloading(null);
    }
  };

  if (loading) {
    return (
      <div className="candidate-profile-page">
        <div className="loading">Loading candidate profile...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="candidate-profile-page">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={handleGoBack} className="btn-back">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="candidate-profile-page">
        <div className="error-container">
          <h2>Candidate Not Found</h2>
          <button onClick={handleGoBack} className="btn-back">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const isPro = user?.subscription_type === 'PRO';

  return (
    <div className="candidate-profile-page">
      <div className="profile-header">
        <button onClick={handleGoBack} className="btn-back-header">
          ← Back
        </button>
        <h1>{candidate.first_name} {candidate.last_name}</h1>
      </div>

      <div className="profile-container">
        {/* Left column - Candidate info */}
        <div className="profile-left">
          <div className="section candidate-info">
            <h2>Basic Information</h2>
            <div className="info-item">
              <label>Email:</label>
              <p>{candidate.email}</p>
            </div>
            <div className="info-item">
              <label>Phone:</label>
              <p>{candidate.phone_number || 'Not provided'}</p>
            </div>
            <div className="info-item">
              <label>Name:</label>
              <p>{candidate.first_name} {candidate.last_name}</p>
            </div>
            <div className="info-item">
              <label>Member Since:</label>
              <p>{new Date(candidate.created_at).toLocaleDateString()}</p>
            </div>
          </div>

          {/* Skills */}
          {candidate.skills && candidate.skills.length > 0 && (
            <div className="section skills-section">
              <h2>Skills</h2>
              <div className="skills-list">
                {candidate.skills.map((skill) => (
                  <span key={skill.id} className="skill-tag">
                    {skill.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Experiences */}
          {candidate.experiences && candidate.experiences.length > 0 && (
            <div className="section experiences-section">
              <h2>Experience</h2>
              {candidate.experiences.map((exp) => (
                <div key={exp.id} className="experience-item">
                  <h3>{exp.job_title}</h3>
                  <p className="company">{exp.company_name}</p>
                  {exp.years && <p className="years">{exp.years} years</p>}
                </div>
              ))}
            </div>
          )}

          {/* Education */}
          {candidate.educations && candidate.educations.length > 0 && (
            <div className="section educations-section">
              <h2>Education</h2>
              {candidate.educations.map((edu) => (
                <div key={edu.id} className="education-item">
                  <h3>{edu.degree}</h3>
                  <p className="institution">{edu.institution}</p>
                  {edu.field_of_study && <p className="field">{edu.field_of_study}</p>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right column - Email template section */}
        <div className="profile-right">
          <div className="section email-section">
            <h2>📧 Contact Candidate</h2>

            {!isPro && (
              <div className="upgrade-notice">
                <div className="upgrade-icon">🔒</div>
                <p>Email feature is only available for <strong>PRO</strong> subscribers</p>
                <p className="upgrade-hint">Upgrade your plan to send messages to candidates</p>
              </div>
            )}

            {isPro && (
              <div className="candidate-contact-info">
                <div className="contact-item">
                  <span className="contact-label">Email:</span>
                  <span className="contact-value">{candidate.email}</span>
                </div>
                <button
                  onClick={() => setShowEmailModal(true)}
                  className="btn-send-email-modal"
                >
                  📧 Send Email
                </button>
                {showEmailModal && (
                  (() => {
                    // Extract email from latest resume parsed data, fall back to candidate.email
                    const latestResume = candidate.resumes && candidate.resumes.length > 0 ? candidate.resumes[0] : null;
                    const parsedEmail = latestResume?.parsed_data?.email || candidate.email;
                    
                    if (!parsedEmail) {
                      return (
                        <div className="email-error-message">
                          <p>⚠️ No email found for this candidate. Please ensure candidate has a valid email.</p>
                        </div>
                      );
                    }
                    
                    return (
                      <EmailSendLive
                        candidateId={candidateId}
                        candidateName={`${candidate.first_name} ${candidate.last_name}`}
                        candidateEmail={parsedEmail}
                        token={localStorage.getItem('access_token')}
                        onClose={() => setShowEmailModal(false)}
                        onSuccess={() => {
                          setShowEmailModal(false);
                        }}
                        onError={(err) => {
                          console.error('Email sending error:', err);
                        }}
                      />
                    );
                  })()
                )}
              </div>
            )}
          </div>

          {/* Resumes */}
          {candidate.resumes && candidate.resumes.length > 0 && (
            <div className="section resumes-section">
              <h2>📄 Resume</h2>
              <div className="resumes-list">
                {candidate.resumes.map((resume) => (
                  <div key={resume.id} className="resume-item">
                    <div className="resume-info">
                      <p className="resume-name">{resume.file_name}</p>
                      <span className={`status ${resume.status.toLowerCase()}`}>
                        {resume.status}
                      </span>
                    </div>
                    <div className="resume-actions">
                      <button
                        onClick={() => !isPro ? null : handleDownloadResume(resume.id, resume.file_name)}
                        disabled={downloading === resume.id || !isPro}
                        className={`btn-download-resume ${!isPro ? 'btn-pro-disabled' : ''}`}
                        title={isPro ? 'Download resume' : 'Download requires PRO subscription'}
                      >
                        {downloading === resume.id && isPro ? (
                          <span className="inline-block animate-spin">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </span>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            {!isPro && <span className="pro-badge">PRO</span>}
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CandidateProfilePage;
