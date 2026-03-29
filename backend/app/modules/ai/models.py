"""
AI Module - Data Models
Pydantic models for AI features (isolated, no database impact)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ParsingStatus(str, Enum):
    """Status of resume parsing"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"  # If AI disabled


# ============================================================
# RESUME PARSER MODELS
# ============================================================

class ResumeEducation(BaseModel):
    """Education entry from parsed resume"""
    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None


class ResumeExperience(BaseModel):
    """Work experience entry"""
    company: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_years: Optional[float] = None
    description: Optional[str] = None


class ResumeCertification(BaseModel):
    """Certification entry"""
    name: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    credential_id: Optional[str] = None


class ParsedResumeData(BaseModel):
    """Structured resume data after parsing"""
    
    # Contact info
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    
    # Professional summary
    summary: Optional[str] = None
    
    # Work experience
    experiences: List[ResumeExperience] = Field(default_factory=list)
    total_experience_years: float = 0.0
    
    # Education
    education: List[ResumeEducation] = Field(default_factory=list)
    
    # Skills
    skills: List[str] = Field(default_factory=list)
    skill_categories: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Certifications
    certifications: List[ResumeCertification] = Field(default_factory=list)
    
    # Languages
    languages: List[str] = Field(default_factory=list)
    
    # Metadata
    parsing_confidence: float = 0.0  # 0-1, how confident the parser is
    raw_text_length: int = 0
    parsing_notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "(555) 123-4567",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "experiences": [
                    {
                        "company": "TechCorp",
                        "job_title": "Senior Developer",
                        "duration_years": 3
                    }
                ],
                "education": [
                    {
                        "degree": "BS",
                        "institution": "State University"
                    }
                ],
                "total_experience_years": 5.0,
                "parsing_confidence": 0.92
            }
        }


# ============================================================
# RESUME PARSING REQUEST/RESPONSE
# ============================================================

class ResumeParseRequest(BaseModel):
    """Request to parse a resume"""
    file_name: str = Field(..., description="Name of the uploaded file")
    file_size_bytes: int = Field(..., description="Size of file in bytes")


class ResumeParseResponse(BaseModel):
    """Response from resume parsing"""
    status: ParsingStatus
    success: bool
    message: str
    
    # Parsed data (if successful)
    parsed_data: Optional[ParsedResumeData] = None
    
    # Error details (if failed)
    error_code: Optional[str] = None
    error_details: Optional[str] = None
    
    # Performance metrics
    parsing_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "success": True,
                "message": "Resume parsed successfully",
                "parsed_data": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "skills": ["Python", "FastAPI"],
                    "total_experience_years": 5.0
                },
                "parsing_time_ms": 2500,
                "tokens_used": 450,
                "cost_estimate": 0.002
            }
        }


# ============================================================
# CANDIDATE MATCHING MODELS
# ============================================================

class JobRequirements(BaseModel):
    """Job posting requirements"""
    job_title: str
    company: str
    required_skills: List[str]
    nice_to_have_skills: List[str] = Field(default_factory=list)
    minimum_experience_years: float = 0.0
    preferred_education: Optional[str] = None
    description: Optional[str] = None


class CandidateScore(BaseModel):
    """Candidate score against a job"""
    candidate_id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    
    # Scoring breakdown
    overall_score: float = Field(..., ge=0, le=1, description="0-1 score")
    skills_match_score: float = Field(..., ge=0, le=1)
    experience_match_score: float = Field(..., ge=0, le=1)
    education_match_score: float = Field(..., ge=0, le=1)
    
    # Details
    matched_skills: List[str]
    missing_skills: List[str]
    score_percentage: int = Field(..., ge=0, le=100, description="0-100 percentage")
    recommendation: str  # "Strong Match", "Good Fit", "Consider", "Not Suitable"


# ============================================================
# EMAIL GENERATION MODELS
# ============================================================

class EmailGenerationRequest(BaseModel):
    """Request to generate recruiter email"""
    candidate_name: str
    candidate_email: str
    candidate_skills: List[str]
    job_title: str
    company_name: str
    candidate_experience_years: Optional[float] = None
    custom_context: Optional[str] = None


class GeneratedEmail(BaseModel):
    """Generated email"""
    subject: str
    body: str
    personalization_level: str  # "basic", "moderate", "high"
    estimated_response_rate: Optional[float] = None


# ============================================================
# BATCH PROCESSING MODELS
# ============================================================

class BatchParseRequest(BaseModel):
    """Request to parse multiple resumes"""
    resume_ids: List[str]
    priority: str = Field(default="normal", description="low, normal, high")


class BatchParseStatus(BaseModel):
    """Status of batch parsing"""
    batch_id: str
    total_resumes: int
    processed: int
    successful: int
    failed: int
    status: str  # "pending", "running", "completed", "failed"


# ============================================================
# ANALYTICS MODELS
# ============================================================

class ParsingAnalytics(BaseModel):
    """Analytics from parsing operations"""
    total_resumes_parsed: int
    successful_parses: int
    failed_parses: int
    average_parsing_time_ms: float
    average_accuracy: float
    total_cost_usd: float
    avg_cost_per_resume: float


class MatchingAnalytics(BaseModel):
    """Analytics from candidate matching"""
    total_comparisons: int
    average_match_score: float
    high_match_percentage: float  # % with score > 0.7
    average_time_ms: float
