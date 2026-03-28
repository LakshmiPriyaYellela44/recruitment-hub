from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import SubscriptionType
from app.core.exceptions import ValidationException
from app.modules.subscription.repository import SubscriptionRepository
from app.utils.audit import log_audit
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SubscriptionRepository(db)
    
    async def upgrade_subscription(self, user_id: UUID, subscription_type: str) -> dict:
        """Upgrade subscription."""
        # Validate subscription type
        try:
            sub_type = SubscriptionType[subscription_type]
        except KeyError:
            raise ValidationException(f"Invalid subscription type: {subscription_type}")
        
        # Upgrade
        user = await self.repository.upgrade_subscription(user_id, subscription_type)
        
        # Log audit
        await log_audit(
            self.db,
            user_id,
            "SUBSCRIPTION_UPGRADED",
            "Subscription",
            str(user_id),
            {"new_type": subscription_type}
        )
        
        return {
            "user_id": str(user_id),
            "subscription_type": user.subscription_type.value,
            "message": f"Subscription upgraded to {subscription_type}"
        }
    
    async def admin_set_recruiter_subscription(self, admin_id: UUID, recruiter_id: UUID, subscription_type: str) -> dict:
        """Admin sets recruiter subscription."""
        # Validate subscription type
        try:
            sub_type = SubscriptionType[subscription_type]
        except KeyError:
            raise ValidationException(f"Invalid subscription type: {subscription_type}")
        
        logger.info(f"Admin {admin_id} setting subscription {subscription_type} for recruiter {recruiter_id}")
        
        # Set subscription
        recruiter = await self.repository.set_recruiter_subscription(recruiter_id, subscription_type, admin_id)
        
        # Log audit
        await log_audit(
            self.db,
            admin_id,
            "RECRUITER_SUBSCRIPTION_SET",
            "Recruiter",
            str(recruiter_id),
            {"subscription_type": subscription_type, "by_admin": str(admin_id)}
        )
        
        return {
            "recruiter_id": str(recruiter_id),
            "subscription_type": recruiter.subscription_type.value,
            "message": f"Recruiter subscription set to {subscription_type}"
        }
    
    async def admin_get_all_recruiters(self, limit: int = 100, offset: int = 0) -> dict:
        """Admin gets all recruiters with pagination."""
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
