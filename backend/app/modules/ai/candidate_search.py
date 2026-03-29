"""
Candidate Search & Ranking
Find and rank candidates based on recruiter queries
Uses vector search + scoring + ranking algorithms
"""

import logging
from typing import List, Dict, Optional
from app.modules.ai.query_parser import get_query_parser
from app.modules.ai.vector_db import get_vector_db
from app.modules.ai.resume_scorer import ResumeScorer

logger = logging.getLogger(__name__)


class CandidateRanker:
    """
    Find and rank candidates for recruiter queries
    Returns top candidates with explanations
    """
    
    @staticmethod
    def search_candidates(
        query: str,
        min_score: int = 60,
        return_count: int = 75,
        total_candidates: Optional[int] = None
    ) -> Dict:
        """
        Search candidates matching recruiter query
        
        Args:
            query: Recruiter search query (e.g., "Senior Python dev with 5+ years")
            min_score: Minimum resume score (0-100)
            return_count: How many to return (default 75)
            total_candidates: Total candidates available (for context)
        
        Returns:
        {
            "query_parsed": {parsed requirements},
            "total_matching": 150,
            "total_filtered": 90,
            "returned": 75,
            "candidates": [
                {
                    "candidate_id": "...",
                    "name": "...",
                    "email": "...",
                    "resume_score": 78,
                    "match_score": 0.92,
                    "final_rank_score": 88,
                    "matched_skills": [...],
                    "missing_skills": [...],
                    "recommendation": "Strong Match"
                },
                ...
            ]
        }
        """
        
        try:
            # Step 1: Parse recruiter query
            query_parsed = get_query_parser().parse_query(query)
            logger.info(f"Parsed query: {query_parsed}")
            
            # Step 2: Search vector DB for similar candidates
            vector_db = get_vector_db()
            search_text = query_parsed.get("search_text", query)
            
            similar_candidates = vector_db.search_candidates(
                query_text=search_text,
                top_k=200  # Get more to filter
            )
            
            if not similar_candidates:
                logger.warning("No candidates found in vector DB")
                return {
                    "query_parsed": query_parsed,
                    "total_matching": 0,
                    "total_filtered": 0,
                    "returned": 0,
                    "candidates": []
                }
            
            # Step 3: Score and rank candidates
            scored_candidates = []
            
            for candidate in similar_candidates:
                metadata = candidate.get("metadata", {})
                
                # Extract candidate data
                candidate_score = int(metadata.get("resume_score", 0))
                skills = metadata.get("skills", "").split(",") if metadata.get("skills") else []
                experience = float(metadata.get("experience_years", 0))
                
                # Filter by minimum score
                if candidate_score < min_score:
                    continue
                
                # Calculate match score
                match_data = CandidateRanker._calculate_match(
                    required_skills=query_parsed.get("required_skills", []),
                    candidate_skills=skills,
                    required_experience=query_parsed.get("min_experience_years", 0),
                    candidate_experience=experience,
                    similarity_score=candidate.get("similarity_score", 0.5)
                )
                
                # Calculate final ranking score
                final_score = CandidateRanker._calculate_final_rank_score(
                    resume_score=candidate_score,
                    match_score=match_data["match_score"],
                    similarity_score=candidate.get("similarity_score", 0.5)
                )
                
                scored_candidates.append({
                    "candidate_id": candidate["candidate_id"],
                    "name": metadata.get("name", "Unknown"),
                    "email": metadata.get("email", ""),
                    "resume_score": candidate_score,
                    "match_score": round(match_data["match_score"], 3),
                    "similarity_score": round(candidate.get("similarity_score", 0), 3),
                    "final_rank_score": round(final_score, 1),
                    "matched_skills": match_data["matched_skills"],
                    "missing_skills": match_data["missing_skills"],
                    "experience_years": experience,
                    "recommendation": CandidateRanker._get_recommendation(
                        final_score,
                        match_data["skills_match_percent"]
                    )
                })
            
            # Step 4: Sort by final rank score
            scored_candidates.sort(
                key=lambda x: x["final_rank_score"],
                reverse=True
            )
            
            # Step 5: Return top candidates
            returned_candidates = scored_candidates[:return_count]
            
            return {
                "status": "success",
                "query": query,
                "query_parsed": query_parsed,
                "search_parameters": {
                    "min_score": min_score,
                    "return_count": return_count
                },
                "results": {
                    "total_matching": len(similar_candidates),
                    "total_after_filtering": len(scored_candidates),
                    "returned_count": len(returned_candidates),
                    "parse_confidence": query_parsed.get("confidence", 0)
                },
                "candidates": returned_candidates
            }
        
        except Exception as e:
            logger.error(f"Error searching candidates: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "candidates": []
            }
    
    @staticmethod
    def _calculate_match(
        required_skills: List[str],
        candidate_skills: List[str],
        required_experience: float,
        candidate_experience: float,
        similarity_score: float
    ) -> Dict:
        """Calculate skill and experience match"""
        
        # Normalize skills
        required = set(s.lower().strip() for s in required_skills if s)
        candidate = set(s.lower().strip() for s in candidate_skills if s)
        
        # Calculate matches and gaps
        matched = required & candidate
        missing = required - candidate
        
        # Skills match percentage
        if required:
            skills_match_percent = len(matched) / len(required)
        else:
            skills_match_percent = 1.0
        
        # Experience match
        if required_experience > 0:
            exp_match = min(candidate_experience / required_experience, 1.0)
        else:
            exp_match = 1.0 if candidate_experience > 0 else 0.5
        
        # Combined match score
        match_score = (skills_match_percent * 0.5) + (exp_match * 0.3) + (similarity_score * 0.2)
        
        return {
            "matched_skills": list(matched),
            "missing_skills": list(missing),
            "match_score": min(match_score, 1.0),
            "skills_match_percent": int(skills_match_percent * 100)
        }
    
    @staticmethod
    def _calculate_final_rank_score(
        resume_score: int,
        match_score: float,
        similarity_score: float
    ) -> float:
        """
        Calculate final ranking score (0-100)
        Weighted combination of:
        - Resume quality (40%)
        - Skill match (40%)
        - Semantic similarity (20%)
        """
        
        # Normalize resume score to 0-1
        resume_norm = resume_score / 100.0
        
        final = (resume_norm * 0.4) + (match_score * 0.4) + (similarity_score * 0.2)
        return final * 100  # Convert to 0-100
    
    @staticmethod
    def _get_recommendation(final_score: float, skills_match_percent: int) -> str:
        """Get recommendation based on score"""
        
        if final_score >= 85 and skills_match_percent >= 80:
            return "Strong Match ⭐⭐⭐"
        elif final_score >= 70 and skills_match_percent >= 60:
            return "Good Fit ⭐⭐"
        elif final_score >= 55 and skills_match_percent >= 40:
            return "Consider ⭐"
        else:
            return "Possible Match"


# Singleton for dependency injection
_ranker_instance = None

def get_candidate_ranker() -> CandidateRanker:
    """Get ranker instance"""
    global _ranker_instance
    if _ranker_instance is None:
        _ranker_instance = CandidateRanker()
    return _ranker_instance
