"""
Query Parser
Understands recruiter search queries and extracts requirements
Uses LLM to parse natural language into structured requirements
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional
from app.modules.ai.config import AIConfig, FeatureFlags

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
        """Initialize query parser with available LLM"""
        self.enabled = FeatureFlags.resume_parser_available() # Reusing same check

        if not self.enabled:
            logger.warning("Query parser disabled - No API keys configured")
            self.client = None
            return

        try:
            # Import client inside to avoid ModuleNotFoundError at top level
            if AIConfig.USE_GOOGLE_GEMINI and AIConfig.GOOGLE_API_KEY:
                import google.generativeai as genai
                genai.configure(api_key=AIConfig.GOOGLE_API_KEY)
                self.client = genai
                self.use_google = True
                logger.info("✅ Query parser using Google Gemini")
            elif AIConfig.OPENAI_API_KEY:
                from openai import OpenAI
                self.client = OpenAI(api_key=AIConfig.OPENAI_API_KEY)
                self.use_google = False
                logger.info("✅ Query parser using OpenAI")
            else:
                self.enabled = False
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize query parser: {e}")
            self.enabled = False
            self.client = None

    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            model_name = AIConfig.PARSER_MODEL
            model = self.client.GenerativeModel(model_name)
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini error in query parser: {e}")
            raise

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=AIConfig.PARSER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error in query parser: {e}")
            raise

    def parse_query(self, query: str) -> Dict[str, any]:
        """
        Parse recruiter query (Synchronous wrapper for legacy compatibility)
        """
        try:
            # Try to get the running loop
            try:
                loop = asyncio.get_running_loop()
                # If a loop is already running, we can't use asyncio.run()
                # Instead, we should ideally await parse_query_async in the caller.
                # But to maintain current sync signature, we use a thread-safe call if possible
                # or just run it and hope for the best in this specific sync context.
                # However, chat_router.py calls this from an async function but doesn't await it.
                return asyncio.run_coroutine_threadsafe(self.parse_query_async(query), loop).result()
            except RuntimeError:
                # No loop running, safe to use asyncio.run()
                return asyncio.run(self.parse_query_async(query))
        except Exception as e:
            logger.error(f"Sync parse_query failed: {e}")
            return self._simple_parse(query)

    async def parse_query_async(self, query: str) -> Dict[str, any]:
        """
        Parse recruiter query (Async version)
        """

        if not self.enabled:
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

            if self.use_google:
                response_text = await self._call_gemini(prompt)
            else:
                response_text = await self._call_openai(prompt)

            # Clean markdown
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if "json" in response_text:
                    response_text = response_text.split("json", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]

            result = json.loads(response_text)
            result["confidence"] = 0.95
            result["parse_method"] = "llm"

            logger.info(f"Parsed query: {result.get('seniority_level')} {result.get('job_title')}")
            return result

        except Exception as e:
            logger.error(f"Error in parse_query_async: {e}")
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
            "confidence": 0.6,
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
 
