"""
Query Parser
Understands recruiter search queries and extracts requirements
Uses LLM to parse natural language into structured requirements
"""

import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
import os

logger = logging.getLogger(__name__)


class QueryParserException(Exception):
    """Query parsing errors"""
    pass


class QueryParser:
    """
    Parse recruiter queries like:
    "Find senior Python developers with 5+ years AWS experience"
    
    Extract:
    - Required skills
    - Minimum experience
    - Seniority level
    - Nice-to-have skills
    """
    
    def __init__(self):
        """Initialize query parser"""
        self.enabled = bool(os.getenv("OPENAI_API_KEY"))
        if self.enabled:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def parse_query(self, query: str) -> Dict[str, any]:
        """
        Parse recruiter query
        
        Input: "Find senior Python developers with 5+ years AWS, Docker experience"
        
        Returns:
        {
            "required_skills": ["Python", "AWS", "Docker"],
            "nice_to_have_skills": [],
            "min_experience_years": 5,
            "seniority_level": "Senior",
            "job_title": "Python Developer",
            "search_text": "...",
            "confidence": 0.95
        }
        """
        
        if not self.enabled:
            # Fallback: simple parsing
            return self._simple_parse(query)
        
        try:
            prompt = f"""Parse this recruiter job query into structured requirements.

Query: "{query}"

Extract and return ONLY valid JSON (no markdown):
{{
    "required_skills": ["list", "of", "required", "skills"],
    "nice_to_have_skills": ["optional", "skills"],
    "job_title": "extracted job title or null",
    "min_experience_years": 0,
    "max_experience_years": null,
    "seniority_level": "Entry/Junior/Mid/Senior/Principal or null",
    "min_resume_score": null,
    "keywords": ["other", "keywords"],
    "full_text": "full clean version of what they're looking for"
}}

Rules:
- If they say "5+ years", set min_experience_years to 5
- If they say "Senior/Lead/Principal", extract seniority_level
- Extract all skills mentioned
- If skills unclear, use keywords field
- Return null for fields not mentioned
- confidence: your confidence in parsing (0-1)"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,  # Deterministic
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content
            
            # Clean markdown
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if "json" in response_text:
                    response_text = response_text.split("json", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]
            
            result = json.loads(response_text)
            result["confidence"] = 0.95
            result["parse_method"] = "llm"
            
            logger.info(f"Parsed query: {result['seniority_level']} {result['job_title']}")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._simple_parse(query)
        
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            return self._simple_parse(query)
    
    @staticmethod
    def _simple_parse(query: str) -> Dict:
        """Fallback simple query parsing"""
        
        query_lower = query.lower()
        
        # Common skill keywords
        skill_keywords = {
            "python": ["python", "py"],
            "java": ["java"],
            "javascript": ["javascript", "js", "typescript"],
            "aws": ["aws", "amazon"],
            "azure": ["azure"],
            "kubernetes": ["kubernetes", "k8s"],
            "docker": ["docker"],
            "postgresql": ["postgres", "postgresql", "postgres"],
            "react": ["react"],
            "fastapi": ["fastapi"],
            "django": ["django"],
            "spring": ["spring"],
        }
        
        # Extract skills
        skills = []
        for skill, keywords in skill_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    skills.append(skill)
                    break
        
        # Extract experience
        exp_years = 0
        for i in range(20, 0, -1):
            patterns = [f"{i}+", f"{i} +", f"{i} or more"]
            if any(p in query_lower for p in patterns):
                exp_years = i
                break
        
        # Extract seniority
        seniority = None
        if any(w in query_lower for w in ["senior", "lead", "principal", "architect"]):
            seniority = "Senior"
        elif any(w in query_lower for w in ["junior", "entry", "intern"]):
            seniority = "Junior"
        elif any(w in query_lower for w in ["mid", "intermediate"]):
            seniority = "Mid"
        
        return {
            "required_skills": skills,
            "nice_to_have_skills": [],
            "min_experience_years": exp_years,
            "seniority_level": seniority,
            "job_title": None,
            "search_text": query,
            "confidence": 0.6,  # Lower confidence for simple parsing
            "parse_method": "simple"
        }


# Singleton
_parser_instance = None

def get_query_parser() -> QueryParser:
    """Get query parser"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = QueryParser()
    return _parser_instance
