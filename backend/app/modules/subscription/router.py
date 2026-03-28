from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.utils.auth_utils import get_current_user, require_admin
from app.modules.subscription.schemas import (
    UpgradeSubscriptionRequest, 
    SubscriptionResponse,
    SetRecruiterSubscriptionRequest,
    RecruiterSubscriptionResponse,
    AdminListRecruitersResponse
)
from app.modules.subscription.service import SubscriptionService
from app.core.exceptions import BaseAppException
from uuid import UUID

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    request: UpgradeSubscriptionRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upgrade user subscription to PRO."""
    try:
        service = SubscriptionService(db)
        result = await service.upgrade_subscription(current_user.id, request.subscription_type)
        return SubscriptionResponse(**result)
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )


# ============ ADMIN ENDPOINTS ============

@router.get("/admin/recruiters", response_model=AdminListRecruitersResponse)
async def admin_list_recruiters(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: List all recruiters."""
    try:
        service = SubscriptionService(db)
        result = await service.admin_get_all_recruiters(limit, offset)
        return AdminListRecruitersResponse(**result)
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )


@router.post("/admin/recruiters/{recruiter_id}/subscription", response_model=RecruiterSubscriptionResponse)
async def admin_set_recruiter_subscription(
    recruiter_id: str,
    request: SetRecruiterSubscriptionRequest,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Set recruiter subscription (BASIC or PRO)."""
    try:
        service = SubscriptionService(db)
        result = await service.admin_set_recruiter_subscription(
            current_user.id,
            UUID(recruiter_id),
            request.subscription_type
        )
        return RecruiterSubscriptionResponse(**result)
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recruiter ID format"
        )
