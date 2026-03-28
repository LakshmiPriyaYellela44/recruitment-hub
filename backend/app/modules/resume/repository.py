"""Updated Resume Repository with cascade delete methods"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.core.models import Resume, CandidateSkill, Experience, Education
from app.core.exceptions import NotFoundException
from uuid import UUID
from typing import Optional, List


class ResumeRepository:
    """Repository for resume operations with cascade delete support."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_resume_by_id(self, resume_id: UUID) -> Optional[Resume]:
        """Get resume by ID."""
        result = await self.db.execute(select(Resume).filter(Resume.id == resume_id))
        return result.scalars().first()
    
    async def get_candidate_resumes(self, user_id: UUID) -> List[Resume]:
        """Get all resumes for a candidate."""
        result = await self.db.execute(select(Resume).filter(Resume.user_id == user_id))
        return result.scalars().all()
    
    async def create_resume(self, resume: Resume) -> Resume:
        """Create resume record."""
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        return resume
    
    async def update_resume(self, resume: Resume, auto_commit: bool = True) -> Resume:
        """Update resume."""
        await self.db.merge(resume)
        
        if auto_commit:
            await self.db.commit()
        else:
            await self.db.flush()  # Flush to register changes in session without committing
        
        return resume
    
    async def delete_resume(self, resume_id: UUID):
        """Delete resume record. Called within transaction - do NOT commit."""
        await self.db.execute(delete(Resume).where(Resume.id == resume_id))
    
    # ============ CASCADE DELETE METHODS ============
    # NOTE: These methods are called within a transaction context in the service.
    # DO NOT call commit() here - let the service transaction handle it.
    
    async def delete_resume_skills(self, resume_id: UUID) -> int:
        """Delete all candidate skills derived from this resume."""
        result = await self.db.execute(
            delete(CandidateSkill).where(
                (CandidateSkill.resume_id == resume_id) &
                (CandidateSkill.is_derived_from_resume == True)
            )
        )
        return result.rowcount
    
    async def delete_resume_experiences(self, resume_id: UUID) -> int:
        """Delete all experiences derived from this resume."""
        result = await self.db.execute(
            delete(Experience).where(
                (Experience.resume_id == resume_id) &
                (Experience.is_derived_from_resume == True)
            )
        )
        return result.rowcount
    
    async def delete_resume_educations(self, resume_id: UUID) -> int:
        """Delete all educations derived from this resume."""
        result = await self.db.execute(
            delete(Education).where(
                (Education.resume_id == resume_id) &
                (Education.is_derived_from_resume == True)
            )
        )
        return result.rowcount
