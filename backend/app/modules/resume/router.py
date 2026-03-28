from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.auth_utils import get_current_user
from app.modules.resume.schemas import ResumeUploadResponse
from app.modules.resume.service import ResumeService
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.audit import log_audit
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload resume file."""
    service = ResumeService(db)
    
    try:
        resume = await service.upload_resume(current_user.id, file)
        return ResumeUploadResponse(
            id=str(resume.id),
            file_name=resume.file_name,
            file_type=resume.file_type,
            status=resume.status,
            message="Resume uploaded successfully. Processing started.",
            s3_key=resume.s3_key
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume upload failed"
        )


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resume details by ID."""
    service = ResumeService(db)
    resume = await service.get_resume(resume_id, current_user.id)
    
    response_data = {
        "id": str(resume.id),
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "status": resume.status,
        "created_at": resume.created_at
    }
    
    # Include parsed data if resume has been parsed
    if resume.status == "PARSED" and resume.parsed_data:
        response_data["parsed_data"] = resume.parsed_data
        response_data["parsed_data_count"] = {
            "skills": len(resume.parsed_data.get("skills", [])),
            "experiences": len(resume.parsed_data.get("experiences", [])),
            "educations": len(resume.parsed_data.get("educations", []))
        }
    
    return response_data


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete resume and all derived data.
    
    Performs atomic cascade delete:
    - All derived skills, experiences, educations
    - S3 file
    - Resume record
    
    If any operation fails, entire transaction rolls back.
    """
    from uuid import UUID
    from app.core.exceptions import NotFoundException
    
    service = ResumeService(db)
    
    # Validate UUID format
    try:
        resume_uuid = UUID(resume_id)
        logger.info(f"[DELETE /resumes/{resume_id}] user_id={current_user.id}, UUID validation passed")
    except ValueError:
        logger.error(f"[DELETE /resumes/{resume_id}] Invalid UUID format: {resume_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resume ID format. Expected UUID, got: {resume_id}"
        )
    
    try:
        logger.info(f"[DELETE /resumes/{resume_id}] Starting delete operation for user_id={current_user.id}")
        
        # Call service to delete - this handles all cascade logic
        await service.delete_resume(resume_uuid, current_user.id)
        
        logger.info(f"[DELETE /resumes/{resume_id}] Successfully completed for user_id={current_user.id}")
        return {
            "message": "Resume deleted successfully with all derived data",
            "resume_id": resume_id,
            "status": "SUCCESS"
        }
    
    except NotFoundException as e:
        # Resume not found or user doesn't own it
        logger.warning(f"[DELETE /resumes/{resume_id}] Not found or unauthorized: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        # Detailed error logging for debugging
        error_msg = str(e)
        logger.error(
            f"[DELETE /resumes/{resume_id}] Deletion failed for user_id={current_user.id}: {error_msg}",
            exc_info=True
        )
        
        # Provide helpful error message based on error type
        if "S3" in error_msg or "delete_file" in error_msg.lower():
            detail = "Failed to delete file from storage. Please try again or contact support."
        elif "skill" in error_msg.lower():
            detail = "Failed to delete associated skills. Please try again."
        elif "experience" in error_msg.lower():
            detail = "Failed to delete associated experiences. Please try again."
        elif "education" in error_msg.lower():
            detail = "Failed to delete associated education. Please try again."
        else:
            detail = f"Failed to delete resume: {error_msg}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download resume file."""
    service = ResumeService(db)
    resume = await service.get_resume(resume_id, current_user.id)
    
    # Get the file from S3 (or local storage)
    file_path = await service.get_resume_file(resume_id, current_user.id)
    
    return FileResponse(
        path=file_path,
        filename=resume.file_name,
        media_type="application/octet-stream"
    )


@router.get("/{resume_id}/view")
async def view_resume(
    resume_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View resume in browser - returns file for inline display in new tab."""
    from uuid import UUID
    from app.core.exceptions import NotFoundException
    
    try:
        # Validate UUID format
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            logger.error(f"Invalid resume ID format: {resume_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid resume ID format"
            )
        
        logger.info(f"[GET /resumes/{resume_id}/view] user_id={current_user.id}, opening for view")
        
        service = ResumeService(db)
        resume = await service.get_resume(resume_uuid, current_user.id)
        
        # Get the file from S3
        file_path = await service.get_resume_file(resume_uuid, current_user.id)
        
        if not file_path:
            logger.error(f"Resume file not found: {resume_id}")
            raise NotFoundException("Resume file", str(resume_id))
        
        # Determine media type based on file extension
        media_type = "application/pdf" if resume.file_type.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        # Audit log: resume viewed
        await log_audit(
            db,
            current_user.id,
            "RESUME_VIEWED",
            "Resume",
            str(resume.id),
            {"file_name": resume.file_name, "file_type": resume.file_type}
        )
        
        logger.info(f"Resume {resume_id} viewed by user {current_user.id}")
        
        # Return file with inline disposition (opens in browser)
        return FileResponse(
            path=file_path,
            filename=resume.file_name,
            media_type=media_type,
            headers={"Content-Disposition": f"inline; filename=\"{resume.file_name}\""}
        )
    except NotFoundException as e:
        logger.warning(f"[GET /resumes/{resume_id}/view] Not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /resumes/{resume_id}/view] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to view resume"
        )


@router.get("/{resume_id}/status")
async def get_resume_status(
    resume_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resume processing status - used for frontend polling."""
    try:
        service = ResumeService(db)
        resume = await service.get_resume(resume_id, current_user.id)
        
        return {
            "id": str(resume.id),
            "file_name": resume.file_name,
            "status": resume.status,  # UPLOADED, PARSING, PARSED, FAILED
            "created_at": resume.created_at,
            "parsed_data": resume.parsed_data if resume.status == "PARSED" else None,
            "processing_message": f"Status: {resume.status}"
        }
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting resume status {resume_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get resume status"
        )
