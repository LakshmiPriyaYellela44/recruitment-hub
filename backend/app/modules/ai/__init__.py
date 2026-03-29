"""
AI Module - Isolated AI Features
Does not affect existing system
All features are optional and gracefully degrade if not configured
"""

from app.modules.ai.resume_parser import get_llm_client
from app.modules.ai.config import AIConfig
from app.modules.ai.models import (
    ParsedResumeData,
    ResumeParseResponse,
    ParsingStatus
)

__all__ = [
    "get_llm_client",
    "AIConfig",
    "ParsedResumeData",
    "ResumeParseResponse",
    "ParsingStatus",
]
