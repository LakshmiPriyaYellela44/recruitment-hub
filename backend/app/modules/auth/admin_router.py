from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.utils.auth_utils import require_admin
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserResponse
from app.core.exceptions import BaseAppException
from uuid import UUID
from pydantic import BaseModel

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


class ChangeRoleRequest(BaseModel):
    new_role: str  # ADMIN, RECRUITER, CANDIDATE


@router.get("/")
async def admin_list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: List all users."""
    try:
        service = AuthService(db)
        result = await service.get_all_users(limit, offset)
        
        users_response = [UserResponse.from_orm(user) for user in result["users"]]
        
        return {
            "users": users_response,
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"]
        }
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )


@router.patch("/{user_id}/role")
async def admin_change_user_role(
    user_id: str,
    request: ChangeRoleRequest,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin: Change a user's role."""
    try:
        # Validate UUID format
        UUID(user_id)
        
        service = AuthService(db)
        updated_user = await service.change_user_role(
            user_id,
            request.new_role,
            current_user.id
        )
        
        return {
            "message": f"User role changed to {request.new_role}",
            "user": UserResponse.from_orm(updated_user)
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.to_dict()
        )
