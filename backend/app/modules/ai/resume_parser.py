"""
Resume Parser
Isolated implementation - does not affect existing system
Supports both OpenAI and Google Gemini (completely FREE with Google)
"""

import io
import json
import time
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from PyPDF2 import PdfReader

from app.modules.ai.config import AIConfig, FeatureFlags
from app.modules.ai.models import (
    ParsedResumeData,
    ResumeEducation,
    ResumeExperience,
    ResumeCertification,
    ParsingStatus,
    ResumeParseResponse
)

logger = logging.getLogger(__name__)


def get_llm_client():
    """Get LLM client - supports both Google Gemini (FREE) and OpenAI"""
    
    logger.debug(f"DEBUG: USE_GOOGLE_GEMINI={AIConfig.USE_GOOGLE_GEMINI}, API_KEY_EXISTS={bool(AIConfig.GOOGLE_API_KEY)}")
    
    if AIConfig.USE_GOOGLE_GEMINI and AIConfig.GOOGLE_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=AIConfig.GOOGLE_API_KEY)
            logger.info("✅ Using Google Gemini (FREE)")
            return genai
        except ImportError:
            logger.warning("google-generativeai not installed. Install: pip install google-generativeai")
            return None
        except Exception as e:
            logger.error(f"Failed to init Google Gemini: {e}")
            return None
    
    elif AIConfig.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            logger.info("✅ Using OpenAI GPT-3.5")
            return OpenAI(api_key=AIConfig.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to init OpenAI: {e}")
            return None
    
    logger.error(f"No LLM provider available: USE_GOOGLE_GEMINI={AIConfig.USE_GOOGLE_GEMINI}, GOOGLE_KEY_EMPTY={not AIConfig.GOOGLE_API_KEY}, OPENAI_KEY_EMPTY={not AIConfig.OPENAI_API_KEY}")
    return None


class ResumeParserException(Exception):
    """Base exception for resume parsing"""
    pass


class ResumeParser:
    """
    Resume parser using Google Gemini (FREE) or OpenAI (paid)
    
    IMPORTANT:
    - Uses GOOGLE_API_KEY if available (FREE tier exists)
    - Falls back to OpenAI if Google key not available
    - If neither key present, returns graceful error
    - Does not affect existing system
    """
    
    def __init__(self):
        """Initialize parser with available LLM"""
        self.enabled = FeatureFlags.resume_parser_available()
        
        if not self.enabled:
            logger.warning("Resume parser disabled - No API keys configured")
            self.client = None
            return
        
        try:
            self.client = get_llm_client()
            self.use_google = AIConfig.USE_GOOGLE_GEMINI and self.client
            self.model = AIConfig.PARSER_MODEL
            logger.info(f"✅ Resume parser ready. Model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize parser: {e}")
            self.enabled = False
            self.client = None
    
    # ================================================================
    # PUBLIC INTERFACE
    # ================================================================
    
    async def parse_resume_file(self, file_content: bytes, file_name: str) -> ResumeParseResponse:
        """
        Parse resume from uploaded file (PDF or text)
        
        Args:
            file_content: Raw file bytes
            file_name: Name of the file (for extension detection)
        
        Returns:
            ResumeParseResponse with parsed data or error
        """
        
        if not self.enabled:
            return ResumeParseResponse(
                status=ParsingStatus.SKIPPED,
                success=False,
                message="Resume parser not enabled. Configure OPENAI_API_KEY to enable.",
                error_code="PARSER_DISABLED"
            )
        
        try:
            start_time = time.time()
            
            # Extract text based on file type
            if file_name.lower().endswith('.pdf'):
                text = self._extract_text_from_pdf(file_content)
            elif file_name.lower().endswith(('.txt', '.docx')):
                # For now, just handle PDF
                text = file_content.decode('utf-8', errors='ignore')
            else:
                return ResumeParseResponse(
                    status=ParsingStatus.FAILED,
                    success=False,
                    message=f"Unsupported file type: {file_name}",
                    error_code="UNSUPPORTED_FILE_TYPE"
                )
            
            # Validate text extraction
            if not text or len(text.strip()) < 100:
                return ResumeParseResponse(
                    status=ParsingStatus.FAILED,
                    success=False,
                    message="Failed to extract text from resume",
                    error_code="TEXT_EXTRACTION_FAILED"
                )
            
            # Parse with GPT
            parsed_data = await self._parse_with_gpt(text)
            
            # Calculate metrics
            parsing_time_ms = int((time.time() - start_time) * 1000)
            
            return ResumeParseResponse(
                status=ParsingStatus.SUCCESS,
                success=True,
                message="Resume parsed successfully",
                parsed_data=parsed_data,
                parsing_time_ms=parsing_time_ms,
                cost_estimate=0.002  # ~$0.002 per GPT-3.5 call
            )
        
        except Exception as e:
            logger.error(f"Error parsing resume: {e}", exc_info=True)
            return ResumeParseResponse(
                status=ParsingStatus.FAILED,
                success=False,
                message="Error parsing resume",
                error_code="PARSING_ERROR",
                error_details=str(e)
            )
    
    async def parse_resume_text(self, text: str) -> ResumeParseResponse:
        """Parse resume from plain text"""
        
        if not self.enabled:
            return ResumeParseResponse(
                status=ParsingStatus.SKIPPED,
                success=False,
                message="Resume parser not enabled",
                error_code="PARSER_DISABLED"
            )
        
        try:
            start_time = time.time()
            
            # Validate input
            if not text or len(text.strip()) < 50:
                return ResumeParseResponse(
                    status=ParsingStatus.FAILED,
                    success=False,
                    message="Resume text too short",
                    error_code="TEXT_TOO_SHORT"
                )
            
            # Parse with GPT
            parsed_data = await self._parse_with_gpt(text)
            parsing_time_ms = int((time.time() - start_time) * 1000)
            
            return ResumeParseResponse(
                status=ParsingStatus.SUCCESS,
                success=True,
                message="Resume parsed successfully",
                parsed_data=parsed_data,
                parsing_time_ms=parsing_time_ms
            )
        
        except Exception as e:
            logger.error(f"Error parsing resume text: {e}", exc_info=True)
            return ResumeParseResponse(
                status=ParsingStatus.FAILED,
                success=False,
                message="Error parsing resume",
                error_code="PARSING_ERROR",
                error_details=str(e)
            )
    
    # ================================================================
    # PRIVATE METHODS
    # ================================================================
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API (FREE)"""
        try:
            import google.generativeai as genai
            
            # Use the updated model names (gemini-pro is deprecated)
            model_name = AIConfig.PARSER_MODEL or 'gemini-2.0-flash'
            model = genai.GenerativeModel(model_name)
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            text = response.text.strip()
            logger.debug(f"✅ Gemini response received ({len(text)} chars)")
            return text
        
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API (paid)"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=AIConfig.OPENAI_API_KEY)
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model=AIConfig.PARSER_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=800
                ),
                timeout=AIConfig.PARSER_TIMEOUT
            )
            
            text = response.choices[0].message.content.strip()
            logger.debug(f"✅ OpenAI response received ({len(text)} chars)")
            return text
        
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text += page.extract_text()
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
            
            return text
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise ResumeParserException(f"Failed to read PDF: {e}")
    
    async def _parse_with_gpt(self, resume_text: str) -> ParsedResumeData:
        """
        Parse resume using either Google Gemini (FREE) or OpenAI
        
        Returns structured data in JSON format
        """
        
        # Limit text to avoid token limits
        text_limit = resume_text[:3000]  # ~750 tokens
        
        # Craft the prompt
        prompt = f"""Extract structured information from this resume. Return ONLY a valid JSON object with no markdown formatting.

Resume text:
{text_limit}

Extract ALL available information. For missing fields, use null. For arrays, use empty arrays if nothing found.

Return this JSON structure exactly:
{{
    "name": null or "string",
    "email": null or "string",
    "phone": null or "string",
    "location": null or "string",
    "summary": null or "string",
    "experiences": [
        {{
            "company": "string or null",
            "job_title": "string or null",
            "start_date": "string or null",
            "end_date": "string or null",
            "duration_years": null or number,
            "description": "string or null"
        }}
    ],
    "total_experience_years": 0,
    "education": [
        {{
            "degree": "string or null",
            "institution": "string or null",
            "field_of_study": "string or null",
            "graduation_year": null or number
        }}
    ],
    "skills": ["array", "of", "skills"],
    "skill_categories": {{}},
    "certifications": [
        {{
            "name": "string",
            "issuer": "string or null",
            "issue_date": "string or null",
            "credential_id": "string or null"
        }}
    ],
    "languages": ["array", "of", "languages"],
    "parsing_confidence": 0.0 to 1.0
}}"""
        
        try:
            if AIConfig.USE_GOOGLE_GEMINI and AIConfig.GOOGLE_API_KEY:
                response_text = await self._call_gemini(prompt)
            else:
                response_text = await self._call_openai(prompt)
            
            # Clean markdown if present
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if "json" in response_text:
                    response_text = response_text.split("json", 1)[1]
                response_text = response_text.rsplit("```", 1)[0]
            
            # Parse JSON
            parsed_json = json.loads(response_text.strip())
            
            # Convert to Pydantic model with validation
            parsed_data = ParsedResumeData(**parsed_json)
            parsed_data.raw_text_length = len(resume_text)
            
            # Calculate total experience if not provided
            if parsed_data.total_experience_years == 0 and parsed_data.experiences:
                parsed_data.total_experience_years = sum(
                    (exp.duration_years or 0) for exp in parsed_data.experiences
                )
            
            logger.info(f"Successfully parsed resume: {parsed_data.name}")
            return parsed_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ResumeParserException(f"Invalid JSON from GPT: {e}")
        
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ResumeParserException(f"OpenAI API error: {e}")
        
        except asyncio.TimeoutError:
            logger.error(f"Parsing timeout after {AIConfig.PARSER_TIMEOUT}s")
            raise ResumeParserException("Parsing timeout")
        
        except Exception as e:
            logger.error(f"Unexpected error in GPT parsing: {e}")
            raise ResumeParserException(f"Parsing failed: {e}")


# ================================================================
# SINGLETON INSTANCE
# ================================================================

_parser_instance: Optional[ResumeParser] = None


def get_resume_parser() -> ResumeParser:
    """Get or create resume parser instance (dependency injection)"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ResumeParser()
    return _parser_instance
