import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import recruiterService from '../services/recruiterService';
import { useAuth } from '../context/AuthContext';
import EmailSendLive from '../components/EmailSendLive';

export const CandidateProfileView = () => {
  const { id } = useParams();
  const { user, setUser } = useAuth();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEmailForm, setShowEmailForm] = useState(false);

  useEffect(() => {
    const fetchCandidate = async () => {
      try {
        const response = await recruiterService.getCandidateDetail(id);
        setCandidate(response.data);
      } catch (err) {
        setError('Failed to load candidate profile');
      } finally {
        setLoading(false);
      }
    };

    fetchCandidate();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center">
          <p className="text-gray-600 text-lg">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center">
          <p className="text-red-600 text-lg">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">
                {candidate.first_name} {candidate.last_name}
              </h1>
              <p className="text-gray-600 text-lg">{candidate.email}</p>
            </div>
            <button
              onClick={() => window.close()}
              className="text-3xl text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="mb-6">
            {user?.subscription_type === 'PRO' ? (
              <button
                onClick={() => setShowEmailForm(true)}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded text-lg"
              >
                📧 Send Email
              </button>
            ) : (
              <button
                onClick={() => window.open('/dashboard', '_self')}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded text-lg"
              >
                🚀 Upgrade to Send Email
              </button>
            )}
          </div>

          {showEmailForm && (
            (() => {
              // Extract email from latest resume parsed data, fall back to candidate.email
              const latestResume = candidate.resumes && candidate.resumes.length > 0 ? candidate.resumes[0] : null;
              const parsedEmail = latestResume?.parsed_data?.email || candidate.email;
              
              if (!parsedEmail) {
                return (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-700 font-semibold">
                      ⚠️ No email found for this candidate. Please ensure candidate has a valid email.
                    </p>
                  </div>
                );
              }
              
              return (
                <EmailSendLive
                  candidateId={candidate.id}
                  candidateName={`${candidate.first_name} ${candidate.last_name}`}
                  candidateEmail={parsedEmail}
                  token={localStorage.getItem('access_token')}
                  onSuccess={(result) => {
                    console.log('Email sent successfully:', result.message_id);
                    setShowEmailForm(false);
                  }}
                  onError={(error) => {
                    console.error('Email sending failed:', error.message);
                  }}
                  onClose={() => setShowEmailForm(false)}
                />
              );
            })()
          )}

          <div className="space-y-8">
            <section>
              <h3 className="text-2xl font-bold text-gray-800 mb-4">Skills</h3>
              {candidate.skills?.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {candidate.skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-4 py-2 bg-blue-100 text-blue-800 rounded-full font-medium"
                    >
                      {skill.name || skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No skills listed</p>
              )}
            </section>

            {candidate.experiences && candidate.experiences.length > 0 && (
              <section>
                <h3 className="text-2xl font-bold text-gray-800 mb-4">Experience</h3>
                <div className="space-y-5">
                  {candidate.experiences.map((exp) => (
                    <div key={exp.id} className="border-l-4 border-blue-500 pl-6 py-2">
                      <p className="text-xl font-semibold text-gray-800">{exp.job_title}</p>
                      <p className="text-lg text-gray-600">{exp.company_name}</p>
                      {exp.years && <p className="text-gray-500 mt-1">{exp.years} years experience</p>}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {candidate.educations && candidate.educations.length > 0 && (
              <section>
                <h3 className="text-2xl font-bold text-gray-800 mb-4">Education</h3>
                <div className="space-y-5">
                  {candidate.educations.map((edu) => (
                    <div key={edu.id} className="border-l-4 border-green-500 pl-6 py-2">
                      <p className="text-xl font-semibold text-gray-800">{edu.degree}</p>
                      <p className="text-lg text-gray-600">{edu.institution}</p>
                      {edu.field_of_study && (
                        <p className="text-gray-500 mt-1">{edu.field_of_study}</p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
