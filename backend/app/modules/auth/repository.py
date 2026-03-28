from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.models import User, PasswordReset
from typing import Optional
from datetime import datetime


class AuthRepository:
    """Repository for auth operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        result = await self.db.execute(
            select(User).filter(func.lower(User.email) == email.lower())
        )
        return result.scalars().first()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()
    
    async def create_user(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user(self, user: User) -> User:
        """Update user."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_all_users(self, limit: int = 20, offset: int = 0) -> dict:
        """Get all users with pagination."""
        # Get total count
        count_result = await self.db.execute(select(func.count(User.id)))
        total = count_result.scalar() or 0
        
        # Get paginated users
        result = await self.db.execute(
            select(User).limit(limit).offset(offset).order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        return {
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def create_password_reset(self, password_reset: PasswordReset) -> PasswordReset:
        """Create a password reset record."""
        self.db.add(password_reset)
        await self.db.commit()
        await self.db.refresh(password_reset)
        return password_reset
    
    async def get_password_reset_by_token(self, reset_token: str) -> Optional[PasswordReset]:
        """Get password reset by token (must not be used and not expired)."""
        result = await self.db.execute(
            select(PasswordReset).filter(
                PasswordReset.reset_token == reset_token,
                PasswordReset.is_used == False,
                PasswordReset.expires_at > datetime.utcnow()
            )
        )
        return result.scalars().first()
    
    async def mark_password_reset_as_used(self, password_reset: PasswordReset) -> PasswordReset:
        """Mark a password reset as used."""
        password_reset.is_used = True
        self.db.add(password_reset)
        await self.db.commit()
        await self.db.refresh(password_reset)
        return password_reset
