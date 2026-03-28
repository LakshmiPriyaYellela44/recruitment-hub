from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.models import UserRole, EmailTemplate
from app.utils.auth_utils import get_current_user, get_current_user_with_query_token, require_subscription
from app.modules.recruiter.schemas import (
    CandidateSearchFilters,
    SendEmailRequest,
    SendEmailWithTemplateRequest,
    CandidateSearchResult,
    EmailResponse
)
from app.modules.recruiter.service import RecruiterService
from app.modules.email.template_service import EmailTemplateService
from app.modules.resume.service import ResumeService
from app.core.exceptions import NotFoundException
from uuid import UUID
import logging
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruiters", tags=["recruiters"])


@router.get("/search")
async def search_candidates(
    skills: str = Query(None, description="Comma-separated skills"),
    experience: str = Query(None, description="Search by job title or company"),
    education: str = Query(None, description="Search by degree or institution"),
    keyword: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Search candidates (BASIC subscription)."""
    # Check if recruiter
    if current_user.role.value != UserRole.RECRUITER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can search candidates"
        )
    
    service = RecruiterService(db)
    
    # Build filters
    skills_list = [s.strip() for s in skills.split(",")] if skills else None
    filters = CandidateSearchFilters(
        skills=skills_list,
        keyword=keyword,
        experience=experience,
        education=education
    )
    
    candidates, total = await service.search_candidates(
        current_user.id,
        filters,
        limit=limit,
        offset=offset
    )
    
    return {
        "candidates": candidates,  # Already dicts, no need to convert
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/candidate/{candidate_id}")
async def get_candidate_profile(
    candidate_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get candidate profile (BASIC and PRO subscriptions)."""
    try:
        # Check if recruiter
        if current_user.role.value != UserRole.RECRUITER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can view candidate profiles"
            )
        
        from uuid import UUID
        service = RecruiterService(db)
        # Convert string ID to UUID
        candidate_id_uuid = UUID(candidate_id)
        logger.info(f"Getting profile for candidate {candidate_id_uuid}")
        profile = await service.get_candidate_profile(current_user.id, candidate_id_uuid)
        logger.info(f"Profile retrieved successfully")
        
        return profile
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid UUID: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid candidate ID: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_candidate_profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/candidate/{candidate_id}/resume/{resume_id}")
async def view_candidate_resume(
    candidate_id: str,
    resume_id: str,
    token: str = Query(None),
    current_user = Depends(get_current_user_with_query_token),
    db: Session = Depends(get_db)
):
    """View candidate's resume file (for recruiters - displays inline in browser)."""
    # Check if recruiter
    if current_user.role.value != UserRole.RECRUITER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can view candidate resumes"
        )
    
    try:
        # Verify candidate exists
        service = RecruiterService(db)
        candidate = await service.get_candidate_profile(current_user.id, candidate_id)
        if not candidate:
            raise NotFoundException("Candidate", candidate_id)
        
        # Verify resume belongs to candidate
        resume = None
        for r in candidate.resumes:
            if str(r.id) == resume_id:
                resume = r
                break
        
        if not resume:
            raise NotFoundException("Resume", resume_id)
        
        # Get resume file path
        file_path = resume.file_path  # This is the S3 key or local file path
        
        logger.info(f"Recruiter {current_user.id} viewing resume {resume_id} for candidate {candidate_id}")
        
        # Determine media type based on file extension
        if resume.file_type.lower() == "pdf":
            media_type = "application/pdf"
        elif resume.file_type.lower() == "docx":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            media_type = "application/octet-stream"
        
        # Read file
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Return with inline disposition for browser display
            return StreamingResponse(
                iter([file_content]),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"inline; filename=\"{resume.file_name}\"",
                    "Content-Type": media_type,
                    "Content-Length": str(len(file_content)),
                    "Cache-Control": "no-cache"
                }
            )
        except FileNotFoundError:
            logger.error(f"Resume file not found at path: {file_path}")
            raise NotFoundException("Resume file", file_path)
            
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error viewing resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to view resume"
        )


@router.post("/send-email")
async def send_email(
    request: SendEmailRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send email to candidate (PRO subscription)."""
    # Check if recruiter
    if current_user.role.value != UserRole.RECRUITER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can send emails"
        )
    
    service = RecruiterService(db)
    result = await service.send_email_to_candidate(
        current_user.id,
        current_user.subscription_type,
        request
    )
    
    return result


@router.get("/email-templates")
async def get_email_templates(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available email templates for recruiters (PRO only)."""
    # Check if recruiter
    if current_user.role.value != UserRole.RECRUITER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can access templates"
        )
    
    # All recruiters can view templates (UI decision before sending)
    result = await db.execute(
        select(EmailTemplate).filter(EmailTemplate.is_active == True)
    )
    templates = result.scalars().all()
    
    return {
        "templates": [
            {
                "id": str(t.id),
                "name": t.name,
                "subject": t.subject,
                "body": t.body,
                "description": t.description,
                "placeholders": t.placeholders
            }
            for t in templates
        ]
    }


@router.post("/send-email-with-template")
async def send_email_with_template(
    request: SendEmailWithTemplateRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send email to candidate using template (PRO subscription)."""
    # Check if recruiter
    if current_user.role.value != UserRole.RECRUITER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can send emails"
        )
    
    service = EmailTemplateService(db)
    result = await service.send_email_with_template(
        current_user.id,
        current_user.subscription_type,
        request.template_id,
        request.candidate_id,
        request.candidate_email,
        request.dynamic_data
    )
    
    return result



