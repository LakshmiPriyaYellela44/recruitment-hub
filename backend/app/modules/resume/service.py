from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import Resume, User
from app.core.exceptions import NotFoundException, ValidationException
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.parser import ResumeParser
from app.modules.resume.validator import ResumeValidator
from app.modules.candidate.service import CandidateService
from app.aws_services.s3_client import S3Client
from app.events.config import EventConfig
from app.utils.audit import log_audit
from app.core.config import settings
from fastapi import UploadFile
from uuid import UUID, uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for resume operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ResumeRepository(db)
        self.s3_client = S3Client()  # Real AWS S3
        # Use SNS client from event configuration
        self.sns_client = EventConfig.get_sns_client()
    
    async def upload_resume(self, user_id: UUID, file: UploadFile) -> Resume:
        """Upload and process resume."""
        logger.info(f"[upload_resume] user_id: {user_id}, filename: {file.filename}")
        
        try:
            # Validate file type
            file_ext = file.filename.split(".")[-1].lower()
            logger.info(f"[upload_resume] File extension: {file_ext}")
            if file_ext not in ["pdf", "docx"]:
                logger.error(f"[upload_resume] Invalid file type: {file_ext}")
                raise ValidationException("Only PDF and DOCX files are supported")
            
            # Check file size (max 10MB)
            content = await file.read()
            file_size = len(content)
            logger.info(f"[upload_resume] File size: {file_size} bytes")
            if file_size > 10 * 1024 * 1024:
                logger.error(f"[upload_resume] File too large: {file_size} bytes")
                raise ValidationException("File size must be less than 10MB")
            
            # Validate file is not empty
            if file_size == 0:
                logger.error(f"[upload_resume] File is empty")
                raise ValidationException("Resume file cannot be empty")
            
            # ✅ VALIDATE FILE INTEGRITY (check if it's a real PDF/DOCX, not corrupted)
            logger.info(f"[upload_resume] Validating file integrity for file_ext={file_ext}...")
            is_valid, integrity_error = ResumeValidator.validate_file_integrity(content, file_ext)
            if not is_valid:
                logger.error(f"[upload_resume] File integrity validation failed: {integrity_error}")
                raise ValidationException(integrity_error)
            logger.info(f"[upload_resume]  File integrity validation passed for {file_ext}")
            
            # ✅ STRONG VALIDATION: Check for actual resume structure (Experience, Skills, Education, Contact)
            logger.info(f"[upload_resume] Validating resume structure and content...")
            is_valid_resume, resume_error = ResumeValidator.validate_resume_structure(content, file_ext)
            if not is_valid_resume:
                logger.error(f"[upload_resume]  Resume structure validation failed: {resume_error}")
                raise ValidationException(resume_error)
            logger.info(f"[upload_resume]  Resume structure validation passed")
            
            # Generate unique file name
            unique_filename = f"{user_id}_{uuid4().hex}_{file.filename}"
            logger.info(f"[upload_resume] Generated unique filename: {unique_filename}, file_ext: {file_ext}")
            
            # Upload to S3 (mock)
            logger.info(f"[upload_resume] Uploading to S3...")
            s3_key = await self.s3_client.upload_file(unique_filename, content)
            logger.info(f"[upload_resume] ✅ File uploaded to S3 with key: {s3_key}")
            
            # Verify file was actually uploaded successfully
            logger.info(f"[upload_resume] Verifying S3 upload...")
            verify_content = await self.s3_client.download_file(s3_key)
            if verify_content is None:
                logger.error(f"[upload_resume]  S3 verification failed - file exists but could not be retrieved")
                raise ValidationException("Resume upload verification failed - file could not be retrieved from S3")
            if len(verify_content) != file_size:
                logger.error(f"[upload_resume]  S3 verification failed - size mismatch. Expected {file_size}, got {len(verify_content)}")
                raise ValidationException("Resume upload verification failed - file size mismatch")
            logger.info(f"[upload_resume]  S3 upload verified successfully")
            
            # Create resume record
            logger.info(f"[upload_resume] Creating resume record in database with file_type={file_ext}...")
            resume = Resume(
                user_id=user_id,
                file_name=file.filename,
                file_path=s3_key,
                file_type=file_ext,
                s3_key=s3_key,
                status="UPLOADED"
            )
            
            logger.info(f"[upload_resume] Resume object created: id={resume.id if hasattr(resume, 'id') else 'not-yet-assigned'}")
            created_resume = await self.repository.create_resume(resume)
            logger.info(f"[upload_resume]  Resume record SAVED to database: id={created_resume.id}")
            
            # If sync parsing is enabled, parse immediately (development mode)
            if settings.RESUME_SYNC_PARSING:
                logger.info(f"[upload_resume] SYNC_PARSING_ENABLED - parsing immediately")
                try:
                    await self.process_resume(created_resume.id)
                    logger.info(f"[upload_resume]  Resume parsed successfully")
                    
                    # Refresh resume to get updated status and parsed_data
                    updated_resume = await self.repository.get_resume_by_id(created_resume.id)
                    logger.info(f"[upload_resume] Refreshed resume status: {updated_resume.status}")
                    created_resume = updated_resume
                except Exception as e:
                    logger.error(f"[upload_resume]  Error parsing resume: {str(e)}", exc_info=True)
                    # Don't fail the upload if parsing fails, parsing can be retried
                    # Return resume with FAILED status if parsing failed
                    updated_resume = await self.repository.get_resume_by_id(created_resume.id)
                    created_resume = updated_resume
            else:
                logger.info(f"[upload_resume] SYNC_PARSING_DISABLED - publishing to SNS for async processing")
                # Publish event to SNS for asynchronous processing (production mode)
                await self.sns_client.publish(
                    topic="recruitment-resume-uploads",
                    message={
                        "resume_id": str(created_resume.id),
                        "candidate_id": str(user_id),
                        "action": "upload",
                        "s3_key": s3_key,
                        "file_type": file_ext
                    }
                )
                logger.info(f"[upload_resume]  Resume upload event published to SNS")
            
            # Log audit
            await log_audit(
                self.db,
                user_id,
                "RESUME_UPLOADED",
                "Resume",
                str(created_resume.id),
                {"file_name": file.filename}
            )
            
            
            return created_resume
            
        except ValidationException as e:
            logger.error(f"[upload_resume] ValidationException: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[upload_resume]  Exception: {str(e)}", exc_info=True)
            raise ValidationException(f"Resume upload failed: {str(e)}")
    
    async def process_resume(self, resume_id: UUID) -> Resume:
        """Process uploaded resume: parse, extract data, persist to DB, update email."""
        logger.info(f"[process_resume] Starting processing for resume_id: {resume_id}")
        
        resume = await self.repository.get_resume_by_id(resume_id)
        if not resume:
            raise NotFoundException("Resume", str(resume_id))
        
        try:
            # 1. Mark resume as PARSING
            resume.status = "PARSING"
            await self.repository.update_resume(resume, auto_commit=False)
            logger.info(f"[process_resume] ✓ Status: PARSING for resume_id={resume_id}")
            
            # 2. Parse resume PDF/DOCX
            if resume.file_type == "pdf":
                parsed_data = await ResumeParser.parse_pdf(resume.file_path)
            else:
                parsed_data = await ResumeParser.parse_docx(resume.file_path)
            
            # Check if parser returned an error
            if "error" in parsed_data:
                error_msg = parsed_data.get("error", "Unknown parsing error")
                logger.error(f"[process_resume] Parser failed for resume_id={resume_id}: {error_msg}")
                raise Exception(f"Resume parsing failed: {error_msg}")
            
            logger.info(f"[process_resume] ✓ Parsed resume, extracted: {len(parsed_data.get('skills', []))} skills, {len(parsed_data.get('experiences', []))} experiences, {len(parsed_data.get('educations', []))} educations")
            
            logger.info(f"[process_resume] Validation checks skipped for now")
            
            # 3. CRITICAL: Set all previous resumes to is_active=FALSE
            logger.info(f"[process_resume] Setting previous resumes to inactive for user_id={resume.user_id}")
            from sqlalchemy import update
            from app.core.models import Resume as ResumeModel
            await self.db.execute(
                update(ResumeModel)
                .where(ResumeModel.user_id == resume.user_id)
                .where(ResumeModel.is_active == True)
                .values(is_active=False)
            )
            await self.db.flush()
            logger.info(f"[process_resume] ✓ All previous resumes deactivated")
            
            # 4. Set current resume to is_active=TRUE
            resume.is_active = True
            await self.repository.update_resume(resume, auto_commit=False)
            logger.info(f"[process_resume] ✓ Current resume set to active")
            
            # 5. Persist extracted data using explicit methods (everything within this transaction)
            skills_count = 0
            experiences_count = 0
            educations_count = 0
            
            try:
                candidate_service = CandidateService(self.db)
                
                # Persist skills
                skills_list = parsed_data.get("skills", [])
                logger.info(f"[process_resume] Skills from parsed_data: type={type(skills_list)}, content={skills_list if isinstance(skills_list, list) else f'dict with {len(skills_list)} categories'}")
                
                if skills_list:
                    logger.info(f"[process_resume] Calling _persist_skills with {len(list(skills_list.keys()) if isinstance(skills_list, dict) else skills_list)} items")
                    skills_count = await candidate_service._persist_skills(
                        resume.user_id,
                        skills_list,
                        resume_id=resume_id,
                        auto_commit=False
                    )
                    logger.info(f"[process_resume] _persist_skills returned: {skills_count} skills persisted")
                else:
                    logger.warning(f"[process_resume] No skills found in parsed_data!")
                
                # Persist experiences
                experiences_list = parsed_data.get("experiences", [])
                if experiences_list:
                    experiences_count = await candidate_service._persist_experiences(
                        resume.user_id,
                        experiences_list,
                        resume_id=resume_id,
                        auto_commit=False
                    )
                
                # Persist educations
                educations_list = parsed_data.get("educations", [])
                if educations_list:
                    educations_count = await candidate_service._persist_educations(
                        resume.user_id,
                        educations_list,
                        resume_id=resume_id,
                        auto_commit=False
                    )
                
                logger.info(f"[process_resume] ✓ Persisted all data: {skills_count} skills, {experiences_count} experiences, {educations_count} educations")
            except Exception as e:
                logger.error(f"[process_resume] Failed to persist parsed data: {str(e)}", exc_info=True)
                raise
            
            # 6. Update candidate email and phone if extracted
            from sqlalchemy import select
            user_result = await self.db.execute(select(User).filter(User.id == resume.user_id))
            user = user_result.scalars().first()
            
            if user:
                # Update email if extracted (only if email doesn't belong to another user)
                email = parsed_data.get("email")
                if email:
                    old_email = user.email
                    # Only update email if it's different and doesn't belong to another user
                    if email != old_email:
                        # Check if email already exists for another user
                        existing_user = await self.db.execute(
                            select(User).filter(User.email == email, User.id != resume.user_id)
                        )
                        if not existing_user.scalars().first():
                            user.email = email
                            await self.db.flush()
                            logger.info(f"[process_resume] ✓ Updated email for user_id={resume.user_id}: {old_email} → {email}")
                        else:
                            logger.warning(f"[process_resume]  Email {email} already in use, skipping email update")
                
                # Update phone if extracted
                phone = parsed_data.get("phone")
                if phone:
                    old_phone = user.phone_number
                    # Only update phone if it's different and not empty
                    if phone != old_phone and phone.strip():
                        user.phone_number = phone
                        await self.db.flush()
                        logger.info(f"[process_resume] ✓ Updated phone for user_id={resume.user_id}: {old_phone} → {phone}")
                    elif not phone.strip():
                        logger.warning(f"[process_resume]  Phone number is empty string, skipping phone update")
            
            # 7. Mark as PARSED
            resume.parsed_data = parsed_data
            resume.status = "PARSED"
            await self.repository.update_resume(resume, auto_commit=False)
            logger.info(f"[process_resume] ✓ Status: PARSED")
            
            # 8. ATOMIC COMMIT - All changes at once
            await self.db.commit()
            logger.info(f"[process_resume]  ATOMIC COMMIT complete for resume_id={resume_id}")
            
            # 9. VERIFICATION: Query to confirm all data persisted
            from sqlalchemy import select, func
            from app.core.models import CandidateSkill, Experience, Education
            
            skill_check = await self.db.execute(
                select(func.count(CandidateSkill.id))
                .filter(CandidateSkill.candidate_id == resume.user_id)
                .filter(CandidateSkill.resume_id == resume_id)
            )
            exp_check = await self.db.execute(
                select(func.count(Experience.id))
                .filter(Experience.user_id == resume.user_id)
                .filter(Experience.resume_id == resume_id)
            )
            edu_check = await self.db.execute(
                select(func.count(Education.id))
                .filter(Education.user_id == resume.user_id)
                .filter(Education.resume_id == resume_id)
            )
            
            verified_skills = skill_check.scalar() or 0
            verified_experiences = exp_check.scalar() or 0
            verified_educations = edu_check.scalar() or 0
            
            logger.info(f"[process_resume] VERIFICATION: {verified_skills} skills, {verified_experiences} experiences, {verified_educations} educations in database")
            
            # 10. Refresh resume from DB
            updated_resume = await self.repository.get_resume_by_id(resume_id)
            
            # 11. Log audit
            await log_audit(
                self.db,
                resume.user_id,
                "RESUME_PARSED",
                "Resume",
                str(resume_id),
                {
                    "skills": verified_skills,
                    "experiences": verified_experiences,
                    "educations": verified_educations,
                    "email": email,
                    "is_active": True
                }
            )
            
            return updated_resume
            
        except Exception as e:
            logger.error(f"[process_resume] ERROR: {str(e)}", exc_info=True)
            
            # Rollback on error
            try:
                await self.db.rollback()
                logger.info(f"[process_resume] ✓ Rolled back transaction")
            except Exception as rollback_err:
                logger.warning(f"[process_resume] Failed to rollback: {str(rollback_err)}")
            
            # Mark resume as FAILED
            resume.status = "FAILED"
            await self.repository.update_resume(resume, auto_commit=True)
            
            await log_audit(
                self.db,
                resume.user_id,
                "RESUME_PARSE_FAILED",
                "Resume",
                str(resume_id),
                {"error": str(e)}
            )
            
            raise
    
    async def get_resume(self, resume_id: UUID, user_id: UUID) -> Resume:
        """Get resume."""
        resume = await self.repository.get_resume_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundException("Resume", str(resume_id))
        return resume
    
    async def get_candidate_resumes(self, user_id: UUID):
        """Get all resumes for candidate."""
        return await self.repository.get_candidate_resumes(user_id)
    
    async def delete_resume(self, resume_id: UUID, user_id: UUID):
        """
        Delete resume and ALL derived data atomically.
        
        This method performs a complete cascade delete:
        1. Validates ownership (authorization check)
        2. Deletes derived skills, experiences, educations
        3. Deletes S3 file
        4. Deletes resume record
        
        All operations are atomic - if any fails, all rollback.
        """
        logger.info(f"[DELETE_RESUME_START] resume_id={resume_id}, user_id={user_id}")
        
        # Validate resume exists and belongs to user
        resume = await self.repository.get_resume_by_id(resume_id)
        if not resume:
            logger.warning(f"[DELETE_RESUME_NOT_FOUND] resume_id={resume_id} does not exist")
            raise NotFoundException("Resume", str(resume_id))
        
        if resume.user_id != user_id:
            logger.warning(f"[DELETE_RESUME_UNAUTHORIZED] user_id={user_id} does not own resume_id={resume_id}")
            raise NotFoundException("Resume", str(resume_id))
        
        s3_key = resume.s3_key
        logger.info(f"[DELETE_RESUME_VALIDATION] Ownership verified. S3 key: {s3_key}, File: {resume.file_name}")
        
        try:
            # IMPORTANT: Execute all deletes in atomic sequence
            # The SQLAlchemy session will handle transaction automatically
            logger.info(f"[DELETE_RESUME_TX_BEGIN] Starting cascade delete for resume_id={resume_id}")
            
            # 1. Delete candidate skills derived from this resume
            try:
                skills_deleted = await self.repository.delete_resume_skills(resume_id)
                logger.info(f"[DELETE_RESUME_SKILLS] Deleted {skills_deleted} skills derived from resume_id={resume_id}")
            except Exception as e:
                logger.error(f"[DELETE_RESUME_SKILLS_ERROR] Failed to delete skills: {str(e)}", exc_info=True)
                raise
            
            # 2. Delete experiences derived from this resume
            try:
                exp_deleted = await self.repository.delete_resume_experiences(resume_id)
                logger.info(f"[DELETE_RESUME_EXPERIENCES] Deleted {exp_deleted} experiences derived from resume_id={resume_id}")
            except Exception as e:
                logger.error(f"[DELETE_RESUME_EXPERIENCES_ERROR] Failed to delete experiences: {str(e)}", exc_info=True)
                raise
            
            # 3. Delete educations derived from this resume
            try:
                edu_deleted = await self.repository.delete_resume_educations(resume_id)
                logger.info(f"[DELETE_RESUME_EDUCATIONS] Deleted {edu_deleted} educations derived from resume_id={resume_id}")
            except Exception as e:
                logger.error(f"[DELETE_RESUME_EDUCATIONS_ERROR] Failed to delete educations: {str(e)}", exc_info=True)
                raise
            
            # 4. Delete file from S3 (CRITICAL: check result)
            try:
                s3_delete_success = await self.s3_client.delete_file(s3_key)
                if not s3_delete_success:
                    error_msg = f"S3 deletion failed for key: {s3_key}"
                    logger.error(f"[DELETE_RESUME_S3_ERROR] {error_msg}")
                    raise Exception(error_msg)
                logger.info(f"[DELETE_RESUME_S3] Successfully deleted S3 file: {s3_key}")
            except Exception as e:
                logger.error(f"[DELETE_RESUME_S3_CRITICAL] S3 deletion failed: {str(e)}", exc_info=True)
                raise
            
            # 5. Delete resume record from database
            try:
                await self.repository.delete_resume(resume_id)
                logger.info(f"[DELETE_RESUME_DB] Successfully deleted resume record: {resume_id}")
            except Exception as e:
                logger.error(f"[DELETE_RESUME_DB_ERROR] Failed to delete resume record: {str(e)}", exc_info=True)
                raise
            
            logger.info(f"[DELETE_RESUME_TX_COMPLETE] All operations completed for resume_id={resume_id}")
            
            # 6. Commit changes to database (flush transaction)
            try:
                await self.db.commit()
                logger.info(f"[DELETE_RESUME_COMMITTED] Changes committed for resume_id={resume_id}")
            except Exception as e:
                await self.db.rollback()
                logger.error(f"[DELETE_RESUME_COMMIT_ERROR] Failed to commit: {str(e)}", exc_info=True)
                raise
            
            # 7. Log audit (outside transaction)
            try:
                await log_audit(
                    self.db,
                    user_id,
                    "RESUME_DELETED_WITH_CASCADE",
                    "Resume",
                    str(resume_id),
                    {
                        "file_name": resume.file_name,
                        "s3_key": s3_key,
                        "skills_deleted": skills_deleted,
                        "experiences_deleted": exp_deleted,
                        "educations_deleted": edu_deleted,
                        "status": "SUCCESS"
                    }
                )
                logger.info(f"[DELETE_RESUME_AUDIT_LOGGED] Audit log created for resume_id={resume_id}")
            except Exception as e:
                logger.warning(f"[DELETE_RESUME_AUDIT_ERROR] Failed to log audit (non-critical): {str(e)}")
                # Don't raise - audit failure shouldn't fail the delete
            
            logger.info(f"[DELETE_RESUME_COMPLETE] Resume deletion completed successfully for resume_id={resume_id}")
            
        except NotFoundException:
            logger.error(f"[DELETE_RESUME_NOTFOUND] Resume not found: {resume_id}")
            raise
        except Exception as e:
            logger.error(f"[DELETE_RESUME_FAILED] Resume deletion failed for resume_id={resume_id}: {str(e)}", exc_info=True)
            # Ensure rollback on error
            try:
                await self.db.rollback()
                logger.info(f"[DELETE_RESUME_ROLLBACK] Transaction rolled back for resume_id={resume_id}")
            except Exception as rollback_err:
                logger.warning(f"[DELETE_RESUME_ROLLBACK_ERROR] Rollback failed: {str(rollback_err)}")
            raise
    
    async def get_resume_file(self, resume_id: UUID, user_id: UUID) -> str:
        """Get resume file path for download."""
        import tempfile
        
        resume = await self.repository.get_resume_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundException("Resume", str(resume_id))
        
        # Download from S3
        file_content = await self.s3_client.download_file(resume.s3_key)
        if not file_content:
            raise NotFoundException("Resume file", str(resume_id))
        
        # Write to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f".{resume.file_type}",
            delete=False
        )
        temp_file.write(file_content)
        temp_file.close()
        
        return temp_file.name
