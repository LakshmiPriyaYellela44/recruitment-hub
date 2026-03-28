from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.utils.auth_utils import require_admin
from app.modules.recruiter.service import RecruiterService
from app.core.exceptions import BaseAppException
from uuid import UUID

router = APIRouter(prefix="/admin/recruiters", tags=["admin-recruiters"])


@router.get("/")
async def admin_list_recruiters(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: List all recruiters with their details and subscription status."""
    try:
        service = RecruiterService(db)
        result = await service.admin_get_all_recruiters(limit, offset)
        return result
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )


@router.get("/{recruiter_id}")
async def admin_get_recruiter_details(
    recruiter_id: str,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get detailed information about a specific recruiter."""
    try:
        service = RecruiterService(db)
        result = await service.admin_get_recruiter_details(UUID(recruiter_id))
        return result
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


@router.post("/{recruiter_id}/deactivate")
async def admin_deactivate_recruiter(
    recruiter_id: str,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Deactivate a recruiter account."""
    try:
        service = RecruiterService(db)
        result = await service.admin_deactivate_recruiter(UUID(recruiter_id))
        return result
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


@router.post("/{recruiter_id}/activate")
async def admin_activate_recruiter(
    recruiter_id: str,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Activate a recruiter account."""
    try:
        service = RecruiterService(db)
        result = await service.admin_activate_recruiter(UUID(recruiter_id))
        return result
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


@router.patch("/{recruiter_id}/subscription")
async def admin_update_recruiter_subscription(
    recruiter_id: str,
    subscription_type: str,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Update recruiter subscription to PRO or BASIC."""
    # Validate subscription type
    if subscription_type not in ["PRO", "BASIC"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription type must be 'PRO' or 'BASIC'"
        )
    
    try:
        service = RecruiterService(db)
        result = await service.admin_set_recruiter_subscription(
            current_user.id,
            UUID(recruiter_id),
            subscription_type
        )
        return result
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
