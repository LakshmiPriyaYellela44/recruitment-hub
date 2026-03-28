from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.models import User, SubscriptionType, UserRole
from app.core.exceptions import NotFoundException
from uuid import UUID


class SubscriptionRepository:
    """Repository for subscription operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def upgrade_subscription(self, user_id: UUID, subscription_type: str) -> User:
        """Upgrade user subscription."""
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.subscription_type = SubscriptionType[subscription_type]
            await self.db.commit()
            await self.db.refresh(user)
        return user
    
    async def get_recruiter_by_id(self, recruiter_id: UUID) -> User:
        """Get recruiter by ID."""
        result = await self.db.execute(
            select(User).filter(
                User.id == recruiter_id,
                User.role == UserRole.RECRUITER
            )
        )
        user = result.scalars().first()
        if not user:
            raise NotFoundException("Recruiter", str(recruiter_id))
        return user
    
    async def set_recruiter_subscription(self, recruiter_id: UUID, subscription_type: str, admin_id: UUID) -> User:
        """Set recruiter subscription (admin only)."""
        recruiter = await self.get_recruiter_by_id(recruiter_id)
        recruiter.subscription_type = SubscriptionType[subscription_type]
        recruiter.updated_by = str(admin_id)
        await self.db.commit()
        await self.db.refresh(recruiter)
        return recruiter
    
    async def get_all_recruiters(self, limit: int = 100, offset: int = 0) -> tuple[list[User], int]:
        """Get all recruiters with pagination."""
        # Get total count
        count_result = await self.db.execute(
            select(User).filter(User.role == UserRole.RECRUITER)
        )
        total = len(count_result.scalars().all())
        
        # Get paginated results
        result = await self.db.execute(
            select(User)
            .filter(User.role == UserRole.RECRUITER)
            .limit(limit)
            .offset(offset)
        )
        recruiters = result.scalars().all()
        return recruiters, total
