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


# ============ SKILL CATEGORIZATION ============
SKILL_CATEGORIES = {
    "backend": {
        "Python", "Django", "FastAPI", "Node.js", "Java", "C#", "Ruby", "PHP", "Go", "Rust",
        "PostgreSQL", "MongoDB", "MySQL", "Redis", "Elasticsearch", "Express", "Spring Boot",
        "Flask", "SQLAlchemy", "Sequelize", "Hibernate", "C++", "Kotlin", "Scala", "Groovy"
    },
    "cloud_devops": {
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "K8s", "CI/CD", "Jenkins",
        "GitLab CI", "GitHub Actions", "Terraform", "CloudFormation", "S3", "SNS", "SQS", "SES",
        "Lambda", "ECS", "EC2", "RDS", "DynamoDB", "CloudWatch", "IAM", "VPC", "Ansible",
        "Chef", "Puppet", "Helm", "GCP", "DevOps", "Infrastructure", "Helm Charts"
    },
    "frontend": {
        "React", "Vue.js", "Angular", "JavaScript", "TypeScript", "HTML", "CSS", "Tailwind",
        "Bootstrap", "Next.js", "Svelte", "jQuery", "D3.js", "Redux", "Vuex", "RxJS",
        "Webpack", "Vite", "Babel", "SASS", "SCSS", "GraphQL", "REST", "Axios", "Fetch"
    },
    "architecture": {
        "System Design", "Microservices", "Event-driven Architecture", "Async Processing",
        "REST APIs", "GraphQL", "Message Queues", "Design Patterns", "SOLID Principles",
        "OAuth", "JWT", "OWASP", "TDD", "BDD", "Clean Architecture", "Serverless"
    },
    "soft_skills": {
        "Problem-solving", "Communication", "Teamwork", "Leadership", "Ownership mindset",
        "Adaptability", "Quick learner", "Attention to detail", "Time management",
        "Collaboration", "Critical thinking", "Analytical ability", "Decision making"
    }
}


def categorize_skills(skills_list):
    """Categorize skills into backend, cloud_devops, frontend, architecture, soft_skills, other."""
    categorized = {
        "backend": [],
        "cloud_devops": [],
        "frontend": [],
        "architecture": [],
        "soft_skills": [],
        "other": []
    }
    
    # Track which skills have been categorized
    categorized_skill_ids = set()
    
    # Go through each category and match skills
    for category, category_skills in SKILL_CATEGORIES.items():
        for skill_name_pattern in category_skills:
            # Check if any skill matches this pattern (case-insensitive)
            for skill_obj in skills_list:
                if skill_obj.id not in categorized_skill_ids and skill_obj.name.lower() == skill_name_pattern.lower():
                    categorized[category].append(skill_obj)
                    categorized_skill_ids.add(skill_obj.id)
                    break  # Move to next pattern
    
    # Remaining skills (not categorized) go to "other"
    categorized["other"] = [s for s in skills_list if s.id not in categorized_skill_ids]
    
    return categorized


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
        skills_list = {}  # Now a dict for categorized skills
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
            
            # Fetch skill IDs from active resume (with fallback for backwards compatibility)
            # STRATEGY: Try to fetch skills with resume_id first (new data)
            # If none found, fallback to ALL skills (for old data without resume_id)
            skills_result = await db.execute(
                select(CandidateSkill.skill_id)
                .filter(CandidateSkill.candidate_id == current_user.id)
                .filter(CandidateSkill.resume_id == active_resume.id)
            )
            skill_ids = [row[0] for row in skills_result.all()]
            
            # FALLBACK: If no skills found with resume_id, fetch all candidate skills (for backwards compatibility)
            if not skill_ids:
                logger.info(f"[GET /candidates/me] No skills with resume_id found, falling back to ALL candidate skills (legacy data support)")
                skills_result = await db.execute(
                    select(CandidateSkill.skill_id)
                    .filter(CandidateSkill.candidate_id == current_user.id)
                )
                skill_ids = [row[0] for row in skills_result.all()]
                logger.info(f"[GET /candidates/me] Fallback query returned {len(skill_ids)} skills with resume_id=NULL")
            
            # Fetch actual skill objects
            if skill_ids:
                from app.core.models import Skill
                skills_query = await db.execute(
                    select(Skill).where(Skill.id.in_(skill_ids))
                )
                skills_objs = skills_query.scalars().all()
                
                logger.info(f"[GET /candidates/me] Fetched {len(skills_objs)} skill objects")
                
                # Categorize skills
                categorized_skills = categorize_skills(skills_objs)
                
                # Convert to SkillResponse objects per category
                skills_list = {
                    category: [SkillResponse.from_orm(s) for s in skills]
                    for category, skills in categorized_skills.items()
                    if skills  # Only include non-empty categories
                }
                logger.info(f"[GET /candidates/me] Categorized into {len(skills_list)} categories with {sum(len(v) for v in skills_list.values())} total skills")
            
            # Fetch actual experience objects from active resume (with fallback)
            experiences_result = await db.execute(
                select(Experience)
                .filter(Experience.user_id == current_user.id)
                .filter(Experience.resume_id == active_resume.id)
            )
            experiences_list = [ExperienceResponse.from_orm(exp) for exp in experiences_result.scalars().all()]
            
            # FALLBACK: If no experiences found with resume_id, fetch all candidate experiences
            if not experiences_list:
                logger.info(f"[GET /candidates/me] No experiences with resume_id found, falling back to ALL candidate experiences (legacy data support)")
                experiences_result = await db.execute(
                    select(Experience)
                    .filter(Experience.user_id == current_user.id)
                )
                experiences_list = [ExperienceResponse.from_orm(exp) for exp in experiences_result.scalars().all()]
            
            # Fetch actual education objects from active resume (with fallback)
            educations_result = await db.execute(
                select(Education)
                .filter(Education.user_id == current_user.id)
                .filter(Education.resume_id == active_resume.id)
            )
            educations_list = [EducationResponse.from_orm(edu) for edu in educations_result.scalars().all()]
            
            # FALLBACK: If no educations found with resume_id, fetch all candidate educations
            if not educations_list:
                logger.info(f"[GET /candidates/me] No educations with resume_id found, falling back to ALL candidate educations (legacy data support)")
                educations_result = await db.execute(
                    select(Education)
                    .filter(Education.user_id == current_user.id)
                )
                educations_list = [EducationResponse.from_orm(edu) for edu in educations_result.scalars().all()]
            
            logger.info(f"[GET /candidates/me] Loaded {sum(len(v) for v in skills_list.values())} skills, {len(experiences_list)} experiences, {len(educations_list)} educations from active resume")
        else:
            logger.info(f"[GET /candidates/me] No active resume found - returning empty profile")
        
        logger.info(f"[GET /candidates/me] Profile data: resumes={len(all_resumes)}, skills={sum(len(v) for v in skills_list.values()) if isinstance(skills_list, dict) else len(skills_list)}, experiences={len(experiences_list)}, educations={len(educations_list)}")
        
        # Extract data from resume (prioritize resume data over login credentials)
        email_from_resume = None
        first_name_from_resume = None
        last_name_from_resume = None
        
        if active_resume and active_resume.parsed_data:
            parsed = active_resume.parsed_data
            email_from_resume = parsed.get('email')
            
            # Extract name from resume - try 'name' field first
            resume_name = parsed.get('name')
            if resume_name:
                # Parse full name into first and last
                name_parts = resume_name.strip().split()
                if len(name_parts) >= 2:
                    first_name_from_resume = name_parts[0]
                    last_name_from_resume = ' '.join(name_parts[1:])
                elif len(name_parts) == 1:
                    first_name_from_resume = name_parts[0]
                    last_name_from_resume = ""
        
        # 7. Build response - PRIORITIZE RESUME DATA
        response_data = {
            "id": candidate.id,
            # PRIORITIZE: Use email from resume, fallback to user email
            "email": (email_from_resume or candidate.email),
            # PRIORITIZE: Use name from resume, fallback to user name
            "first_name": (first_name_from_resume or candidate.first_name),
            "last_name": (last_name_from_resume or candidate.last_name),
            "role": candidate.role,
            "created_at": candidate.created_at,
            "resumes": resumes_with_flag,  # Use resumes with is_latest flag
            "skills": skills_list if isinstance(skills_list, dict) else {},  # Return categorized skills or empty dict
            "experiences": experiences_list,
            "educations": educations_list
        }
        
        logger.info(f"[GET /candidates/me] Response ready: {sum(len(v) for v in response_data['skills'].values())} skills from {len(response_data['skills'])} categories, {len(experiences_list)} experiences, {len(educations_list)} educations from active PARSED resume")
        
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






