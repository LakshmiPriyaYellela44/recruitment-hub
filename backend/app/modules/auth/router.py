from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
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


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request a password reset. Generates a reset token."""
    try:
        service = AuthService(db)
        reset_token, expires_in_hours = await service.forgot_password(request.email)
        
        return {
            "message": "If that email address is in our system, we will send a password reset email",
            "reset_token": reset_token,  # In production, this would be sent via email instead
            "expires_in_hours": expires_in_hours
        }
    except BaseAppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )


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

