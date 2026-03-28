from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.utils.auth_utils import get_current_user, require_role
from app.core.models import UserRole, User, Resume, CandidateSkill, Experience, Education
from app.modules.candidate.schemas import (
    CandidateProfileResponse,
    SkillResponse,
    ExperienceResponse,
    EducationResponse
)
from app.modules.candidate.service import CandidateService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/me", response_model=CandidateProfileResponse)
async def get_profile(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    response: Response = None
):
    """
    Get current candidate profile with LATEST parsed resume data.
    
    Strategy:
    1. Get candidate with all relationships (selectinload for efficiency)
    2. Get resumes ordered by creation date (latest first)
    3. Return current synced data + latest resume info
    4. Aggregate from the most recent PARSED resume with data
    
    Important: The response will show:
    - Latest resume file info (for status/upload date)
    - But aggregated skills/experiences/educations from all PARSED resumes
    - This ensures users see the most complete profile from all their resumes
    
    CACHE CONTROL: No-cache to ensure always fresh data from server
    """
    logger.info(f"[GET /candidates/me] user_id={current_user.id}, role={current_user.role}")
    
    # 1. Validate user is a candidate
    if current_user.role.value != "CANDIDATE":
        logger.warning(f"[GET /candidates/me] Access denied - user is {current_user.role}, not CANDIDATE")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only candidates can access this endpoint")
    
    try:
        # 2. Fetch candidate with all relationships efficiently
        result = await db.execute(
            select(User)
            .filter(User.id == current_user.id)
            .options(
                selectinload(User.resumes),
                selectinload(User.skills),
                selectinload(User.experiences),
                selectinload(User.educations)
            )
        )
        candidate = result.scalars().first()
        
        if not candidate:
            logger.error(f"[GET /candidates/me] User not found: {current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
        
        logger.info(f"[GET /candidates/me] Loaded candidate: id={candidate.id}")
        
        # 3. Get the ACTIVE resume (only ONE resume should be is_active=TRUE)
        try:
            active_resume_result = await db.execute(
                select(Resume)
                .filter(Resume.user_id == current_user.id)
                .filter(Resume.is_active == True)
                .filter(Resume.status == "PARSED")
                .order_by(desc(Resume.created_at))
                .limit(1)
            )
            active_resume = active_resume_result.scalars().first()
        except Exception as e:
            logger.warning(f"[GET /candidates/me] Error querying active resume (is_active column may not exist): {str(e)}")
            # Fallback: get latest PARSED resume
            active_resume_result = await db.execute(
                select(Resume)
                .filter(Resume.user_id == current_user.id)
                .filter(Resume.status == "PARSED")
                .order_by(desc(Resume.created_at))
                .limit(1)
            )
            active_resume = active_resume_result.scalars().first()
        
        if active_resume:
            logger.info(f"[GET /candidates/me] Active PARSED resume: {active_resume.file_name} (ID: {active_resume.id})")
        else:
            logger.warning(f"[GET /candidates/me] No active PARSED resume for user_id: {current_user.id}")
        
        # 4. Get all resumes (for the UI list)
        all_resumes_result = await db.execute(
            select(Resume)
            .filter(Resume.user_id == current_user.id)
            .order_by(desc(Resume.created_at))
        )
        all_resumes = all_resumes_result.scalars().all()
        
        # 5. Build resume list for UI
        resumes_with_flag = []
        for resume in all_resumes:
            resume_dict = {
                "id": str(resume.id),
                "file_name": resume.file_name,
                "file_type": resume.file_type,
                "status": resume.status,
                "created_at": resume.created_at,
                "is_latest": resume == all_resumes[0] if all_resumes else False
            }
            resumes_with_flag.append(resume_dict)
        
        # 6. Initialize data lists (important for new candidates with no resume)
        skills_list = []
        experiences_list = []
        educations_list = []
        skill_count = 0
        exp_count = 0
        edu_count = 0
        
        if active_resume:
            # Count ONLY data from ACTIVE resume
            skills_result = await db.execute(
                select(func.count(CandidateSkill.id))
                .filter(CandidateSkill.candidate_id == current_user.id)
                .filter(CandidateSkill.resume_id == active_resume.id)
            )
            skill_count = skills_result.scalar() or 0
            
            experiences_result = await db.execute(
                select(func.count(Experience.id))
                .filter(Experience.user_id == current_user.id)
                .filter(Experience.resume_id == active_resume.id)
            )
            exp_count = experiences_result.scalar() or 0
            
            educations_result = await db.execute(
                select(func.count(Education.id))
                .filter(Education.user_id == current_user.id)
                .filter(Education.resume_id == active_resume.id)
            )
            edu_count = educations_result.scalar() or 0
            
            # Fetch skill IDs from active resume
            skills_result = await db.execute(
                select(CandidateSkill.skill_id)
                .filter(CandidateSkill.candidate_id == current_user.id)
                .filter(CandidateSkill.resume_id == active_resume.id)
            )
            skill_ids = [row[0] for row in skills_result.all()]
            
            # Fetch actual skill objects
            if skill_ids:
                from app.core.models import Skill
                skills_query = await db.execute(
                    select(Skill).where(Skill.id.in_(skill_ids))
                )
                skills_list = [SkillResponse.from_orm(s) for s in skills_query.scalars().all()]
            
            # Fetch actual experience objects from active resume
            experiences_result = await db.execute(
                select(Experience)
                .filter(Experience.user_id == current_user.id)
                .filter(Experience.resume_id == active_resume.id)
            )
            experiences_list = [ExperienceResponse.from_orm(exp) for exp in experiences_result.scalars().all()]
            
            # Fetch actual education objects from active resume
            educations_result = await db.execute(
                select(Education)
                .filter(Education.user_id == current_user.id)
                .filter(Education.resume_id == active_resume.id)
            )
            educations_list = [EducationResponse.from_orm(edu) for edu in educations_result.scalars().all()]
            
            logger.info(f"[GET /candidates/me] Loaded {len(skills_list)} skills, {len(experiences_list)} experiences, {len(educations_list)} educations from active resume")
        else:
            logger.info(f"[GET /candidates/me] No active resume found - returning empty profile")
        
        logger.info(f"[GET /candidates/me] Profile data: resumes={len(all_resumes)}, skills={len(skills_list)}, experiences={len(experiences_list)}, educations={len(educations_list)}")
        
        # 7. Build response
        response_data = {
            "id": candidate.id,
            "email": candidate.email,
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "role": candidate.role,
            "created_at": candidate.created_at,
            "resumes": resumes_with_flag,  # Use resumes with is_latest flag
            "skills": skills_list,
            "experiences": experiences_list,
            "educations": educations_list
        }
        
        logger.info(f"[GET /candidates/me] Response ready: {len(skills_list)} skills, {len(experiences_list)} experiences, {len(educations_list)} educations from active PARSED resume")
        
        # 8. Add cache control headers to ensure fresh data
        if response:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return CandidateProfileResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /candidates/me] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load profile")






