from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = Field(..., description="ADMIN, CANDIDATE, or RECRUITER")


class RegisterRequest(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    subscription_type: Optional[str] = None  # Only for RECRUITERS
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, user):
        """Convert ORM model to schema, hiding subscription for CANDIDATES"""
        obj = cls.model_validate(user)
        # Hide subscription_type for candidates
        if hasattr(user, 'role') and user.role.value == "CANDIDATE":
            obj.subscription_type = None
        return obj
    
    def dict(self, **kwargs):
        """Override dict to ensure candidates never expose subscription"""
        data = super().dict(**kwargs)
        # Explicitly None out subscription for candidates
        if self.role == "CANDIDATE":
            data['subscription_type'] = None
        return data


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6, description="New password (minimum 6 characters)")


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str  # For testing/development; remove in production if using email
    expires_in_hours: int
