import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import recruiterService from '../services/recruiterService';
import { useAuth } from '../context/AuthContext';

export const RecruiterDashboard = () => {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useState({
    skills: '',
    keyword: '',
    experience: '',
    education: '',
  });
  const [hasSearched, setHasSearched] = useState(false);

  const handleViewProfile = (candidateId) => {
    // Navigate to candidate profile page in a new tab
    const token = localStorage.getItem('access_token');
    const profileUrl = `/candidate/${candidateId}?token=${token}`;
    window.open(profileUrl, '_blank');
  };

  // Auto-clear search results when all filters are removed
  React.useEffect(() => {
    const allEmpty = 
      !searchParams.keyword && 
      !searchParams.skills && 
      !searchParams.experience &&
      !searchParams.education;
    
    if (allEmpty && hasSearched) {
      setHasSearched(false);
    }
  }, [searchParams, hasSearched]);

  const { data, isLoading } = useQuery({
    queryKey: ['candidates', searchParams, hasSearched],
    queryFn: async () => {
      if (!hasSearched) return null;
      const response = await recruiterService.searchCandidates({
        skills: searchParams.skills,
        keyword: searchParams.keyword,
        experience: searchParams.experience,
        education: searchParams.education,
      });
      return response.data;
    },
    enabled: hasSearched,
  });

  const handleSearch = (e) => {
    if (e.key === 'Enter' || e.type === 'click') {
      const hasFilter = searchParams.keyword || searchParams.skills || searchParams.experience || searchParams.education;
      if (hasFilter) {
        setHasSearched(true);
      }
    }
  };

  const handleClearSearch = () => {
    setSearchParams({
      skills: '',
      keyword: '',
      experience: '',
      education: '',
    });
    setHasSearched(false);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Candidate Search 🔍</h1>
          <p className="text-gray-600">
            Find and connect with top talent
            {user?.subscription_type !== 'PRO' && (
              <span className="text-sm text-orange-600 block mt-2">
                ⚠️ <strong>Limited features</strong> - You're on BASIC plan
              </span>
            )}
            {user?.subscription_type === 'PRO' && (
              <span className="text-sm text-green-600 block mt-2">
                ✨ <strong>PRO Plan Active</strong> - You have access to detailed profiles and email
              </span>
            )}
          </p>
        </div>
        <div className="flex flex-col gap-2">
          <div className="text-right">
            <p className="text-sm text-gray-600">Current Plan</p>
            <p className="text-lg font-bold text-gray-800">{user?.subscription_type}</p>
            {user?.subscription_type === 'BASIC' && (
              <p className="text-xs text-orange-600 mt-1">Contact admin to upgrade</p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Keywords</label>
            <input
              type="text"
              name="keyword"
              value={searchParams.keyword}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, keyword: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Name, email..."
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Skills</label>
            <input
              type="text"
              name="skills"
              value={searchParams.skills}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, skills: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Python, React..."
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Experience</label>
            <input
              type="text"
              name="experience"
              value={searchParams.experience}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, experience: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Job title, company..."
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Education</label>
            <input
              type="text"
              name="education"
              value={searchParams.education}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, education: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Degree, institution..."
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex flex-col justify-end gap-2">
            <button
              onClick={handleSearch}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition"
            >
              🔍 Search
            </button>
            {hasSearched && (
              <button
                onClick={handleClearSearch}
                className="px-6 py-2 bg-gray-400 hover:bg-gray-500 text-white rounded font-medium transition text-sm"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {!hasSearched && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
          <p className="text-blue-800 text-lg font-medium">Enter search criteria and click Search to find candidates</p>
        </div>
      )}

      {isLoading && hasSearched ? (
        <div className="text-center py-12">
          <p className="text-gray-600 text-lg">Loading candidates...</p>
        </div>
      ) : hasSearched && data?.candidates?.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-100 border-b">
                  <th className="px-6 py-4 text-left font-semibold text-gray-800">Name</th>
                  <th className="px-6 py-4 text-left font-semibold text-gray-800">Email</th>
                  <th className="px-6 py-4 text-left font-semibold text-gray-800">Skills</th>
                  <th className="px-6 py-4 text-center font-semibold text-gray-800">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.candidates.map((candidate, idx) => (
                  <tr key={candidate.id} className={`border-b hover:bg-gray-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                    <td className="px-6 py-4 text-gray-800 font-medium">
                      {candidate.first_name} {candidate.last_name}
                    </td>
                    <td className="px-6 py-4 text-gray-600">{candidate.email}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-2">
                        {candidate.skills?.slice(0, 3).map((skill, sidx) => (
                          <span
                            key={sidx}
                            className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                          >
                            {skill.name || skill}
                          </span>
                        ))}
                        {candidate.skills?.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                            +{candidate.skills.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => handleViewProfile(candidate.id)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded font-medium transition"
                      >
                        View Profile
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : hasSearched ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-400 text-5xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">No candidates found</h3>
          <p className="text-gray-600 mb-4">
            No candidates with parsed resumes match your search criteria.
          </p>
          <p className="text-sm text-gray-500">
            💡 Try adjusting your search criteria or check back later as more candidates upload their resumes.
          </p>
        </div>
      ) : null}
    </div>
  );
};
