from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.core.models import User, Resume, Skill, CandidateSkill, Experience, Education
from typing import List, Optional
from uuid import UUID


class CandidateRepository:
    """Repository for candidate operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_candidate_by_id(self, user_id: UUID) -> Optional[User]:
        """Get candidate by ID with eagerly loaded relationships."""
        result = await self.db.execute(
            select(User)
            .filter(User.id == user_id)
            .options(
                selectinload(User.resumes),
                selectinload(User.experiences),
                selectinload(User.educations),
                selectinload(User.candidate_skills)
            )
        )
        return result.scalars().first()
    
    async def get_candidate_skills(self, user_id: UUID) -> List[Skill]:
        """Get all skills for a candidate."""
        result = await self.db.execute(
            select(Skill).join(CandidateSkill).filter(
                CandidateSkill.candidate_id == user_id
            )
        )
        return result.scalars().all()
    
    async def add_candidate_skill(self, user_id: UUID, skill_id: UUID, proficiency: Optional[str] = None, resume_id: Optional[UUID] = None, is_derived: bool = False, auto_commit: bool = True) -> CandidateSkill:
        """Add skill to candidate."""
        candidate_skill = CandidateSkill(
            candidate_id=user_id,
            skill_id=skill_id,
            proficiency=proficiency,
            resume_id=resume_id,
            is_derived_from_resume=is_derived
        )
        self.db.add(candidate_skill)
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(candidate_skill)
        return candidate_skill
    
    async def remove_candidate_skill(self, user_id: UUID, skill_id: UUID):
        """Remove skill from candidate."""
        await self.db.execute(
            delete(CandidateSkill).where(
                CandidateSkill.candidate_id == user_id,
                CandidateSkill.skill_id == skill_id
            )
        )
        await self.db.commit()
    
    async def get_experience(self, experience_id: UUID) -> Optional[Experience]:
        """Get experience by ID."""
        result = await self.db.execute(select(Experience).filter(Experience.id == experience_id))
        return result.scalars().first()
    
    async def create_experience(self, user_id: UUID, data: dict, resume_id: Optional[UUID] = None, is_derived: bool = False, auto_commit: bool = True) -> Experience:
        """Create experience."""
        experience = Experience(user_id=user_id, resume_id=resume_id, is_derived_from_resume=is_derived, **data)
        self.db.add(experience)
        await self.db.flush()  # ALWAYS flush to register in session
        
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(experience)
        return experience
    

    
    async def get_education(self, education_id: UUID) -> Optional[Education]:
        """Get education by ID."""
        result = await self.db.execute(select(Education).filter(Education.id == education_id))
        return result.scalars().first()
    
    async def create_education(self, user_id: UUID, data: dict, resume_id: Optional[UUID] = None, is_derived: bool = False, auto_commit: bool = True) -> Education:
        """Create education."""
        education = Education(user_id=user_id, resume_id=resume_id, is_derived_from_resume=is_derived, **data)
        self.db.add(education)
        await self.db.flush()  # ALWAYS flush to register in session
        
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(education)
        return education
    

