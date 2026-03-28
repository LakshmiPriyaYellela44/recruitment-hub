from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import User, UserRole, AuditLog, PasswordReset
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    ConflictException
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import RegisterRequest, LoginRequest
from datetime import datetime, timedelta
from typing import Optional
import json
import logging
import secrets

logger = logging.getLogger(__name__)

# Password reset token expiry in hours
RESET_TOKEN_EXPIRY_HOURS = 24


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AuthRepository(db)
    
    async def register(self, request: RegisterRequest) -> User:
        """Register a new user. Auto-creates candidate profile if role is CANDIDATE."""
        # Normalize email to lowercase
        email = request.email.lower().strip()
        
        # Check if email already exists
        existing_user = await self.repository.get_user_by_email(email)
        if existing_user:
            raise ConflictException(f"Email {email} already registered")
        
        # Validate role
        try:
            role = UserRole[request.role]
        except KeyError:
            raise ValidationException(f"Invalid role: {request.role}")
        
        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            role=role
        )
        
        created_user = await self.repository.create_user(user)
        
        # Log audit
        await self._log_audit(None, "USER_CREATED", "User", str(created_user.id), created_user)
        
        return created_user
    
    async def login(self, request: LoginRequest) -> tuple[User, str]:
        """Authenticate user and return token."""
        # Normalize email to lowercase
        email = request.email.lower().strip()
        
        user = await self.repository.get_user_by_email(email)
        
        if not user or not verify_password(request.password, user.password_hash):
            raise AuthenticationException("Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationException("User account is disabled")
        
        # Create token
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
        token = create_access_token(token_data)
        
        # Log audit
        await self._log_audit(user.id, "USER_LOGIN", "User", str(user.id), user)
        
        return user, token
    
    async def get_current_user(self, user_id: str) -> Optional[User]:
        """Get current user by ID."""
        user = await self.repository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationException("User not found or inactive")
        return user
    
    async def get_all_users(self, limit: int = 20, offset: int = 0) -> dict:
        """Get all users with pagination (admin only)."""
        return await self.repository.get_all_users(limit, offset)
    
    async def change_user_role(self, user_id: str, new_role: str, admin_user_id) -> User:
        """Change a user's role (admin only operation)."""
        from uuid import UUID
        
        # Validate new role
        if new_role.upper() not in [role.value for role in UserRole]:
            raise ValidationException(f"Invalid role: {new_role}")
        
        # Convert user_id to UUID if needed
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        # Get the user
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise ValidationException("User not found")
        
        # Track old role for audit
        old_role = user.role.value
        new_role_enum = UserRole[new_role.upper()]
        
        # Update role
        user.role = new_role_enum
        user.updated_by = str(admin_user_id)
        user.updated_at = datetime.utcnow()
        updated_user = await self.repository.update_user(user)
        
        # Log audit
        await self._log_audit(
            admin_user_id,
            "USER_ROLE_CHANGED",
            "User",
            str(user_id),
            {"old_role": old_role, "new_role": new_role}
        )
        
        return updated_user
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> User:
        """Change user password."""
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            raise AuthenticationException("User not found")
        
        if not verify_password(old_password, user.password_hash):
            raise ValidationException("Old password is incorrect")
        
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        updated_user = await self.repository.update_user(user)
        await self._log_audit(user.id, "PASSWORD_CHANGED", "User", str(user.id), user)
        
        return updated_user
    
    async def forgot_password(self, email: str) -> tuple[str, int]:
        """Generate a password reset token for the user's email."""
        # Normalize email
        email = email.lower().strip()
        
        # Check if user exists
        user = await self.repository.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists (security best practice)
            raise AuthenticationException("If that email address is in our system, we will send a password reset email")
        
        # Generate secure token
        reset_token = secrets.token_urlsafe(32)
        
        # Create password reset record with expiry
        expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
        password_reset = PasswordReset(
            user_id=user.id,
            reset_token=reset_token,
            expires_at=expires_at
        )
        
        await self.repository.create_password_reset(password_reset)
        
        # Log audit
        await self._log_audit(user.id, "PASSWORD_RESET_REQUESTED", "User", str(user.id), {"email": email})
        
        return reset_token, RESET_TOKEN_EXPIRY_HOURS
    
    async def reset_password(self, reset_token: str, new_password: str) -> User:
        """Reset user password using a valid reset token."""
        # Get password reset record
        password_reset = await self.repository.get_password_reset_by_token(reset_token)
        if not password_reset:
            raise ValidationException("Invalid or expired password reset token")
        
        # Get user
        user = await self.repository.get_user_by_id(str(password_reset.user_id))
        if not user:
            raise AuthenticationException("User not found")
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        updated_user = await self.repository.update_user(user)
        
        # Mark reset as used
        await self.repository.mark_password_reset_as_used(password_reset)
        
        # Log audit
        await self._log_audit(user.id, "PASSWORD_RESET", "User", str(user.id), {"email": user.email})
        
        return updated_user
    
    async def _log_audit(self, user_id, action: str, entity_type: str, entity_id: str, changes=None):
        """Log audit event."""
        try:
            # Build changes dict
            changes_dict = {"event": action, "timestamp": datetime.utcnow().isoformat()}
            if isinstance(changes, dict):
                changes_dict.update(changes)
            
            audit = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                changes=json.dumps(changes_dict)
            )
            self.db.add(audit)
            await self.db.commit()
        except Exception:
            pass  # Don't fail on audit logging errors
