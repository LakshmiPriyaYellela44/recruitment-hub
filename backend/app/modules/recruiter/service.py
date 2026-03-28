from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.models import UserRole, SubscriptionType, Skill, Resume, User
from app.core.exceptions import AuthorizationException, NotFoundException
from app.modules.recruiter.repository import RecruiterRepository
from app.modules.recruiter.schemas import CandidateSearchFilters, SendEmailRequest
from app.aws_services.ses_client import SESClient
from app.utils.audit import log_audit
from uuid import UUID
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class RecruiterService:
    """Service for recruiter operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = RecruiterRepository(db)
        self.ses_client = SESClient()
    
    async def search_candidates(
        self,
        recruiter_id: UUID,
        filters: CandidateSearchFilters,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List, int]:
        """Search candidates - filtered by skills, experience, education from parsed data."""
        logger.info(f"[search_candidates] recruiter_id={recruiter_id}, filters={filters.dict()}")
        
        # Get skill IDs from names
        skill_ids = None
        if filters.skills:
            result = await self.db.execute(
                select(Skill).filter(
                    Skill.name.in_([s.lower() for s in filters.skills])
                )
            )
            skill_records = result.scalars().all()
            skill_ids = [s.id for s in skill_records]
            logger.info(f"[search_candidates] Found {len(skill_ids)} skills matching filter")
        
        # Search with new filters
        candidates, total = await self.repository.search_candidates(
            skill_ids=skill_ids,
            experience_filter=filters.experience,
            education_filter=filters.education,
            keyword=filters.keyword,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"[search_candidates] Found {len(candidates)} candidates (total: {total})")
        
        # Log audit
        await log_audit(
            self.db,
            recruiter_id,
            "CANDIDATE_SEARCH",
            "Candidate",
            "batch",
            {
                "count": len(candidates),
                "total": total,
                "filters": filters.dict()
            }
        )
        
        return candidates, total
    
    async def get_candidate_profile(self, recruiter_id: UUID, candidate_id: UUID):
        """Get candidate profile with parsed resume data (including email extracted from resume)."""
        candidate = await self.repository.get_candidate_by_id(candidate_id)
        
        if not candidate:
            raise NotFoundException("Candidate", str(candidate_id))
        
        # Build response with candidate info and parsed resume data
        response = {
            "id": str(candidate.id),
            "email": candidate.email,  # This contains the email extracted from parsed resume
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "phone_number": getattr(candidate, 'phone_number', None) or "",
            "role": candidate.role.value if hasattr(candidate, 'role') else "CANDIDATE",
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "member_since": candidate.created_at.strftime("%m/%d/%Y") if candidate.created_at else None,
            "resumes": [],
            "experiences": [],
            "educations": [],
            "skills": [],
            "parsed_data": {}
        }
        
        # Get active resume with parsed data
        from sqlalchemy import select, desc
        from app.core.models import Resume
        
        resume_result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == candidate_id, Resume.is_active == True)
            .order_by(desc(Resume.created_at))
            .limit(1)
        )
        active_resume = resume_result.scalars().first()
        
        if active_resume and active_resume.parsed_data:
            parsed = active_resume.parsed_data
            response["parsed_data"] = parsed
            
            # Extract structured data from parsed resume
            if parsed.get('skills'):
                response["skills"] = parsed.get('skills', [])[:20]  # Top 20 skills
            
            if parsed.get('experiences'):
                response["experiences"] = parsed.get('experiences', [])[:5]  # Last 5 jobs
            
            if parsed.get('educations'):
                response["educations"] = parsed.get('educations', [])
        
        return response
    
    async def send_email_to_candidate(
        self,
        recruiter_id: UUID,
        recruiter_subscription: SubscriptionType,
        request: SendEmailRequest
    ) -> dict:
        """Send email to candidate (PRO only)."""
        # Check subscription
        if recruiter_subscription != SubscriptionType.PRO:
            raise AuthorizationException(
                "Sending emails requires PRO subscription"
            )
        
        # Get candidate
        candidate = await self.repository.get_candidate_by_id(request.candidate_id)
        if not candidate:
            raise NotFoundException("Candidate", str(request.candidate_id))
        
        # Send email
        email_id = await self.ses_client.send_email(
            to_addresses=[candidate.email],
            subject=request.subject,
            body=request.body
        )
        
        # Log email
        email_record = await self.repository.log_email_sent(
            from_user_id=recruiter_id,
            to_email=candidate.email,
            to_candidate_id=request.candidate_id,
            subject=request.subject,
            body=request.body
        )
        
        # Log audit
        await log_audit(
            self.db,
            recruiter_id,
            "EMAIL_SENT",
            "Email",
            str(email_record.id),
            {
                "to_candidate": str(request.candidate_id),
                "to_email": candidate.email,
                "subject": request.subject
            }
        )
        
        return {
            "message": "Email sent successfully",
            "email_id": email_id,
            "recipient": candidate.email
        }
    
    # ============ ADMIN METHODS ============
    
    async def admin_get_all_recruiters(self, limit: int = 20, offset: int = 0) -> dict:
        """Admin: Get all recruiters with pagination."""
        logger.info(f"[admin_get_all_recruiters] Fetching recruiters with limit={limit}, offset={offset}")
        recruiters, total = await self.repository.get_all_recruiters(limit, offset)
        
        return {
            "recruiters": [
                {
                    "id": str(r.id),
                    "email": r.email,
                    "first_name": r.first_name,
                    "last_name": r.last_name,
                    "subscription_type": r.subscription_type.value,
                    "is_active": r.is_active,
                    "created_at": r.created_at
                }
                for r in recruiters
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def admin_get_recruiter_details(self, recruiter_id: UUID) -> dict:
        """Admin: Get detailed information about a specific recruiter."""
        logger.info(f"[admin_get_recruiter_details] Getting details for recruiter_id={recruiter_id}")
        recruiter = await self.repository.get_recruiter_by_id(recruiter_id)
        
        if not recruiter:
            raise NotFoundException("Recruiter", str(recruiter_id))
        
        return {
            "id": str(recruiter.id),
            "email": recruiter.email,
            "first_name": recruiter.first_name,
            "last_name": recruiter.last_name,
            "subscription_type": recruiter.subscription_type.value,
            "is_active": recruiter.is_active,
            "created_at": recruiter.created_at,
            "updated_at": recruiter.updated_at,
            "created_by": recruiter.created_by,
            "updated_by": recruiter.updated_by
        }
    
    async def admin_deactivate_recruiter(self, recruiter_id: UUID) -> dict:
        """Admin: Deactivate a recruiter account."""
        logger.info(f"[admin_deactivate_recruiter] Deactivating recruiter_id={recruiter_id}")
        recruiter = await self.repository.deactivate_recruiter(recruiter_id)
        
        # Log audit
        await log_audit(
            self.db,
            recruiter_id,
            "RECRUITER_DEACTIVATED_BY_ADMIN",
            "Recruiter",
            str(recruiter_id),
            {}
        )
        
        return {
            "message": "Recruiter deactivated successfully",
            "recruiter_id": str(recruiter_id),
            "is_active": recruiter.is_active
        }
    
    async def admin_activate_recruiter(self, recruiter_id: UUID) -> dict:
        """Admin: Activate a recruiter account."""
        logger.info(f"[admin_activate_recruiter] Activating recruiter_id={recruiter_id}")
        recruiter = await self.repository.activate_recruiter(recruiter_id)
        
        # Log audit
        await log_audit(
            self.db,
            recruiter_id,
            "RECRUITER_ACTIVATED_BY_ADMIN",
            "Recruiter",
            str(recruiter_id),
            {}
        )
        
        return {
            "message": "Recruiter activated successfully",
            "recruiter_id": str(recruiter_id),
            "is_active": recruiter.is_active
        }
    
    async def admin_set_recruiter_subscription(self, admin_id: UUID, recruiter_id: UUID, subscription_type: str) -> dict:
        """Admin: Update recruiter subscription (PRO or BASIC)."""
        logger.info(f"[admin_set_recruiter_subscription] Admin {admin_id} setting subscription {subscription_type} for recruiter {recruiter_id}")
        
        # Validate subscription type
        if subscription_type not in ["PRO", "BASIC"]:
            from app.core.exceptions import ValidationException
            raise ValidationException(f"Invalid subscription type: {subscription_type}")
        
        # Get recruiter for old subscription
        recruiter = await self.repository.get_recruiter_by_id(recruiter_id)
        if not recruiter:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Recruiter", str(recruiter_id))
        
        old_subscription = recruiter.subscription_type.value
        
        # Update subscription
        recruiter.subscription_type = SubscriptionType[subscription_type]
        recruiter.updated_by = str(admin_id)
        self.db.add(recruiter)
        await self.db.commit()
        await self.db.refresh(recruiter)
        
        # Log audit
        await log_audit(
            self.db,
            admin_id,
            "RECRUITER_SUBSCRIPTION_UPDATED",
            "Recruiter",
            str(recruiter_id),
            {
                "old_subscription": old_subscription,
                "new_subscription": subscription_type,
                "admin_id": str(admin_id)
            }
        )
        
        logger.info(f"[admin_set_recruiter_subscription] Subscription updated to {subscription_type} for recruiter {recruiter_id}")
        
        return {
            "message": f"Recruiter subscription updated to {subscription_type}",
            "recruiter_id": str(recruiter_id),
            "subscription_type": recruiter.subscription_type.value,
            "email": recruiter.email
        }
