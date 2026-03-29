"""
AI Module - Configuration
Isolated configuration for AI features
Does NOT affect existing system
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Ensure .env is loaded first (critical for API keys)
load_dotenv()

# ============================================================
# OPTIONAL: AI Configuration
# If these env vars are not set, AI features gracefully disable
# ============================================================

class AIConfig:
    """AI module configuration - entirely optional"""
    
    # ===== API KEYS (gracefully optional) =====
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")  # For Google Gemini
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    
    # ===== LLM PROVIDER SELECTION =====
    # Use "google_gemini" for free, "openai" for GPT
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google_gemini").lower()
    USE_GOOGLE_GEMINI = os.getenv("USE_GOOGLE_GEMINI", "true").lower() == "true"
    
    # ===== VECTOR DB PROVIDER SELECTION =====
    # Use "chroma" for free/local, "pinecone" for cloud
    VECTOR_DB_PROVIDER = os.getenv("VECTOR_DB_PROVIDER", "chroma").lower()
    USE_CHROMA = os.getenv("USE_CHROMA", "true").lower() == "true"
    
    # Feature flags (can be disabled)
    ENABLE_RESUME_PARSER = os.getenv("ENABLE_RESUME_PARSER", "true").lower() == "true"
    ENABLE_CANDIDATE_MATCHER = os.getenv("ENABLE_CANDIDATE_MATCHER", "false").lower() == "true"
    ENABLE_EMAIL_GENERATOR = os.getenv("ENABLE_EMAIL_GENERATOR", "false").lower() == "true"
    
    # ===== MODEL CHOICES =====
    # LLM Models - using gemini-1.5-flash for better free tier compatibility
    PARSER_MODEL = "gemini-1.5-flash" if USE_GOOGLE_GEMINI else os.getenv("PARSER_MODEL", "gpt-3.5-turbo")
    EMBEDDING_MODEL = "embedding-001" if USE_GOOGLE_GEMINI else "text-embedding-3-small"
    EMAIL_MODEL = PARSER_MODEL
    
    # ===== VECTOR DB CONFIGURATION =====
    # Chroma configuration (free, local)
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    CHROMA_COLLECTION_NAME = "recruitment-hub-candidates"
    
    # Pinecone configuration (paid, cloud)
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "recruitment-hub")
    PINECONE_DIMENSION = 768 if USE_GOOGLE_GEMINI else 1536
    
    # Timeouts and limits
    PARSER_TIMEOUT = int(os.getenv("PARSER_TIMEOUT", "30"))  # seconds
    MAX_RESUME_SIZE_MB = int(os.getenv("MAX_RESUME_SIZE_MB", "10"))
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if AI features are enabled"""
        has_llm = bool(cls.GOOGLE_API_KEY or cls.OPENAI_API_KEY)
        return cls.ENABLE_RESUME_PARSER and has_llm
    
    @classmethod
    def validate(cls) -> tuple[bool, str]:
        """Validate configuration - returns (is_valid, error_message)"""
        if cls.USE_GOOGLE_GEMINI:
            if not cls.GOOGLE_API_KEY:
                return False, "GOOGLE_API_KEY not set in environment"
        else:
            if not cls.OPENAI_API_KEY:
                return False, "OPENAI_API_KEY not set in environment"
        
        if cls.USE_CHROMA:
            # Chroma needs no API key - runs locally
            return True, ""
        else:
            if not cls.PINECONE_API_KEY:
                return False, "PINECONE_API_KEY not set for vector search"
        
        return True, ""


# ============================================================
# Feature flags for graceful degradation
# ============================================================

class FeatureFlags:
    """Feature flags - turn features on/off without code changes"""
    
    @staticmethod
    def resume_parser_available() -> bool:
        """Check if resume parser is available and configured"""
        has_llm = bool(AIConfig.GOOGLE_API_KEY or AIConfig.OPENAI_API_KEY)
        return AIConfig.ENABLE_RESUME_PARSER and has_llm
    
    @staticmethod
    def candidate_matcher_available() -> bool:
        """Check if candidate matcher is available"""
        has_llm = bool(AIConfig.GOOGLE_API_KEY or AIConfig.OPENAI_API_KEY)
        has_vector_db = bool(AIConfig.PINECONE_API_KEY) or AIConfig.USE_CHROMA
        return (
            AIConfig.ENABLE_CANDIDATE_MATCHER 
            and has_llm
            and has_vector_db
        )
    
    @staticmethod
    def email_generator_available() -> bool:
        """Check if email generator is available"""
        has_llm = bool(AIConfig.GOOGLE_API_KEY or AIConfig.OPENAI_API_KEY)
        return AIConfig.ENABLE_EMAIL_GENERATOR and has_llm
