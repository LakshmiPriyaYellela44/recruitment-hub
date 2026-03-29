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
    const token = localStorage.getItem('access_token');
    const profileUrl = '/candidate/' + candidateId + '?token=' + token;
    window.open(profileUrl, '_blank');
  };

  React.useEffect(() => {
    const allEmpty = !searchParams.keyword && !searchParams.skills && !searchParams.experience && !searchParams.education;
    if (allEmpty && hasSearched) {
      setHasSearched(false);
    }
  }, [searchParams, hasSearched]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['candidates', searchParams, hasSearched],
    queryFn: async () => {
      if (!hasSearched) return null;
      try {
        const response = await recruiterService.searchCandidates(searchParams);
        console.log('Search response:', response);
        return response.data;
      } catch (err) {
        console.error('Search error:', err);
        throw err;
      }
    },
    enabled: hasSearched,
  });

  const handleSearch = (e) => {
    if (e.key === 'Enter' || e.type === 'click') {
      const hasFilter = searchParams.keyword || searchParams.skills || searchParams.experience || searchParams.education;
      if (hasFilter) setHasSearched(true);
    }
  };

  const handleClearSearch = () => {
    setSearchParams({ skills: '', keyword: '', experience: '', education: '' });
    setHasSearched(false);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Candidate Search</h1>
          <p className="text-gray-600">Find and connect with top talent</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-600">Current Plan</p>
          <p className="text-lg font-bold text-gray-800">{user?.subscription_type}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Keywords</label>
            <input type="text" value={searchParams.keyword} onChange={(e) => setSearchParams({...searchParams, keyword: e.target.value})} onKeyPress={handleSearch} placeholder="Name, email..." className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Skills</label>
            <input type="text" value={searchParams.skills} onChange={(e) => setSearchParams({...searchParams, skills: e.target.value})} onKeyPress={handleSearch} placeholder="Python, React..." className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Experience</label>
            <input type="text" value={searchParams.experience} onChange={(e) => setSearchParams({...searchParams, experience: e.target.value})} onKeyPress={handleSearch} placeholder="Job title, company..." className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Education</label>
            <input type="text" value={searchParams.education} onChange={(e) => setSearchParams({...searchParams, education: e.target.value})} onKeyPress={handleSearch} placeholder="Degree, institution..." className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex flex-col justify-end gap-2">
            <button onClick={handleSearch} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition">Search</button>
            {hasSearched && <button onClick={handleClearSearch} className="px-6 py-2 bg-gray-400 hover:bg-gray-500 text-white rounded font-medium transition text-sm">Clear</button>}
          </div>
        </div>
      </div>

      {!hasSearched && <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center"><p className="text-blue-800 text-lg font-medium">Enter search criteria and click Search</p></div>}
      
      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-4"><h3 className="text-red-800 font-bold mb-2">Error loading results</h3><p className="text-red-700">{error?.message || 'Failed to fetch candidates. Please try again.'}</p></div>}
      
      {isLoading && hasSearched && <div className="text-center py-12"><p className="text-gray-600 text-lg">Loading...</p></div>}
      
      {hasSearched && data?.candidates?.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead><tr className="bg-gray-100 border-b"><th className="px-6 py-4 text-left">Name</th><th className="px-6 py-4 text-left">Email</th><th className="px-6 py-4 text-left">Skills</th><th className="px-6 py-4 text-center">Action</th></tr></thead>
            <tbody>{data.candidates.map((c, i) => <tr key={c.id} className={i%2 ? 'bg-gray-50' : 'bg-white'}><td className="px-6 py-4">{c.first_name} {c.last_name}</td><td className="px-6 py-4">{c.email}</td><td className="px-6 py-4"><div className="flex flex-wrap gap-2">{c.skills?.slice(0,3).map((s,j) => <span key={j} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">{typeof s === 'object' ? s.name : s}</span>)}{c.skills?.length > 3 && <span className="px-2 py-1 bg-gray-100 text-xs">+{c.skills.length-3}</span>}</div></td><td className="px-6 py-4 text-center"><button onClick={() => handleViewProfile(c.id)} className="px-4 py-2 bg-blue-600 text-white text-sm rounded">View</button></td></tr>)}</tbody>
          </table>
        </div>
      )}
      
      {hasSearched && !data?.candidates?.length && !isLoading && <div className="bg-white rounded-lg shadow p-12 text-center"><h3 className="text-lg font-semibold text-gray-700 mb-2">No candidates found</h3><p className="text-gray-600">No match your criteria</p></div>}
    </div>
  );
};
