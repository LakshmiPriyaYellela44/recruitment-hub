"""
Resume Scorer
Calculate 0-100 score for candidates based on:
- Experience years (40%)
- Education level (30%)
- Skills depth (30%)
"""

import logging
from typing import Dict, List, Optional, Any
from app.modules.ai.models import ParsedResumeData

logger = logging.getLogger(__name__)


class ResumeScorer:
    """
    Score resumes on 0-100 scale
    Used for filtering and ranking candidates
    """
    
    # Education level mapping
    EDUCATION_LEVELS = {
        "phd": 95,
        "doctorate": 95,
        "master": 85,
        "mba": 85,
        "ms": 80,
        "ma": 80,
        "bachelor": 70,
        "bs": 70,
        "ba": 70,
        "associate": 40,
        "high school": 20,
        "diploma": 15,
        "certificate": 25
    }
    
    # Skill categories and complexity
    HIGH_VALUE_SKILLS = {
        # Programming languages
        "python": 10, "java": 10, "go": 10, "rust": 12, "kotlin": 8,
        "javascript": 8, "typescript": 9, "c++": 12, "c#": 10,
        
        # Cloud & DevOps
        "aws": 12, "azure": 11, "gcp": 11, "kubernetes": 13, "docker": 11,
        "terraform": 11, "jenkins": 9, "ci/cd": 10,
        
        # Databases
        "postgresql": 11, "mongodb": 10, "mysql": 9, "redis": 10,
        "dynamodb": 10, "elasticsearch": 11,
        
        # Frameworks
        "fastapi": 11, "django": 10, "react": 10, "spring": 10,
        "node.js": 9, "vue": 8, ".net": 10,
        
        # Leadership & Management
        "management": 8, "leadership": 8, "mentoring": 7,
        "team lead": 10, "architect": 10, "staff engineer": 11
    }
    
    MEDIUM_VALUE_SKILLS = {
        "git": 5, "html": 4, "css": 4, "sql": 8, "api": 7,
        "rest": 7, "microservices": 9, "agile": 6, "scrum": 5
    }
    
    # Experience bands
    EXPERIENCE_BANDS = {
        0: 0,      # Entry level: 0 points
        1: 15,     # 1 year: 15 points
        2: 25,     # 2 years: 25 points
        3: 35,     # 3 years: 35 points
        5: 50,     # 5 years: 50 points
        7: 65,     # 7 years: 65 points
        10: 85,    # 10 years: 85 points
        15: 95,    # 15+ years: 95 points
    }
    
    @staticmethod
    def calculate_score(parsed_data: ParsedResumeData) -> Dict[str, Any]:
        """
        Calculate comprehensive resume score
        
        Returns:
        {
            "total_score": 75,           # 0-100
            "experience_score": 50,      # 0-100
            "education_score": 70,       # 0-100
            "skills_score": 85,          # 0-100
            "seniority_level": "Senior", # Entry/Mid/Senior/Principal
            "competency_rating": "High"  # Low/Medium/High/Expert
        }
        """
        
        try:
            # 1. Experience Scoring (40%)
            exp_score = ResumeScorer._score_experience(
                parsed_data.total_experience_years,
                parsed_data.experiences
            )
            
            # 2. Education Scoring (30%)
            edu_score = ResumeScorer._score_education(parsed_data.education)
            
            # 3. Skills Scoring (30%)
            skills_score = ResumeScorer._score_skills(parsed_data.skills)
            
            # Weighted total
            total_score = (exp_score * 0.4) + (edu_score * 0.3) + (skills_score * 0.3)
            total_score = int(min(total_score, 100))
            
            # Determine seniority level
            seniority = ResumeScorer._get_seniority_level(
                parsed_data.total_experience_years,
                edu_score,
                skills_score
            )
            
            # Competency rating
            competency = ResumeScorer._get_competency_rating(total_score)
            
            return {
                "total_score": total_score,
                "experience_score": int(exp_score),
                "education_score": int(edu_score),
                "skills_score": int(skills_score),
                "seniority_level": seniority,
                "competency_rating": competency,
                "breakdown": {
                    "experience": int(exp_score),
                    "education": int(edu_score),
                    "skills": int(skills_score)
                }
            }
        
        except Exception as e:
            logger.error(f"Error calculating score: {e}")
            return {
                "total_score": 0,
                "error": str(e)
            }
    
    @staticmethod
    def _score_experience(years: float, experiences: List) -> float:
        """Score based on years and job titles"""
        
        # Base score from years
        base_score = 0
        for exp_years, score in sorted(ResumeScorer.EXPERIENCE_BANDS.items()):
            if years >= exp_years:
                base_score = score
        
        # Bonus for leadership/senior roles
        bonus = 0
        senior_keywords = ["lead", "senior", "principal", "director", "manager", 
                          "architect", "head", "chief", "staff"]
        
        if experiences:
            for exp in experiences:
                if exp.job_title:
                    title_lower = exp.job_title.lower()
                    if any(kw in title_lower for kw in senior_keywords):
                        bonus = min(bonus + 5, 15)
        
        return min(base_score + bonus, 100)
    
    @staticmethod
    def _score_education(education: List) -> float:
        """Score based on education level"""
        
        best_score = 0
        
        for edu in education:
            if edu.degree:
                degree_lower = edu.degree.lower()
                
                # Try to match education level
                for level_keyword, score in ResumeScorer.EDUCATION_LEVELS.items():
                    if level_keyword in degree_lower:
                        best_score = max(best_score, score)
        
        return best_score
    
    @staticmethod
    def _score_skills(skills: List[str]) -> float:
        """Score based on skills depth and quality"""
        
        if not skills:
            return 0
        
        total_value = 0
        max_possible = len(skills) * 10
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            
            # Check high-value skills
            if skill_lower in ResumeScorer.HIGH_VALUE_SKILLS:
                total_value += ResumeScorer.HIGH_VALUE_SKILLS[skill_lower]
            
            # Check medium-value skills
            elif skill_lower in ResumeScorer.MEDIUM_VALUE_SKILLS:
                total_value += ResumeScorer.MEDIUM_VALUE_SKILLS[skill_lower]
            
            # Generic skill value
            else:
                total_value += 5
        
        # Normalize to 0-100, bonus for having many skills
        skill_score = (total_value / max_possible) * 80  # Base 80%
        skill_count_bonus = min(len(skills) / 20 * 20, 20)  # Up to +20% for many skills
        
        return min(skill_score + skill_count_bonus, 100)
    
    @staticmethod
    def _get_seniority_level(years: float, edu_score: float, skills_score: float) -> str:
        """Determine seniority level"""
        
        if years >= 10 or skills_score >= 80 and years >= 5:
            return "Principal"
        elif years >= 7 or (skills_score >= 75 and years >= 3):
            return "Senior"
        elif years >= 3 or skills_score >= 60:
            return "Mid-level"
        elif years >= 1:
            return "Junior"
        else:
            return "Entry-level"
    
    @staticmethod
    def _get_competency_rating(score: float) -> str:
        """Get competency rating"""
        
        if score >= 85:
            return "Expert"
        elif score >= 70:
            return "High"
        elif score >= 50:
            return "Medium"
        else:
            return "Low"


# Singleton
_scorer_instance = None

def get_resume_scorer() -> ResumeScorer:
    """Get scorer instance"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = ResumeScorer()
    return _scorer_instance
