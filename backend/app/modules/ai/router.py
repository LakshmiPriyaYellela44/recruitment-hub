"""
AI Module - API Router
Isolated API routes at /ai/* prefix
Does not interfere with existing routes
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.modules.ai.config import FeatureFlags, AIConfig
from app.modules.ai.resume_parser import get_resume_parser, ResumeParserException
from app.modules.ai.models import (
    ResumeParseResponse,
    ParsingStatus,
    ParsedResumeData
)

logger = logging.getLogger(__name__)

# Create router with /ai prefix - DOES NOT affect existing routes
router = APIRouter(prefix="/ai", tags=["ai"])


# ================================================================
# HEALTH CHECK
# ================================================================

@router.get("/health")
async def ai_health_check():
    """Check if AI features are available"""
    return {
        "status": "healthy",
        "ai_enabled": FeatureFlags.resume_parser_available(),
        "features": {
            "resume_parser": FeatureFlags.resume_parser_available(),
            "candidate_matcher": FeatureFlags.candidate_matcher_available(),
            "email_generator": FeatureFlags.email_generator_available()
        }
    }


# ================================================================
# RESUME PARSING ENDPOINTS
# ================================================================

@router.post("/parse-resume", response_model=ResumeParseResponse)
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    Parse uploaded resume file
    
    Supported formats: PDF, TXT
    
    Returns structured resume data or error
    
    **This endpoint does NOT modify existing data**
    **This is a new isolated feature**
    """
    
    # Check if feature enabled
    if not FeatureFlags.resume_parser_available():
        raise HTTPException(
            status_code=503,
            detail="Resume parser not available. Configure OPENAI_API_KEY to enable."
        )
    
    try:
        # Validate file size (max 10 MB)
        content = await file.read()
        if len(content) > AIConfig.MAX_RESUME_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {AIConfig.MAX_RESUME_SIZE_MB}MB"
            )
        
        # Parse resume
        parser = get_resume_parser()
        result = await parser.parse_resume_file(content, file.filename)
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error in parse_resume endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error processing resume"
        )


@router.post("/parse-resume-text", response_model=ResumeParseResponse)
async def parse_resume_text_endpoint(resume_text: str):
    """
    Parse resume from plain text
    
    **This endpoint does NOT modify existing data**
    **This is a new isolated feature**
    """
    
    # Check if feature enabled
    if not FeatureFlags.resume_parser_available():
        raise HTTPException(
            status_code=503,
            detail="Resume parser not available"
        )
    
    try:
        parser = get_resume_parser()
        result = await parser.parse_resume_text(resume_text)
        return result
    
    except Exception as e:
        logger.error(f"Error in parse_resume_text endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error processing resume"
        )


# ================================================================
# TEST ENDPOINT (for verification)
# ================================================================

@router.post("/test-parser")
async def test_parser():
    """
    Test resume parser with sample resume
    
    Use this to verify the parser is working correctly
    Does not require file upload
    """
    
    if not FeatureFlags.resume_parser_available():
        return {
            "status": "parser_disabled",
            "message": "Resume parser not enabled"
        }
    
    try:
        sample_resume = """
        John Doe
        john@example.com
        (555) 123-4567
        New York, NY
        
        Senior Python Developer with 5 years of experience
        
        EXPERIENCE:
        TechCorp Inc. - Senior Developer (2021-Present)
        - Led development of microservices architecture using FastAPI
        - Managed PostgreSQL databases with 1M+ records
        - Built REST APIs serving 10K+ requests/day
        
        StartupXYZ - Full Stack Developer (2019-2021)
        - Developed React UI with 50K+ daily active users
        - Implemented real-time notifications using WebSockets
        - 2 years building scalable systems
        
        SKILLS:
        Programming: Python, JavaScript, Go
        Frameworks: FastAPI, React, Django
        Databases: PostgreSQL, MongoDB, Redis
        Cloud: AWS, Docker, Kubernetes
        
        EDUCATION:
        BS Computer Science, State University (2019)
        
        CERTIFICATIONS:
        AWS Solutions Architect Associate
        Certified Kubernetes Administrator
        
        LANGUAGES:
        English (Native), Spanish (Fluent)
        """
        
        parser = get_resume_parser()
        result = await parser.parse_resume_text(sample_resume)
        
        return {
            "status": "test_complete",
            "result": result.dict()
        }
    
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return {
            "status": "test_failed",
            "error": str(e)
        }


# ================================================================
# CONFIGURATION ENDPOINT
# ================================================================

@router.get("/config")
async def get_config():
    """
    Get current AI configuration
    
    SECURITY: Only returns public non-sensitive config
    """
    return {
        "enabled": FeatureFlags.resume_parser_available(),
        "features": {
            "resume_parser": {
                "enabled": FeatureFlags.resume_parser_available(),
                "model": AIConfig.PARSER_MODEL if FeatureFlags.resume_parser_available() else None
            },
            "candidate_matcher": {
                "enabled": FeatureFlags.candidate_matcher_available()
            },
            "email_generator": {
                "enabled": FeatureFlags.email_generator_available()
            }
        },
        "limits": {
            "max_resume_size_mb": AIConfig.MAX_RESUME_SIZE_MB,
            "parser_timeout_seconds": AIConfig.PARSER_TIMEOUT
        }
    }


# ================================================================
# ERROR HANDLER
# ================================================================

@router.get("/info")
async def ai_info():
    """
    Get information about AI module
    
    Shows which features are available and why others might be disabled
    """
    
    status_dict = {
        "python_version": "3.8+",
        "module_version": "1.0.0",
        "last_updated": "2026-03-29"
    }
    
    # Resume Parser status
    if FeatureFlags.resume_parser_available():
        status_dict["resume_parser"] = {
            "status": "available",
            "model": AIConfig.PARSER_MODEL,
            "cost_per_parse": "$0.002-0.005"
        }
    else:
        status_dict["resume_parser"] = {
            "status": "disabled",
            "reason": "OPENAI_API_KEY not configured" if not AIConfig.OPENAI_API_KEY else "Feature disabled"
        }
    
    # Candidate Matcher status
    if FeatureFlags.candidate_matcher_available():
        status_dict["candidate_matcher"] = {
            "status": "available",
            "backend": "Pinecone"
        }
    else:
        status_dict["candidate_matcher"] = {
            "status": "disabled",
            "reason": "Feature disabled or Pinecone not configured"
        }
    
    # Email Generator status
    if FeatureFlags.email_generator_available():
        status_dict["email_generator"] = {
            "status": "available",
            "model": AIConfig.EMAIL_MODEL
        }
    else:
        status_dict["email_generator"] = {
            "status": "disabled",
            "reason": "Feature disabled or OpenAI not configured"
        }
    
    return status_dict


# ================================================================
# RESUME SCORING ENDPOINTS (NEW)
# ================================================================

@router.post("/score-resume")
async def score_resume(parsed_data: dict):
    """
    Score a parsed resume (0-100)
    
    Input: Parsed resume data from /parse-resume endpoint
    Output: Score with breakdown
    
    Example:
    {
        "total_experience_years": 5,
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "education": [{"degree": "BS", "institution": "State Univ"}]
    }
    """
    
    try:
        from app.modules.ai.resume_scorer import ResumeScorer
        from app.modules.ai.models import ParsedResumeData
        
        # Convert dict to model
        resume_data = ParsedResumeData(**parsed_data)
        
        # Score
        score = ResumeScorer.calculate_score(resume_data)
        
        return {
            "status": "success",
            "score": score
        }
    
    except Exception as e:
        logger.error(f"Error scoring resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# CANDIDATE SEARCH ENDPOINTS (NEW)
# ================================================================

@router.post("/search-candidates")
async def search_candidates_endpoint(
    query: str,
    min_score: int = 60,
    return_count: int = 75
):
    """
    Search for candidates matching recruiter query
    
    This is the main feature:
    - Parses recruiter query
    - Searches vector DB for similar candidates
    - Ranks by multiple factors
    - Returns top candidates
    
    Example query: "Find senior Python developers with 5+ years AWS experience"
    
    Returns top 75 candidates (or fewer if not available)
    with scores and recommendations
    """
    
    try:
        from app.modules.ai.candidate_search import CandidateRanker
        
        if not FeatureFlags.resume_parser_available():
            raise HTTPException(
                status_code=503,
                detail="Candidate search not available. Configure OPENAI_API_KEY."
            )
        
        ranker = CandidateRanker()
        results = ranker.search_candidates(
            query=query,
            min_score=min_score,
            return_count=return_count
        )
        
        return results
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error searching candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-candidates-stats")
async def get_candidate_search_stats():
    """
    Get statistics about candidates in vector DB
    
    Shows:
    - Total candidates indexed
    - Average score
    - Popular skills
    - Experience distribution
    """
    
    try:
        from app.modules.ai.vector_db import get_vector_db
        
        vector_db = get_vector_db()
        stats = vector_db.get_index_stats()
        
        if stats.get("status") == "error":
            raise HTTPException(status_code=503, detail="Vector DB unavailable")
        
        return {
            "status": "success",
            "candidates_indexed": stats.get("total_vectors", 0),
            "vector_db": vector_db.__class__.__name__ if vector_db.enabled else "disabled"
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# BULK OPERATIONS
# ================================================================

@router.post("/store-candidate-for-search")
async def store_candidate_for_search(candidate_data: dict):
    """
    Store candidate in vector DB for semantic search
    
    Call after parsing resume
    
    Input:
    {
        "candidate_id": "uuid",
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "AWS"],
        "experience_years": 5,
        "resume_score": 75,
        "education": "BS Computer Science",
        "summary": "Senior Python developer..."
    }
    """
    
    try:
        from app.modules.ai.vector_db import get_vector_db
        
        vector_db = get_vector_db()
        
        if not vector_db.enabled:
            return {
                "status": "skipped",
                "reason": "Vector DB disabled - configure PINECONE_API_KEY"
            }
        
        success = vector_db.store_candidate(
            candidate_data.get("candidate_id"),
            candidate_data
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Candidate {candidate_data.get('candidate_id')} stored"
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to store candidate"
            }
    
    except Exception as e:
        logger.error(f"Error storing candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))
