import io
import re
from typing import Dict, List, Optional
from PyPDF2 import PdfReader
from docx import Document
import logging
import asyncio
from app.aws_services.s3_client import S3Client

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parser for resume documents."""
    
    @staticmethod
    def _is_s3_key(file_path: str) -> bool:
        """Detect if file_path is an S3 key (not a local path)."""
        # Local paths have backslashes (Windows), forward slashes at start (Unix), or drive letters
        # S3 keys typically don't have these patterns
        if '\\' in file_path:  # Windows path
            return False
        if file_path.startswith('/'):  # Unix path
            return False
        if len(file_path) > 1 and file_path[1] == ':':  # Drive letter (C:, D:, etc.)
            return False
        # If it looks like a filename with UUID prefix (no slashes), likely S3 key
        return True
    
    @staticmethod
    async def _download_from_s3(s3_key: str) -> Optional[bytes]:
        """Download file from S3 using S3Client with retries."""
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                s3_client = S3Client()
                logger.info(f"[_download_from_s3] Downloading from S3 (attempt {attempt + 1}/{max_retries}): {s3_key}")
                content = await s3_client.download_file(s3_key)
                if content is None:
                    logger.warning(f"[_download_from_s3] File not found in S3: {s3_key}")
                    return None  # File doesn't exist, no point retrying
                logger.info(f"[_download_from_s3] Downloaded {len(content)} bytes successfully on attempt {attempt + 1}")
                return content
            except Exception as e:
                logger.warning(f"[_download_from_s3] Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"[_download_from_s3] Waiting {retry_delay} seconds before retry...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"[_download_from_s3] Max retries exceeded for {s3_key}: {str(e)}")
                    raise
        
        return None
    
    @staticmethod
    async def parse_pdf(file_path: str) -> Dict:
        """Parse PDF resume from local file or S3 (ASYNC)."""
        try:
            logger.info(f"[parse_pdf] Starting PDF parse for file_path: {file_path[:100]}")
            # Try to read from S3 if it looks like an S3 key
            is_s3 = ResumeParser._is_s3_key(file_path)
            logger.info(f"[parse_pdf] S3 key detection: is_s3={is_s3}")
            
            if is_s3:
                logger.info(f"[parse_pdf] Attempting S3 download for: {file_path}")
                pdf_content = await ResumeParser._download_from_s3(file_path)
                
                if pdf_content is None:
                    error_msg = f"Could not download resume from S3: {file_path}"
                    logger.error(f"[parse_pdf] {error_msg}")
                    return {"error": error_msg}
                if len(pdf_content) == 0:
                    error_msg = f"Downloaded PDF file is empty from S3: {file_path}"
                    logger.error(f"[parse_pdf] {error_msg}")
                    return {"error": error_msg}
                logger.info(f"[parse_pdf] Successfully downloaded {len(pdf_content)} bytes from S3")
                file_obj = io.BytesIO(pdf_content)
            else:
                # Local file
                logger.info(f"[parse_pdf] Reading local file: {file_path}")
                file_obj = open(file_path, "rb")
            
            text = ""
            try:
                reader = PdfReader(file_obj)
                if len(reader.pages) == 0:
                    error_msg = f"PDF file has no pages: {file_path}"
                    logger.error(f"[parse_pdf] {error_msg}")
                    if not isinstance(file_obj, io.BytesIO):
                        file_obj.close()
                    return {"error": error_msg}
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                    except Exception as page_err:
                        logger.warning(f"[parse_pdf] Failed to extract text from page {page_num}: {str(page_err)}")
                        # Continue with other pages
                        continue
            except Exception as pdf_err:
                error_msg = f"Failed to read PDF structure: {str(pdf_err)}"
                logger.error(f"[parse_pdf] {error_msg}")
                if not isinstance(file_obj, io.BytesIO):
                    file_obj.close()
                return {"error": error_msg}
            
            if not isinstance(file_obj, io.BytesIO):
                file_obj.close()
            
            # Validate text extraction
            if not text or len(text.strip()) == 0:
                error_msg = f"No text could be extracted from PDF: {file_path}"
                logger.error(f"[parse_pdf] {error_msg}")
                return {"error": error_msg}
            
            logger.info(f"[parse_pdf] Successfully extracted {len(text)} characters from PDF")
            return ResumeParser._extract_data(text)
        except Exception as e:
            logger.error(f"[parse_pdf] Exception during PDF parsing: {str(e)}", exc_info=True)
            return {"error": f"PDF parsing failed: {str(e)}"}
    
    @staticmethod
    async def parse_docx(file_path: str) -> Dict:
        """Parse DOCX resume from local file or S3 (ASYNC)."""
        try:
            logger.info(f"[parse_docx] Starting DOCX parse for file_path: {file_path[:100]}")
            # Try to read from S3 if it looks like an S3 key
            is_s3 = ResumeParser._is_s3_key(file_path)
            logger.info(f"[parse_docx] S3 key detection: is_s3={is_s3}")
            
            if is_s3:
                logger.info(f"[parse_docx] Attempting S3 download for: {file_path}")
                docx_content = await ResumeParser._download_from_s3(file_path)
                
                if docx_content is None:
                    error_msg = f"Could not download resume from S3: {file_path}"
                    logger.error(f"[parse_docx] {error_msg}")
                    return {"error": error_msg}
                if len(docx_content) == 0:
                    error_msg = f"Downloaded DOCX file is empty from S3: {file_path}"
                    logger.error(f"[parse_docx] {error_msg}")
                    return {"error": error_msg}
                logger.info(f"[parse_docx] Successfully downloaded {len(docx_content)} bytes from S3")
                file_obj = io.BytesIO(docx_content)
            else:
                # Local file
                logger.info(f"[parse_docx] Reading local file: {file_path}")
                file_obj = open(file_path, "rb")
            
            try:
                doc = Document(file_obj)
                if not doc.paragraphs:
                    error_msg = f"DOCX file has no paragraphs: {file_path}"
                    logger.error(f"[parse_docx] {error_msg}")
                    if not isinstance(file_obj, io.BytesIO):
                        file_obj.close()
                    return {"error": error_msg}
                
                text = "\n".join([para.text for para in doc.paragraphs])
            except Exception as docx_err:
                error_msg = f"Failed to read DOCX structure: {str(docx_err)}"
                logger.error(f"[parse_docx] {error_msg}")
                if not isinstance(file_obj, io.BytesIO):
                    file_obj.close()
                return {"error": error_msg}
            
            if not isinstance(file_obj, io.BytesIO):
                file_obj.close()
            
            # Validate text extraction
            if not text or len(text.strip()) == 0:
                error_msg = f"No text could be extracted from DOCX: {file_path}"
                logger.error(f"[parse_docx] {error_msg}")
                return {"error": error_msg}
            
            logger.info(f"[parse_docx] Successfully extracted {len(text)} characters from DOCX")
            return ResumeParser._extract_data(text)
        except Exception as e:
            logger.error(f"[parse_docx] Exception during DOCX parsing: {str(e)}", exc_info=True)
            return {"error": f"DOCX parsing failed: {str(e)}"}
    
    @staticmethod
    def _extract_data(text: str) -> Dict:
        """Extract structured data from resume text."""
        logger.info(f"[_extract_data] Starting extraction from text of {len(text)} characters")
        logger.info(f"[_extract_data] First 500 chars: {text[:500]}")
        
        data = {
            "name": ResumeParser._extract_name(text),
            "email": ResumeParser._extract_email(text),
            "phone": ResumeParser._extract_phone(text),
            "skills": ResumeParser._extract_skills(text),
            "experiences": ResumeParser._extract_experiences(text),
            "educations": ResumeParser._extract_educations(text),
            "summary": ResumeParser._extract_summary(text)
        }
        
        logger.info(f"[_extract_data] Extracted: name={data['name']}, email={data['email']}, phone={data['phone']}")
        logger.info(f"[_extract_data] Skills found: {len(data['skills'])} → {data['skills']}")
        logger.info(f"[_extract_data] Experiences found: {len(data['experiences'])}")
        logger.info(f"[_extract_data] Educations found: {len(data['educations'])}")
        
        # Validate that we extracted meaningful data
        has_email = data.get('email') is not None
        has_phone = data.get('phone') is not None
        has_skills = len(data.get('skills', [])) > 0
        has_experiences = len(data.get('experiences', [])) > 0
        has_educations = len(data.get('educations', [])) > 0
        
        # At least one contact method OR meaningful resume data
        has_contact = has_email or has_phone
        has_resume_data = has_skills or has_experiences or has_educations
        
        if not (has_contact or has_resume_data):
            error_msg = "Could not extract meaningful data from resume (no contact info and no skills/experience/education found)"
            logger.warning(f"[_extract_data] {error_msg}")
            # Don't return error yet - service will decide if this is acceptable
            logger.warning(f"[_extract_data] Returning extracted data with minimal information")
        
        return data
    
    @staticmethod
    def _extract_name(text: str) -> Optional[str]:
        """Extract name from resume."""
        lines = text.split("\n")
        # Assume first non-empty line might be name
        for line in lines:
            if line.strip() and len(line.strip().split()) <= 4:
                return line.strip()
        return None
    
    @staticmethod
    def _extract_email(text: str) -> Optional[str]:
        """Extract email from resume."""
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    @staticmethod
    def _extract_phone(text: str) -> Optional[str]:
        """Extract phone number from resume."""
        phone_pattern = r"\+?1?\d{9,15}"
        match = re.search(phone_pattern, text)
        return match.group(0) if match else None
    
    @staticmethod
    def _extract_skills(text: str) -> List[str]:
        """Extract skills from resume."""
        common_skills = [
            "python", "java", "javascript", "typescript", "react", "node.js",
            "django", "fastapi", "sql", "postgresql", "mongodb", "aws",
            "docker", "kubernetes", "git", "agile", "scrum", "leadership",
            "communication", "teamwork", "project management", "html", "css",
            "vue.js", "angular", "spring", "c++", "c#", ".net", "golang",
            "rust", "php", "ruby", "rails", "devops", "ci/cd", "jenkins",
            "gitlab", "github", "terraform", "cloudformation"
        ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    @staticmethod
    def _extract_experiences(text: str) -> List[Dict]:
        """Extract work experiences from resume."""
        # Simple extraction - in production would use more sophisticated NLP
        experiences = []
        
        # Look for common job title patterns
        job_patterns = [
            r"(?:Senior|Junior|Lead)?\s*(?:Software|Data|Product|Project|Business)?\s*(?:Engineer|Developer|Analyst|Manager)",
            r"(?:Full[- ]?Stack|Frontend|Backend|DevOps|QA)\s*(?:Engineer|Developer)"
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                experiences.append({
                    "title": match.group(0),
                    "company": "Unknown",
                    "years": None
                })
        
        return experiences[:3]  # Return top 3
    
    @staticmethod
    def _extract_educations(text: str) -> List[Dict]:
        """Extract education from resume."""
        educations = []
        
        degrees = ["bachelor", "master", "phd", "b.s.", "b.a.", "m.s.", "m.a.", "m.b.a."]
        fields = ["computer science", "engineering", "business", "mathematics", "physics"]
        
        text_lower = text.lower()
        
        for degree in degrees:
            if degree in text_lower:
                for field in fields:
                    if field in text_lower:
                        educations.append({
                            "degree": degree.upper(),
                            "field": field.title(),
                            "institution": "Unknown"
                        })
                        break
        
        return educations[:3]
    
    @staticmethod
    def _extract_summary(text: str) -> Optional[str]:
        """Extract professional summary."""
        lines = text.split("\n")
        # Look for summary or objective section
        for i, line in enumerate(lines):
            if "summary" in line.lower() or "objective" in line.lower():
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        
        # Otherwise return first few sentences
        sentences = text.split(".")[:2]
        return ". ".join(sentences) if sentences else None
