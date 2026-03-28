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

  useEffect(() => {
    const fetchCandidateProfile = async () => {
      try {
        const response = await recruiterService.getCandidateProfile(candidateId);
        setCandidate(response.data);
        setLoading(false);
      } catch (err) {
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

  const openResumeInNewTab = (resumeId) => {
    const token = localStorage.getItem('access_token');
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:9000/api';
    const resumeUrl = `${baseURL}/recruiters/candidate/${candidateId}/resume/${resumeId}?token=${token}`;
    window.open(resumeUrl, '_blank');
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

          {/* Resumes */}
          {candidate.resumes && candidate.resumes.length > 0 && (
            <div className="section resumes-section">
              <h2>Resumes</h2>
              <div className="resumes-list">
                {candidate.resumes.map((resume) => (
                  <div key={resume.id} className="resume-item">
                    <div className="resume-info">
                      <p className="resume-name">{resume.file_name}</p>
                      <span className={`status ${resume.status.toLowerCase()}`}>
                        {resume.status}
                      </span>
                    </div>
                    <button
                      onClick={() => openResumeInNewTab(resume.id)}
                      className="btn-view-resume"
                    >
                      View Resume
                    </button>
                  </div>
                ))}
              </div>
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
                  <EmailSendLive
                    candidateId={candidateId}
                    candidateName={`${candidate.first_name} ${candidate.last_name}`}
                    candidateEmail={candidate.email}
                    token={localStorage.getItem('access_token')}
                    onClose={() => setShowEmailModal(false)}
                    onSuccess={() => {
                      setShowEmailModal(false);
                    }}
                    onError={(err) => {
                      console.error('Email sending error:', err);
                    }}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandidateProfilePage;
