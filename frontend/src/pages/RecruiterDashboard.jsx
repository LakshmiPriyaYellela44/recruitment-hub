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
    <div className="min-h-screen bg-gradient-to-b from-[#0f1419] via-[#1a1f26] to-[#0f1419]">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8 md:py-12">
        {/* Header Section */}
        <div className="mb-12 flex justify-between items-start">
          <div className="flex-1">
            <p className="text-xs md:text-sm font-bold text-[#8B2635] uppercase tracking-widest mb-3">Discovery</p>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#f5f7fa] mb-3 tracking-tight">
              Find Top Talent
            </h1>
            <p className="text-sm sm:text-base md:text-lg text-[#8b95a5] font-normal max-w-2xl">
              Search our database of qualified professionals by skills, experience, and education
            </p>
            {user?.subscription_type === 'BASIC' && (
              <p className="text-sm text-[#f59e0b] mt-4 font-semibold bg-[#fffbeb] px-4 py-2 rounded-lg w-fit border border-[#fcd34d]">
                ⚡ Limited features - Upgrade to PRO for advanced search
              </p>
            )}
            {user?.subscription_type === 'PRO' && (
              <p className="text-sm text-[#10b981] mt-4 font-semibold bg-[#ecfdf5] px-4 py-2 rounded-lg w-fit border border-[#d1fae5]">
                ✓ PRO Plan active - Full search capabilities unlocked
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2 text-right pl-8 hidden md:block">
            <p className="text-xs text-[#8b95a5] font-medium">Current Subscription</p>
            <p className="text-2xl font-bold text-[#8B2635]">{user?.subscription_type}</p>
          </div>
        </div>

        {/* Search Form Card */}
        <div className="bg-[#1a1f26] border border-[#2d333f] rounded-xl shadow-sm p-4 sm:p-6 md:p-8 mb-8">
          <h2 className="text-base sm:text-lg font-semibold text-[#f5f7fa] mb-4 sm:mb-6">Search Filters</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 sm:gap-4 md:gap-5">
            {/* Keywords Input */}
            <div>
              <label className="block text-sm font-semibold text-[#f5f7fa] mb-2 uppercase tracking-wide">
                Keywords
              </label>
              <input
                type="text"
                name="keyword"
                value={searchParams.keyword}
                onChange={(e) => setSearchParams((prev) => ({ ...prev, keyword: e.target.value }))}
                onKeyPress={handleSearch}
                placeholder="Name, email..."
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-[#2d333f] text-[#0f1419] placeholder-[#6d7a88] rounded-lg focus:outline-none focus:border-[#8B2635] focus:ring-4 focus:ring-[#5C1520] transition text-sm"
              />
            </div>

            {/* Skills Input */}
            <div>
              <label className="block text-sm font-semibold text-[#f5f7fa] mb-2 uppercase tracking-wide">
                Skills
              </label>
              <input
                type="text"
                name="skills"
                value={searchParams.skills}
                onChange={(e) => setSearchParams((prev) => ({ ...prev, skills: e.target.value }))}
                onKeyPress={handleSearch}
                placeholder="Python, React..."
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-[#2d333f] text-[#0f1419] placeholder-[#6d7a88] rounded-lg focus:outline-none focus:border-[#8B2635] focus:ring-4 focus:ring-[#5C1520] transition text-sm"
              />
            </div>

            {/* Experience Input */}
            <div>
              <label className="block text-sm font-semibold text-[#f5f7fa] mb-2 uppercase tracking-wide">
                Experience
              </label>
              <input
                type="text"
                name="experience"
                value={searchParams.experience}
                onChange={(e) => setSearchParams((prev) => ({ ...prev, experience: e.target.value }))}
                onKeyPress={handleSearch}
                placeholder="Job title..."
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-[#2d333f] text-[#0f1419] placeholder-[#6d7a88] rounded-lg focus:outline-none focus:border-[#8B2635] focus:ring-4 focus:ring-[#5C1520] transition text-sm"
              />
            </div>

            {/* Education Input */}
            <div>
              <label className="block text-sm font-semibold text-[#f5f7fa] mb-2 uppercase tracking-wide">
                Education
              </label>
              <input
                type="text"
                name="education"
                value={searchParams.education}
                onChange={(e) => setSearchParams((prev) => ({ ...prev, education: e.target.value }))}
                onKeyPress={handleSearch}
                placeholder="Degree..."
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border-2 border-[#2d333f] text-[#0f1419] placeholder-[#6d7a88] rounded-lg focus:outline-none focus:border-[#8B2635] focus:ring-4 focus:ring-[#5C1520] transition text-sm"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col justify-end gap-2 sm:gap-3">
              <button
                onClick={handleSearch}
                style={{ backgroundColor: '#C41E3A' }}
                className="px-4 sm:px-6 py-2 sm:py-3 hover:opacity-90 text-white rounded-lg font-semibold transition-all duration-200 transform hover:shadow-md active:scale-95 flex items-center justify-center gap-2 text-sm sm:text-base"
              >
                Search
              </button>
              {hasSearched && (
                <button
                  onClick={handleClearSearch}
                  className="px-4 sm:px-6 py-1.5 sm:py-2 bg-[#2d333f] hover:bg-[#3d4551] text-[#f5f7fa] rounded-lg font-medium transition text-xs sm:text-sm"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Results Section */}
        {!hasSearched && (
          <div className="bg-[#1a1f26] border-2 border-dashed border-[#3d4551] rounded-xl p-12 text-center">

            <p className="text-[#8b95a5] text-lg font-medium">Enter search criteria to discover qualified candidates</p>
            <p className="text-[#6d7a88] text-sm mt-2">Refine your search using multiple filters for best results</p>
          </div>
        )}

        {isLoading && hasSearched ? (
          <div className="text-center py-16">
            <div className="inline-block w-8 h-8 border-4 border-[#2d333f] border-t-[#8B2635] rounded-full animate-spin mb-4"></div>
            <p className="text-[#8b95a5] text-lg font-medium">Loading candidates...</p>
          </div>
        ) : hasSearched && data?.candidates?.length > 0 ? (
          <div className="bg-[#1a1f26] border border-[#2d333f] rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-[#0f1419] border-b border-[#2d333f]">
                    <th className="px-3 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-bold text-[#f5f7fa] uppercase tracking-wide">
                      Candidate
                    </th>
                    <th className="px-3 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-bold text-[#f5f7fa] uppercase tracking-wide">
                      Email
                    </th>
                    <th className="px-3 sm:px-6 py-3 sm:py-4 text-left text-xs sm:text-sm font-bold text-[#f5f7fa] uppercase tracking-wide">
                      Top Skills
                    </th>
                    <th className="px-3 sm:px-6 py-3 sm:py-4 text-center text-xs sm:text-sm font-bold text-[#f5f7fa] uppercase tracking-wide">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.candidates.map((candidate, idx) => (
                    <tr 
                      key={candidate.id} 
                      className="border-b border-[#2d333f] hover:bg-[#0f1419] transition"
                    >
                      <td className="px-3 sm:px-6 py-3 sm:py-4 text-white font-bold text-base sm:text-lg">
                        {candidate.first_name} {candidate.last_name}
                      </td>
                      <td className="px-3 sm:px-6 py-3 sm:py-4 text-[#d0d8e0] font-medium text-sm sm:text-base">{candidate.email}</td>
                      <td className="px-3 sm:px-6 py-3 sm:py-4">
                        <div className="flex flex-wrap gap-1 sm:gap-2">
                          {candidate.skills?.slice(0, 3).map((skill, sidx) => (
                            <span
                              key={sidx}
                              className="px-2 sm:px-3 py-0.5 sm:py-1 bg-[#5C1520] text-[#C41E3A] text-xs font-medium rounded-full border border-[#8B2635]"
                            >
                              {skill.name || skill}
                            </span>
                          ))}
                          {candidate.skills?.length > 3 && (
                            <span className="px-2 sm:px-3 py-0.5 sm:py-1 bg-[#2d333f] text-[#8b95a5] text-xs font-medium rounded-full">
                              +{candidate.skills.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 sm:px-6 py-3 sm:py-4 text-center">
                        <button
                          onClick={() => handleViewProfile(candidate.id)}
                          style={{ backgroundColor: '#C41E3A' }}
                          className="px-3 sm:px-4 py-1.5 sm:py-2 hover:opacity-90 text-white text-xs sm:text-sm rounded-lg font-semibold transition-all duration-200 transform hover:shadow-md active:scale-95"
                        >
                          View Profile
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Results Summary */}
            <div className="bg-[#0f1419] border-t border-[#2d333f] px-6 py-4">
              <p className="text-sm text-[#8b95a5]">
                Showing <span className="font-semibold text-[#f5f7fa]">{data.candidates.length}</span> candidate{data.candidates.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        ) : hasSearched ? (
          <div className="bg-[#1a1f26] border border-[#2d333f] rounded-xl p-12 text-center">
            <h3 className="text-lg font-bold text-[#f5f7fa] mb-2">No candidates found</h3>
            <p className="text-[#8b95a5] mb-4">
              We couldn't find any candidates matching your criteria.
            </p>
            <p className="text-sm text-[#6d7a88]">
              Try adjusting your search filters or check back later as new candidates join
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default RecruiterDashboard;
