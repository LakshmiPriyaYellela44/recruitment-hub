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
    <div className="min-h-screen bg-gradient-to-b from-[#0f1419] to-[#1a1f26]">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8 md:py-12">
        {/* Header Section */}
        <div className="mb-8 flex justify-between items-start">
          <div className="flex-1">
            <p className="text-xs md:text-sm font-semibold text-[#C41E3A] uppercase tracking-widest mb-2">Find Top Talent</p>
            <h1 className="text-2xl md:text-3xl font-semibold text-white mb-2 tracking-tight">Discover Talented Professionals</h1>
            <p className="text-xs md:text-sm text-gray-400 font-normal">Search by skills, experience, and education</p>
            {user?.subscription_type === 'BASIC' && (
              <p className="text-xs text-orange-500 mt-3 block">⚠️ Limited features - Upgrade to PRO for full access</p>
            )}
            {user?.subscription_type === 'PRO' && (
              <p className="text-xs text-[#10B981] mt-3 block">✨ PRO Plan - Full access unlocked</p>
            )}
          </div>
          <div className="flex flex-col gap-2 text-right pl-4">
            <div>
              <p className="text-xs text-gray-500 mb-1">Current Plan</p>
              <p className="text-lg font-bold text-white">{user?.subscription_type}</p>
            </div>
          </div>
      </div>

      <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg shadow p-6 md:p-8 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs md:text-sm font-semibold text-[#f5f7fa] mb-2 uppercase">Keywords</label>
            <input
              type="text"
              name="keyword"
              value={searchParams.keyword}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, keyword: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Name, email..."
              className="w-full px-3 md:px-4 py-3 bg-[#0f1419] border border-[#2d333f] text-[#f5f7fa] placeholder-[#6b7684] rounded focus:outline-none focus:ring-2 focus:ring-[#C41E3A]"
            />
          </div>
          <div>
            <label className="block text-xs md:text-sm font-semibold text-[#f5f7fa] mb-2 uppercase">Skills</label>
            <input
              type="text"
              name="skills"
              value={searchParams.skills}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, skills: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Python, React..."
              className="w-full px-3 md:px-4 py-3 bg-[#0f1419] border border-[#2d333f] text-[#f5f7fa] placeholder-[#6b7684] rounded focus:outline-none focus:ring-2 focus:ring-[#C41E3A]"
            />
          </div>
          <div>
            <label className="block text-xs md:text-sm font-semibold text-[#f5f7fa] mb-2 uppercase">Experience</label>
            <input
              type="text"
              name="experience"
              value={searchParams.experience}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, experience: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Job title, company..."
              className="w-full px-3 md:px-4 py-3 bg-[#0f1419] border border-[#2d333f] text-[#f5f7fa] placeholder-[#6b7684] rounded focus:outline-none focus:ring-2 focus:ring-[#C41E3A]"
            />
          </div>
          <div>
            <label className="block text-xs md:text-sm font-semibold text-[#f5f7fa] mb-2 uppercase">Education</label>
            <input
              type="text"
              name="education"
              value={searchParams.education}
              onChange={(e) => setSearchParams((prev) => ({ ...prev, education: e.target.value }))}
              onKeyPress={handleSearch}
              placeholder="Degree, institution..."
              className="w-full px-3 md:px-4 py-3 bg-[#0f1419] border border-[#2d333f] text-[#f5f7fa] placeholder-[#6b7684] rounded focus:outline-none focus:ring-2 focus:ring-[#C41E3A]"
            />
          </div>
          <div className="flex flex-col justify-end gap-2">
            <button
              onClick={handleSearch}
              className="px-4 md:px-6 py-3 bg-[#C41E3A] hover:bg-[#A91930] text-white rounded font-semibold transition duration-200 shadow-md hover:shadow-lg"
            >
              Search
            </button>
            {hasSearched && (
              <button
                onClick={handleClearSearch}
                className="px-4 md:px-6 py-2 bg-[#2d333f] hover:bg-[#3d444f] text-[#8b95a5] rounded font-medium transition text-sm"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {!hasSearched && (
        <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg p-8 md:p-12 text-center">
          <p className="text-[#8b95a5] text-base md:text-lg font-medium">Enter search criteria and click Search to find candidates</p>
        </div>
      )}

      {isLoading && hasSearched ? (
        <div className="text-center py-12">
          <p className="text-[#8b95a5] text-lg">Loading candidates...</p>
        </div>
      ) : hasSearched && data?.candidates?.length > 0 ? (
        <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-[#0f1419] border-b border-[#2d333f]">
                  <th className="px-6 py-4 text-left font-semibold text-[#f5f7fa]">Name</th>
                  <th className="px-6 py-4 text-left font-semibold text-[#f5f7fa]">Email</th>
                  <th className="px-6 py-4 text-left font-semibold text-[#f5f7fa]">Skills</th>
                  <th className="px-6 py-4 text-center font-semibold text-[#f5f7fa]">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.candidates.map((candidate, idx) => (
                  <tr key={candidate.id} className={`border-b border-[#2d333f] hover:bg-[#232a33] transition ${idx % 2 === 0 ? 'bg-[#1a1f26]' : 'bg-[#1f2530]'}`}>
                    <td className="px-6 py-4 text-[#f5f7fa] font-medium">
                      {candidate.first_name} {candidate.last_name}
                    </td>
                    <td className="px-6 py-4 text-[#8b95a5]">{candidate.email}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-2">
                        {candidate.skills?.slice(0, 3).map((skill, sidx) => (
                          <span
                            key={sidx}
                            className="px-2 py-1 bg-[rgba(196,30,58,0.15)] text-[#FF6B7A] text-xs rounded"
                          >
                            {skill.name || skill}
                          </span>
                        ))}
                        {candidate.skills?.length > 3 && (
                          <span className="px-2 py-1 bg-[rgba(139,149,165,0.15)] text-[#8b95a5] text-xs rounded">
                            +{candidate.skills.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => handleViewProfile(candidate.id)}
                        className="px-4 py-3 bg-[#C41E3A] hover:bg-[#A91930] text-white text-sm rounded font-semibold transition"
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
        <div className="bg-[#1a1f26] border border-[#2d333f] rounded-lg shadow p-12 text-center">
          <div className="text-[#2d333f] text-5xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold text-[#f5f7fa] mb-2">No candidates found</h3>
          <p className="text-[#8b95a5] mb-4">
            No candidates with parsed resumes match your search criteria.
          </p>
          <p className="text-sm text-[#6b7684]">
            💡 Try adjusting your search criteria or check back later as more candidates upload their resumes.
          </p>
        </div>
      ) : null}
    </div>
  );
};
