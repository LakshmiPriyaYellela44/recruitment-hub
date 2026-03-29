from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BaseAppException
from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse
)
from app.modules.auth.service import AuthService
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    try:
        service = AuthService(db)
        user = await service.register(request)
        return {
            "message": "User registered successfully",
            "user": UserResponse.from_orm(user)
        }
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access token."""
    try:
        service = AuthService(db)
        user, token = await service.login(request)
        
        return TokenResponse(
            access_token=token,
            user=UserResponse.from_orm(user)
        )
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
    current_user = Depends(get_current_user)
):
    """Get current user profile."""
    return UserResponse.from_orm(current_user)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    service = AuthService(db)
    user = await service.change_password(str(current_user.id), request.old_password, request.new_password)
    
    return {
        "message": "Password changed successfully",
        "user": UserResponse.from_orm(user)
    }


@router.post("/reset-password", response_model=dict)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset user password using a valid reset token."""
    try:
        service = AuthService(db)
        user = await service.reset_password(request.reset_token, request.new_password)
        
        return {
            "message": "Password reset successfully",
            "user": UserResponse.from_orm(user)
        }
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Forgot Password - Reset password with just email and new password.
    No current password verification needed (for users who forgot their password).
    
    Returns success regardless of whether email exists (for security).
    If email exists in system, password is reset. Otherwise, operation completes silently.
    """
    try:
        from app.core.security import get_password_hash
        from app.modules.auth.repository import AuthRepository
        
        repo = AuthRepository(db)
        
        # Find user by email (if exists)
        user = await repo.get_user_by_email(request.email.lower())
        
        if user:
            # User found - reset their password
            user.password_hash = get_password_hash(request.new_password)
            user.updated_at = datetime.utcnow()
            updated_user = await repo.update_user(user)
            
            return {
                "message": "✅ Password reset successfully",
                "user": UserResponse.from_orm(updated_user)
            }
        else:
            # Email not found - still return success (security best practice)
            # Don't reveal whether email exists in system
            return {
                "message": "✅ If that email address is in our system, the password has been updated",
                "user": None
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RESET_ERROR", "message": str(e)}}
        )



@router.post("/simple-reset-password")
async def simple_reset_password(
    email: str,
    current_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Simple password reset - user provides email and current password to set new one.
    No tokens or emails required. Simple UI flow for password changes.
    """
    try:
        from app.core.security import get_password_hash, verify_password
        from app.modules.auth.repository import AuthRepository
        
        repo = AuthRepository(db)
        
        # Verify user exists and password is correct
        user = await repo.get_user_by_email(email.lower())
        if not user or not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}}
            )
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        updated_user = await repo.update_user(user)
        
        return {
            "message": "✅ Password changed successfully",
            "user": UserResponse.from_orm(updated_user)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RESET_ERROR", "message": str(e)}}
        )


# ============ DEBUG ENDPOINTS (Development Only) ============

@router.post("/debug/reset-password-by-email")
async def debug_reset_password_by_email(
    email: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    DEBUG ENDPOINT - Reset password by email (development only).
    
    WARNING: This endpoint is only available in DEBUG mode!
    Do not use in production.
    
    Usage:
        POST /api/auth/debug/reset-password-by-email
        ?email=candidate1@gmail.com&new_password=TestPassword123
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in DEBUG mode"
        )
    
    try:
        from app.core.security import get_password_hash
        from app.modules.auth.repository import AuthRepository
        
        repo = AuthRepository(db)
        
        # Find user
        user = await repo.get_user_by_email(email.lower())
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "USER_NOT_FOUND", "message": f"User {email} not found"}}
            )
        
        # Reset password
        user.password_hash = get_password_hash(new_password)
        updated_user = await repo.update_user(user)
        
        return {
            "message": "✅ Password reset successfully (DEBUG MODE)",
            "user": {
                "email": updated_user.email,
                "role": updated_user.role.value,
                "is_active": updated_user.is_active,
                "new_password": new_password
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RESET_ERROR", "message": str(e)}}
        )


