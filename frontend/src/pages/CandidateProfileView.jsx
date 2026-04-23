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
      <div className="flex items-center justify-center h-screen bg-[#0f1419]">
        <div className="text-center">
          <p className="text-[#C41E3A] text-lg">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0f1419] to-[#1a1f26] p-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg shadow-lg p-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-bold text-[#f5f7fa] mb-2">
                {candidate.first_name} {candidate.last_name}
              </h1>
              <p className="text-[#8b95a5] text-lg">{candidate.email}</p>
            </div>
            <button
              onClick={() => window.close()}
              className="text-3xl text-[#6b7684] hover:text-[#8b95a5]"
            >
              ✕
            </button>
          </div>

          <div className="mb-6">
            {user?.subscription_type === 'PRO' ? (
              <button
                onClick={() => setShowEmailForm(true)}
                style={{ backgroundColor: '#C41E3A' }}
                className="px-6 py-3 hover:opacity-90 text-white font-medium rounded text-lg"
              >
                Send Email
              </button>
            ) : (
              <button
                onClick={() => window.open('/dashboard', '_self')}
                style={{ backgroundColor: '#C41E3A' }}
                className="px-6 py-3 hover:opacity-90 text-white font-medium rounded text-lg"
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
                  <div className="mb-6 p-4 bg-[rgba(196,30,58,0.15)] border border-[#C41E3A] rounded-lg">
                    <p className="text-[#C41E3A] font-semibold">
                      No email found for this candidate. Please ensure candidate has a valid email.
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
              <h3 className="text-2xl font-bold text-[#f5f7fa] mb-4">Skills</h3>
              {candidate.skills ? (
                typeof candidate.skills === 'object' && !Array.isArray(candidate.skills) ? (
                  // Categorized skills
                  <div className="space-y-6">
                    {Object.entries(candidate.skills).map(([category, skillList]) => 
                      skillList && skillList.length > 0 && (
                        <div key={category}>
                          <h4 className="text-lg font-semibold text-[#f5f7fa] mb-2 capitalize">
                            {category.replace(/_/g, ' ')}
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {skillList.map((skill, idx) => (
                              <span
                                key={idx}
                                style={{ backgroundColor: '#C41E3A' }}
                                className="px-4 py-2 hover:opacity-90 text-white rounded-full font-medium transition-colors"
                              >
                                {skill.name || skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  // Flat skills array (backwards compatibility)
                  <div className="flex flex-wrap gap-2">
                    {candidate.skills.map((skill, idx) => (
                      <span
                        key={idx}
                        style={{ backgroundColor: '#C41E3A' }}
                        className="px-4 py-2 hover:opacity-90 text-white rounded-full font-medium transition-colors"
                      >
                        {skill.name || skill}
                      </span>
                    ))}
                  </div>
                )
              ) : (
                <p className="text-[#8b95a5]">No skills listed</p>
              )}
            </section>

            {candidate.experiences && candidate.experiences.length > 0 && (
              <section>
                <h3 className="text-2xl font-bold text-[#f5f7fa] mb-4">Experience</h3>
                <div className="space-y-5">
                  {candidate.experiences.map((exp) => (
                    <div key={exp.id} className="border-l-4 border-[#C41E3A] pl-6 py-2">
                      <p className="text-xl font-semibold text-[#f5f7fa]">{exp.job_title}</p>
                      <p className="text-lg text-[#8b95a5]">{exp.company_name}</p>
                      {exp.years && <p className="text-[#6b7684] mt-1">{exp.years} years experience</p>}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {candidate.educations && candidate.educations.length > 0 && (
              <section>
                <h3 className="text-2xl font-bold text-[#f5f7fa] mb-4">Education</h3>
                <div className="space-y-5">
                  {candidate.educations.map((edu) => (
                    <div key={edu.id} className="border-l-4 border-[#C41E3A] pl-6 py-2">>
                      <p className="text-xl font-semibold text-[#f5f7fa]">{edu.degree}</p>
                      <p className="text-lg text-[#8b95a5]">{edu.institution}</p>
                      {edu.field_of_study && (
                        <p className="text-[#6b7684] mt-1">{edu.field_of_study}</p>
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
