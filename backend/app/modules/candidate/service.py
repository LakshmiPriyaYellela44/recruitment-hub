from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.models import Skill, UserRole, User
from app.core.exceptions import NotFoundException, ValidationException
from app.modules.candidate.repository import CandidateRepository
from app.modules.candidate.schemas import (
    ExperienceCreate,
    EducationCreate
)
from app.utils.audit import log_audit
from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CandidateService:
    """Service for candidate operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = CandidateRepository(db)
    
    async def get_or_create_candidate_profile(self, user_id: UUID):
        """Get candidate profile, or create if doesn't exist. ALWAYS returns a candidate."""
        logger.info(f"[get_or_create_candidate_profile] Attempting to fetch/create profile for user_id: {user_id}")
        
        try:
            # Try to fetch candidate with all relationships eagerly loaded
            result = await self.db.execute(
                select(User)
                .filter(User.id == user_id)
                .options(
                    selectinload(User.resumes),
                    selectinload(User.experiences),
                    selectinload(User.educations),
                    selectinload(User.skills)
                )
            )
            candidate = result.scalars().first()
            
            if candidate:
                logger.info(f"[get_or_create_candidate_profile] Profile found for user_id: {user_id}")
                return candidate
            
            # Profile doesn't exist, create a new one
            logger.warning(f"[get_or_create_candidate_profile] Profile NOT found for user_id: {user_id} - creating one")
            
            # Fetch the user
            user_result = await self.db.execute(select(User).filter(User.id == user_id))
            user = user_result.scalars().first()
            
            if not user:
                logger.error(f"[get_or_create_candidate_profile] User not found: {user_id}")
                raise NotFoundException("User", str(user_id))
            
            # User exists, just return it (it already has empty relationships initialized)
            # Initialize empty collections if they're None
            if not hasattr(user, 'resumes') or user.resumes is None:
                user.resumes = []
            if not hasattr(user, 'experiences') or user.experiences is None:
                user.experiences = []
            if not hasattr(user, 'educations') or user.educations is None:
                user.educations = []
            if not hasattr(user, 'candidate_skills') or user.candidate_skills is None:
                user.candidate_skills = []
            
            logger.info(f"[get_or_create_candidate_profile] Candidate profile auto-created for user_id: {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"[get_or_create_candidate_profile] Error for user_id {user_id}: {str(e)}", exc_info=True)
            raise
    
    async def get_candidate_profile(self, user_id: UUID):
        """Get candidate profile with all data."""
        logger.info(f"Fetching candidate profile for user_id: {user_id}")
        try:
            candidate = await self.repository.get_candidate_by_id(user_id)
            if not candidate:
                logger.warning(f"Candidate profile not found for user_id: {user_id}")
                raise NotFoundException("Candidate", str(user_id))
            logger.info(f"Successfully fetched candidate profile for user_id: {user_id}")
            return candidate
        except Exception as e:
            logger.error(f"Error fetching candidate profile: {str(e)}", exc_info=True)
            raise
    
    async def add_skill_to_candidate(self, user_id: UUID, skill_name: str, proficiency: Optional[str] = None, resume_id: Optional[UUID] = None, is_derived: bool = False, auto_commit: bool = True):
        """Add skill to candidate."""
        try:
            # Sanitize skill name - preserve original casing but remove whitespace
            skill_name_clean = skill_name.strip() if isinstance(skill_name, str) else str(skill_name)
            skill_name_lower = skill_name_clean.lower()
            
            logger.debug(f"[add_skill] Adding skill: original='{skill_name}', cleaned='{skill_name_clean}'")
            
            # Get or create skill using case-insensitive search
            result = await self.db.execute(select(Skill).filter(Skill.name.ilike(skill_name_lower)))
            skill = result.scalars().first()
            
            if not skill:
                logger.debug(f"[add_skill] Skill '{skill_name_lower}' not found, creating with name='{skill_name_clean}'")
                # Store with original casing for better display
                skill = Skill(name=skill_name_clean)
                self.db.add(skill)
                await self.db.flush()  # ALWAYS flush to get ID
                await self.db.refresh(skill)
                logger.debug(f"[add_skill] Created skill: id={skill.id}, name='{skill.name}'")
            else:
                logger.debug(f"[add_skill] Found existing skill: id={skill.id}, name='{skill.name}'")
            
            # Create candidate skill relationship
            from app.core.models import CandidateSkill
            candidate_skill = CandidateSkill(
                candidate_id=user_id,
                skill_id=skill.id,
                proficiency=proficiency,
                resume_id=resume_id,
                is_derived_from_resume=is_derived
            )
            self.db.add(candidate_skill)
            await self.db.flush()  # ALWAYS flush to register in session
            logger.debug(f"[add_skill] Created candidate_skill relationship")
            
            if auto_commit:
                await self.db.commit()
                await self.db.refresh(candidate_skill)
                logger.debug(f"[add_skill] Committed changes")
            
            logger.info(f"[add_skill] ✓ Added skill '{skill_name_clean}' to candidate {user_id}")
            return candidate_skill
        except Exception as e:
            logger.error(f"[add_skill] ❌ Error adding skill '{skill_name}' to candidate {user_id}: {str(e)}", exc_info=True)
            raise
    
    async def remove_skill_from_candidate(self, user_id: UUID, skill_id: UUID):
        """Remove skill from candidate."""
        result = await self.db.execute(select(Skill).filter(Skill.id == skill_id))
        skill = result.scalars().first()
        
        if not skill:
            raise NotFoundException("Skill", str(skill_id))
        
        await self.repository.remove_candidate_skill(user_id, skill_id)
        
        # Log audit
        await log_audit(
            self.db,
            user_id,
            "SKILL_REMOVED",
            "Skill",
            skill.name
        )
    
    async def add_experience(self, user_id: UUID, experience: ExperienceCreate, resume_id: Optional[UUID] = None, is_derived: bool = False, auto_commit: bool = True) -> dict:
        """Add experience to candidate."""
        experience_data = experience.dict()
        created = await self.repository.create_experience(user_id, experience_data, resume_id=resume_id, is_derived=is_derived, auto_commit=auto_commit)
        
        # Log audit (only if auto_commit, otherwise caller will handle)
        if auto_commit:
            await log_audit(
                self.db,
                user_id,
                "EXPERIENCE_ADDED",
                "Experience",
                str(created.id),
                {"company": experience.company_name}
            )
        
        return created
    

    
    async def add_education(self, user_id: UUID, education: EducationCreate, resume_id: Optional[UUID] = None, is_derived: bool = False, auto_commit: bool = True) -> dict:
        """Add education to candidate."""
        education_data = education.dict()
        created = await self.repository.create_education(user_id, education_data, resume_id=resume_id, is_derived=is_derived, auto_commit=auto_commit)
        
        # Log audit (only if auto_commit, otherwise caller will handle)
        if auto_commit:
            await log_audit(
                self.db,
                user_id,
                "EDUCATION_ADDED",
                "Education",
                str(created.id),
                {"institution": education.institution}
            )
        
        return created
    

    
    async def sync_parsed_resume_data(self, user_id: UUID, parsed_data: dict, resume_id: Optional[UUID] = None):
        """Sync extracted resume data (skills, experiences) to candidate profile with traceability."""
        logger.info(f"[sync_parsed_resume_data] Starting sync for user_id: {user_id}, resume_id: {resume_id}")
        logger.info(f"[sync_parsed_resume_data] Parsed data: skills={len(parsed_data.get('skills', []))}, experiences={len(parsed_data.get('experiences', []))}, educations={len(parsed_data.get('educations', []))}") 
        
        skills_added = 0
        experiences_added = 0
        educations_added = 0
        
        try:
            # Extract and add skills (handle both flat array and categorized object)
            skills_data = parsed_data.get("skills", [])
            skills_list = []
            
            if isinstance(skills_data, dict):
                # New format: categorized skills {backend: [...], cloud_devops: [...], etc}
                logger.info(f"[sync_parsed_resume_data] Processing categorized skills")
                for category, category_skills in skills_data.items():
                    if isinstance(category_skills, list) and category != "other":
                        skills_list.extend(category_skills)
                    elif category == "other" and isinstance(category_skills, list):
                        skills_list.extend(category_skills)
            elif isinstance(skills_data, list):
                # Old format: flat array of skills
                logger.info(f"[sync_parsed_resume_data] Processing flat skills array")
                skills_list = skills_data
            
            if skills_list:
                logger.info(f"[sync_parsed_resume_data] Adding {len(skills_list)} skills: {skills_list}")
                for skill_name in skills_list:
                    try:
                        await self.add_skill_to_candidate(
                            user_id, 
                            skill_name, 
                            proficiency="INTERMEDIATE",
                            resume_id=resume_id,
                            is_derived=True,
                            auto_commit=False
                        )
                        skills_added += 1
                        logger.info(f"[sync_parsed_resume_data] ✓ Added skill: {skill_name}")
                    except Exception as e:
                        logger.error(f"[sync_parsed_resume_data] Failed to add skill '{skill_name}': {str(e)}", exc_info=True)
            
            # Extract and add experiences
            experiences_list = parsed_data.get("experiences", [])
            if experiences_list:
                logger.info(f"[sync_parsed_resume_data] Adding {len(experiences_list)} experiences")
                for exp_data in experiences_list:
                    try:
                        exp = ExperienceCreate(
                            job_title=exp_data.get("title", "Unknown"),
                            company_name=exp_data.get("company", "Unknown"),
                            location=None,
                            description=None,
                            start_date=None,
                            end_date=None,
                            is_current=False
                        )
                        await self.add_experience(
                            user_id, 
                            exp,
                            resume_id=resume_id,
                            is_derived=True,
                            auto_commit=False
                        )
                        experiences_added += 1
                        logger.info(f"[sync_parsed_resume_data] ✓ Added experience: {exp.job_title} at {exp.company_name}")
                    except Exception as e:
                        logger.error(f"[sync_parsed_resume_data] Failed to add experience: {str(e)}", exc_info=True)
            
            # Extract and add educations
            educations_list = parsed_data.get("educations", [])
            if educations_list:
                logger.info(f"[sync_parsed_resume_data] Adding {len(educations_list)} educations")
                for edu_data in educations_list:
                    try:
                        edu = EducationCreate(
                            institution=edu_data.get("institution", "Unknown"),
                            degree=edu_data.get("degree", "Unknown"),
                            field_of_study=edu_data.get("field", None),
                            start_date=None,
                            end_date=None,
                            description=None
                        )
                        await self.add_education(
                            user_id, 
                            edu,
                            resume_id=resume_id,
                            is_derived=True,
                            auto_commit=False
                        )
                        educations_added += 1
                        logger.info(f"[sync_parsed_resume_data] ✓ Added education: {edu.degree} in {edu.field_of_study}")
                    except Exception as e:
                        logger.error(f"[sync_parsed_resume_data] Failed to add education: {str(e)}", exc_info=True)
            
            # Flush all changes (do NOT commit - let calling transaction handle it)
            logger.info(f"[sync_parsed_resume_data] Flushing {skills_added} skills, {experiences_added} experiences, {educations_added} educations to session (NOT committing yet)")
            await self.db.flush()
            logger.info(f"[sync_parsed_resume_data] ✓ Successfully flushed all changes for user_id: {user_id}")
            
        except Exception as e:
            logger.error(f"[sync_parsed_resume_data] Error syncing: {str(e)}", exc_info=True)
            raise
    
    
    # ============ EXPLICIT PERSISTENCE METHODS ============
    
    async def _persist_skills(self, user_id: UUID, skills, resume_id: Optional[UUID] = None, auto_commit: bool = True) -> int:
        """
        Persist skills extracted from resume. Handles both flat list and categorized dict formats.
        Returns count of skills added.
        """
        logger.info(f"[_persist_skills] Persisting skills for user_id={user_id}, resume_id={resume_id}")
        
        # Flatten skills if they're categorized (dict format from Gemini/Fallback)
        skills_to_persist = []
        if isinstance(skills, dict):
            # Categorized format: {backend: [...], frontend: [...], ...}
            logger.info(f"[_persist_skills] Processing categorized skills dictionary with {len(skills)} categories")
            for category, category_skills in skills.items():
                if isinstance(category_skills, list) and len(category_skills) > 0:
                    skills_to_persist.extend(category_skills)
                    logger.info(f"[_persist_skills]   Category '{category}': {len(category_skills)} skills - {category_skills}")
        elif isinstance(skills, list):
            # Flat list format
            logger.info(f"[_persist_skills] Processing flat skills list")
            skills_to_persist = skills
        
        logger.info(f"[_persist_skills] Total skills to persist: {len(skills_to_persist)}")
        
        if not skills_to_persist:
            logger.warning(f"[_persist_skills] No skills to persist!")
            return 0
        
        count = 0
        failed_skills = []
        try:
            for i, skill_name in enumerate(skills_to_persist, 1):
                try:
                    # Ensure skill_name is a string and not empty
                    if not isinstance(skill_name, str) or not skill_name.strip():
                        logger.warning(f"[_persist_skills] Skipping invalid skill name: {repr(skill_name)}")
                        continue
                    
                    skill_name = skill_name.strip()
                    logger.debug(f"[_persist_skills] Persisting skill {i}/{len(skills_to_persist)}: '{skill_name}'")
                    
                    await self.add_skill_to_candidate(
                        user_id,
                        skill_name,
                        proficiency="INTERMEDIATE",
                        resume_id=resume_id,
                        is_derived=True,
                        auto_commit=False
                    )
                    count += 1
                    logger.info(f"[_persist_skills]   ✓ Skill {i}: {skill_name}")
                except Exception as e:
                    logger.error(f"[_persist_skills]   ❌ Skill {i}: Failed to persist '{skill_name}': {str(e)}", exc_info=True)
                    failed_skills.append((skill_name, str(e)))
            
            logger.info(f"[_persist_skills] Processed {len(skills_to_persist)} skills: {count} succeeded, {len(failed_skills)} failed")
            if failed_skills:
                logger.warning(f"[_persist_skills] Failed skills: {failed_skills}")
            
            if auto_commit:
                await self.db.commit()
                logger.info(f"[_persist_skills] ✅ Committed {count} skills to database")
            else:
                await self.db.flush()
                logger.info(f"[_persist_skills] ✅ Flushed {count} skills to session")
            
            return count
        except Exception as e:
            logger.error(f"[_persist_skills] CRITICAL ERROR persisting skills: {str(e)}", exc_info=True)
            if auto_commit:
                await self.db.rollback()
                logger.error(f"[_persist_skills] Transaction rolled back")
            raise
    
    
    async def _persist_experiences(self, user_id: UUID, experiences: list, resume_id: Optional[UUID] = None, auto_commit: bool = True) -> int:
        """Persist experiences extracted from resume. Returns count of experiences added."""
        logger.info(f"[_persist_experiences] Persisting {len(experiences)} experiences for user_id={user_id}")
        
        count = 0
        try:
            for exp_data in experiences:
                try:
                    exp = ExperienceCreate(
                        job_title=exp_data.get("title", "Unknown"),
                        company_name=exp_data.get("company", "Unknown"),
                        location=None,
                        description=None,
                        start_date=None,
                        end_date=None,
                        is_current=False
                    )
                    await self.add_experience(
                        user_id,
                        exp,
                        resume_id=resume_id,
                        is_derived=True,
                        auto_commit=False
                    )
                    count += 1
                    logger.info(f"[_persist_experiences] ✓ Persisted experience: {exp.job_title} at {exp.company_name}")
                except Exception as e:
                    logger.error(f"[_persist_experiences] Failed to persist experience: {str(e)}")
            
            if auto_commit:
                await self.db.commit()
                logger.info(f"[_persist_experiences] ✓ Committed {count} experiences")
            else:
                await self.db.flush()
                logger.info(f"[_persist_experiences] ✓ Flushed {count} experiences")
            
            return count
        except Exception as e:
            logger.error(f"[_persist_experiences] Error persisting experiences: {str(e)}", exc_info=True)
            if auto_commit:
                await self.db.rollback()
            raise
    
    
    async def _persist_educations(self, user_id: UUID, educations: list, resume_id: Optional[UUID] = None, auto_commit: bool = True) -> int:
        """Persist educations extracted from resume. Returns count of educations added."""
        logger.info(f"[_persist_educations] Persisting {len(educations)} educations for user_id={user_id}")
        
        count = 0
        try:
            for edu_data in educations:
                try:
                    edu = EducationCreate(
                        institution=edu_data.get("institution", "Unknown"),
                        degree=edu_data.get("degree", "Unknown"),
                        field_of_study=edu_data.get("field", None),
                        start_date=None,
                        end_date=None,
                        description=None
                    )
                    await self.add_education(
                        user_id,
                        edu,
                        resume_id=resume_id,
                        is_derived=True,
                        auto_commit=False
                    )
                    count += 1
                    logger.info(f"[_persist_educations] ✓ Persisted education: {edu.degree} in {edu.field_of_study}")
                except Exception as e:
                    logger.error(f"[_persist_educations] Failed to persist education: {str(e)}")
            
            if auto_commit:
                await self.db.commit()
                logger.info(f"[_persist_educations] ✓ Committed {count} educations")
            else:
                await self.db.flush()
                logger.info(f"[_persist_educations] ✓ Flushed {count} educations")
            
            return count
        except Exception as e:
            logger.error(f"[_persist_educations] Error persisting educations: {str(e)}", exc_info=True)
            if auto_commit:
                await self.db.rollback()
            raise
