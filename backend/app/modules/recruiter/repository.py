from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func
from sqlalchemy.orm import selectinload
from app.core.models import User, UserRole, Skill, CandidateSkill, Experience, Education, EmailSent, Resume
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class RecruiterRepository:
    """Repository for recruiter operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_candidates(
        self,
        skill_ids: Optional[List[UUID]] = None,
        experience_filter: Optional[str] = None,
        education_filter: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search candidates with filters - only shows candidates with PARSED resumes."""
        # First, get candidates that have at least one PARSED resume
        parsed_candidates_query = select(User.id).join(Resume).filter(
            User.role == UserRole.CANDIDATE,
            Resume.status == "PARSED"
        ).distinct()
        
        parsed_result = await self.db.execute(parsed_candidates_query)
        parsed_candidate_ids = parsed_result.scalars().all()
        
        if not parsed_candidate_ids:
            return [], 0
        
        query = select(User).filter(
            User.id.in_(parsed_candidate_ids),
            User.role == UserRole.CANDIDATE
        ).options(
            selectinload(User.skills)
        )
        
        # Filter by skills
        if skill_ids:
            query = query.join(CandidateSkill).filter(
                CandidateSkill.skill_id.in_(skill_ids)
            ).distinct()
        
        # Filter by experience (job title, company, description)
        if experience_filter:
            exp_search = f"%{experience_filter}%"
            exp_query = select(Experience.user_id).filter(
                Experience.user_id.in_(parsed_candidate_ids),
                or_(
                    Experience.job_title.ilike(exp_search),
                    Experience.company_name.ilike(exp_search),
                    Experience.description.ilike(exp_search)
                )
            ).distinct()
            
            exp_result = await self.db.execute(exp_query)
            exp_user_ids = exp_result.scalars().all()
            if exp_user_ids:
                query = query.filter(User.id.in_(exp_user_ids))
            else:
                return [], 0  # No candidates match experience filter
        
        # Filter by education (degree, institution, field of study)
        if education_filter:
            edu_search = f"%{education_filter}%"
            edu_query = select(Education.user_id).filter(
                Education.user_id.in_(parsed_candidate_ids),
                or_(
                    Education.degree.ilike(edu_search),
                    Education.institution.ilike(edu_search),
                    Education.field_of_study.ilike(edu_search)
                )
            ).distinct()
            
            edu_result = await self.db.execute(edu_query)
            edu_user_ids = edu_result.scalars().all()
            if edu_user_ids:
                query = query.filter(User.id.in_(edu_user_ids))
            else:
                return [], 0  # No candidates match education filter
        
        # Filter by keyword (name, email)
        if keyword:
            keyword_filter = f"%{keyword}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(keyword_filter),
                    User.last_name.ilike(keyword_filter),
                    User.email.ilike(keyword_filter)
                )
            )
        
        # Get total count before pagination
        count_query = select(func.count(User.id)).select_from(User).filter(
            User.id.in_(parsed_candidate_ids),
            User.role == UserRole.CANDIDATE
        )
        
        # Apply same filters to count
        if skill_ids:
            count_query = count_query.join(CandidateSkill).filter(
                CandidateSkill.skill_id.in_(skill_ids)
            ).distinct()
        
        if experience_filter:
            exp_search = f"%{experience_filter}%"
            exp_query = select(Experience.user_id).filter(
                Experience.user_id.in_(parsed_candidate_ids),
                or_(
                    Experience.job_title.ilike(exp_search),
                    Experience.company_name.ilike(exp_search),
                    Experience.description.ilike(exp_search)
                )
            ).distinct()
            exp_result = await self.db.execute(exp_query)
            exp_user_ids = exp_result.scalars().all()
            if exp_user_ids:
                count_query = count_query.filter(User.id.in_(exp_user_ids))
            else:
                return [], 0
        
        if education_filter:
            edu_search = f"%{education_filter}%"
            edu_query = select(Education.user_id).filter(
                Education.user_id.in_(parsed_candidate_ids),
                or_(
                    Education.degree.ilike(edu_search),
                    Education.institution.ilike(edu_search),
                    Education.field_of_study.ilike(edu_search)
                )
            ).distinct()
            edu_result = await self.db.execute(edu_query)
            edu_user_ids = edu_result.scalars().all()
            if edu_user_ids:
                count_query = count_query.filter(User.id.in_(edu_user_ids))
            else:
                return [], 0
        
        if keyword:
            keyword_filter = f"%{keyword}%"
            count_query = count_query.filter(
                or_(
                    User.first_name.ilike(keyword_filter),
                    User.last_name.ilike(keyword_filter),
                    User.email.ilike(keyword_filter)
                )
            )
        
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        # Manually convert to dict
        candidates = []
        for user in users:
            try:
                # Safely serialize skills data
                skills_list = []
                if user.skills:
                    for s in user.skills:
                        skills_list.append({
                            "id": str(s.id) if hasattr(s, 'id') else "",
                            "name": s.name if hasattr(s, 'name') else ""
                        })
                
                candidate_dict = {
                    "id": str(user.id),
                    "email": user.email or "",
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "skills": skills_list
                }
                candidates.append(candidate_dict)
            except Exception as e:
                logger.error(f"Error serializing candidate {user.id}: {e}")
                # Add basic candidate info even if there's an error
                candidates.append({
                    "id": str(user.id),
                    "email": user.email or "",
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "skills": []
                })
        
        return candidates, total_count
    
    async def get_candidate_by_id(self, candidate_id: UUID) -> Optional[User]:
        """Get candidate profile."""
        result = await self.db.execute(
            select(User).filter(
                User.id == candidate_id,
                User.role == UserRole.CANDIDATE
            ).options(
                selectinload(User.resumes),
                selectinload(User.skills),
                selectinload(User.experiences),
                selectinload(User.educations)
            )
        )
        return result.scalars().first()
    
    async def log_email_sent(
        self,
        from_user_id: UUID,
        to_email: str,
        to_candidate_id: Optional[UUID],
        subject: str,
        body: str,
        status: str = "SENT"
    ) -> EmailSent:
        """Log sent email."""
        email_record = EmailSent(
            from_user_id=from_user_id,
            to_email=to_email,
            to_candidate_id=to_candidate_id,
            subject=subject,
            body=body,
            status=status
        )
        self.db.add(email_record)
        await self.db.commit()
        await self.db.refresh(email_record)
        return email_record
    
    # ============ ADMIN METHODS ============
    
    async def get_all_recruiters(self, limit: int = 20, offset: int = 0) -> Tuple[List[User], int]:
        """Get all recruiters with pagination."""
        # Get total count
        count_query = select(func.count()).select_from(User).filter(User.role == UserRole.RECRUITER)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        result = await self.db.execute(
            select(User)
            .filter(User.role == UserRole.RECRUITER)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        recruiters = result.scalars().all()
        return recruiters, total
    
    async def get_recruiter_by_id(self, recruiter_id: UUID) -> Optional[User]:
        """Get recruiter by ID."""
        result = await self.db.execute(
            select(User).filter(
                User.id == recruiter_id,
                User.role == UserRole.RECRUITER
            )
        )
        return result.scalars().first()
    
    async def deactivate_recruiter(self, recruiter_id: UUID) -> User:
        """Deactivate a recruiter."""
        recruiter = await self.get_recruiter_by_id(recruiter_id)
        if not recruiter:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Recruiter", str(recruiter_id))
        
        recruiter.is_active = False
        await self.db.commit()
        await self.db.refresh(recruiter)
        return recruiter
    
    async def activate_recruiter(self, recruiter_id: UUID) -> User:
        """Activate a recruiter."""
        recruiter = await self.get_recruiter_by_id(recruiter_id)
        if not recruiter:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Recruiter", str(recruiter_id))
        
        recruiter.is_active = True
        await self.db.commit()
        await self.db.refresh(recruiter)
        return recruiter
